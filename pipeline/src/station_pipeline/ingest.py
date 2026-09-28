"""Step 5: fetch accepted datasets -> normalize -> geocode -> interim facilities + report."""

import json
import logging
import re
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .fetch.download import fetch_resource
from .geo.geocode import Geocoder, is_outside_tokyo
from .http import HttpClient, HttpError
from .inspect.tabular import TabularError, parse_table
from .normalize.dedupe import dedupe_facilities
from .normalize.facilities import NormalizeError, normalize_rows

log = logging.getLogger(__name__)
DEGRADED_BELOW = 0.5
# "千代田図書館分室" is a library; "神田公園出張所" (a 神田公園-district office) is not a park.
_NAME_SUFFIXES = ("", "分館", "分室", "本館")


def matches_feature(
    facility: dict[str, Any], keywords: tuple[str, ...], include_names: tuple[str, ...] = ()
) -> bool:
    """Rule-based row classification for mixed lists (RuleBasedClassifier, ADR 0003)."""
    words = keywords + include_names
    text = " ".join([facility["name"], *facility.get("categories", [])])
    return any(w in text for w in words)


def is_excluded_name(name: str, words: tuple[str, ...]) -> bool:
    base = re.sub(r"[（(].*?[）)]$", "", unicodedata.normalize("NFKC", name)).strip()
    return any(base.endswith(w + suffix) for w in words for suffix in _NAME_SUFFIXES)


def geocode_missing(
    facilities: list[dict[str, Any]], geocoder: Geocoder, scope: frozenset[str] = frozenset()
) -> None:
    """Fills coordinates from addresses. Every facility left unlocated gets a reason."""
    for f in facilities:
        if f["coordSource"] is not None:
            continue
        if not f["address"]:
            f["unlocatedReason"] = "no-address"
            continue
        if is_outside_tokyo(f["address"]):
            f["unlocatedReason"] = "outside-tokyo"  # cannot be near any Tokyo station
            continue
        if scope and f.get("organization") not in scope:
            f["unlocatedReason"] = "out-of-geocode-scope"
            continue
        try:
            result = geocoder.geocode(f["address"], f.get("organization"))
        except HttpError as exc:
            log.warning("geocode failed for %s: %s", f["id"], exc)
            f["unlocatedReason"] = "geocode-error"
            continue
        if result is None:
            f["unlocatedReason"] = "geocode-not-found"
            continue
        f.update(lat=result.lat, lng=result.lng, coordSource="geocode", geocode=result.to_dict())


def ingest_feature(
    manifest: dict[str, Any],
    feature: str,
    client: HttpClient,
    geocoder: Geocoder,
    raw_dir: Path,
    now: datetime,
    geocode_scope: frozenset[str] = frozenset(),
    dedupe_max_distance_m: float = 150.0,
    exclude_names: tuple[str, ...] = (),
    exclude_markers: tuple[str, ...] = (),
    exclude_categories: tuple[str, ...] = (),
    same_place_m: float | None = None,
    include_names: tuple[str, ...] = (),
    feature_keywords: tuple[str, ...] = (),
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries = [
        e for e in manifest["datasets"] if e["feature"] == feature and e["status"] == "accepted"
    ]
    facilities: list[dict[str, Any]] = []
    datasets = []
    for e in sorted(entries, key=lambda e: e["datasetId"]):
        report: dict[str, Any] = {
            "datasetId": e["datasetId"],
            "name": e["name"],
            "organization": e.get("organization"),
            "resourceUrl": e.get("resourceUrl"),
        }
        try:
            if (e.get("format") or "").lower() not in ("csv", "geojson", "json"):
                raise TabularError(f"unsupported format: {e.get('format')}")
            raw = fetch_resource(client, e, raw_dir, now)
            fields, records, encoding = parse_table(raw.path.read_bytes(), e.get("format"))
            rows = normalize_rows(fields, records, e)
            total_rows = len(rows)
            # Not a destination for this feature: counted by another feature (a library in a
            # public facility list), not open to the public (※非公開), or not a place (無形).
            rows = [
                f
                for f in rows
                if not is_excluded_name(f["name"], exclude_names)
                and not any(m in f["name"] for m in exclude_markers)
                and not any(w in c for c in f["categories"] for w in exclude_categories)
                and (not include_names or any(w in f["name"] for w in include_names))
                and (not e.get("rowFilter") or matches_feature(f, feature_keywords, include_names))
            ]
        except (HttpError, TabularError, NormalizeError) as exc:
            # A failed dataset is missing data, never "zero facilities".
            report.update(status="failed", error=str(exc))
            datasets.append(report)
            log.warning("ingest failed for %s: %s", e["datasetId"], exc)
            continue

        with_source = sum(1 for f in rows if f["coordSource"] == "source")
        geocode_missing(rows, geocoder, geocode_scope)
        geocoded = sum(1 for f in rows if f["coordSource"] == "geocode")
        located = with_source + geocoded
        out_of_scope = sum(1 for f in rows if f.get("unlocatedReason") == "out-of-geocode-scope")
        outside = sum(1 for f in rows if f.get("unlocatedReason") == "outside-tokyo")
        in_scope = len(rows) - out_of_scope - outside
        if rows and in_scope == 0 and located == 0:
            status = "out-of-scope"  # deliberately not geocoded yet (pipeline.yaml geocode.scope)
        elif in_scope and located / in_scope < DEGRADED_BELOW:
            status = "degraded"
        else:
            status = "ok"
        report.update(
            status=status,
            encoding=encoding,
            sha256=raw.sha256,
            retrievedAt=raw.retrievedAt,
            rows=len(rows),
            excluded=total_rows - len(rows),
            withSourceCoords=with_source,
            geocoded=geocoded,
            geocodedPartial=sum(
                1 for f in rows if f["geocode"] and f["geocode"]["precision"] == "partial"
            ),
            # Facilities outside Tokyo are not "missing" for any Tokyo station.
            unlocated=len(rows) - located - outside,
            outsideTokyo=outside,
            outOfGeocodeScope=out_of_scope,
        )
        datasets.append(report)
        facilities.extend(rows)

    before = len(facilities)
    facilities = dedupe_facilities(facilities, dedupe_max_distance_m, same_place_m)
    summary = {
        "feature": feature,
        "generatedAt": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "datasets": datasets,
        "totals": {
            "datasets": len(datasets),
            "failed": sum(1 for d in datasets if d["status"] == "failed"),
            "degraded": sum(1 for d in datasets if d["status"] == "degraded"),
            "outOfScope": sum(1 for d in datasets if d["status"] == "out-of-scope"),
            "rows": before,
            "mergedDuplicates": before - len(facilities),
            "facilities": len(facilities),
            "located": sum(1 for f in facilities if f["coordSource"]),
            "unlocated": sum(1 for f in facilities if not f["coordSource"]),
        },
    }
    summary["totals"]["unlocatedByReason"] = dict(
        sorted(
            Counter(f.get("unlocatedReason") for f in facilities if not f["coordSource"]).items()
        )
    )
    summary["geocodeScope"] = sorted(geocode_scope)
    return facilities, summary


def write_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
