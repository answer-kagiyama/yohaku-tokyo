"""Build the stations dataset: fixture raw values, overridden by real aggregates where available."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import FEATURES, SCORING_METHOD, SCORING_VERSION, WEIGHTS
from .scoring import competition_ranks, compute_scores, rank_ranges


def _opendata_source(entry: Mapping[str, Any], feature: str) -> dict[str, Any]:
    org = entry.get("organization") or ""
    return {
        "id": entry["datasetId"],
        "name": f"{org} {entry['name']}".strip(),
        "organization": org or None,
        "url": entry["sourceUrl"],
        "license": entry.get("license"),
        "features": [feature],
        "kind": "opendata",
    }


def build_from_fixture(
    path: Path,
    generated_at: str | None = None,
    aggregates: Mapping[str, Mapping[str, Any]] | None = None,
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    aggregates = aggregates or {}
    real_features = [f for f in FEATURES if f in aggregates]
    fixture_features = [f for f in FEATURES if f not in aggregates]
    by_station = {
        feature: {s["stationId"]: s for s in agg["stations"]} for feature, agg in aggregates.items()
    }
    manifest_entries = {
        (e["feature"], e["datasetId"]): e for e in (manifest or {}).get("datasets", [])
    }

    # Fixture sources only cover features that are still fixtures; other base sources (the station
    # master, MLIT N02) always stay.
    fixture_sources = []
    for src in fixture["sources"]:
        if src.get("kind") != "fixture":
            fixture_sources.append(src)
            continue
        features = [f for f in src.get("features", []) if f in fixture_features]
        if features:
            fixture_sources.append({**src, "features": features})

    raws, evidence, sources = [], [], []
    for st in fixture["stations"]:
        raw = {f: st["raw"].get(f) for f in FEATURES}
        ev: dict[str, Any] = {}
        station_sources = list(fixture_sources)
        for feature in real_features:
            agg = by_station[feature].get(st["id"])
            if agg is None:
                raw[feature] = None  # station not aggregated: missing, never 0
                continue
            raw[feature] = agg["count"]
            if aggregates[feature].get("kind") == "ridership":
                ev[feature] = {
                    "kind": "ridership",
                    "status": agg["status"],
                    "count": agg["count"],
                    "fiscalYear": aggregates[feature]["fiscalYear"],
                    "measure": aggregates[feature]["measure"],
                    "lines": agg["lines"],
                }
            else:
                ev[feature] = {
                    "kind": "facilities",
                    "status": agg["status"],
                    "radiusMeters": aggregates[feature]["radiusMeters"],
                    "count": agg["count"],
                    "lowerBound": agg["lowerBound"],
                    "municipalities": agg["municipalities"],
                    "facilities": [
                        {k: f[k] for k in ("name", "distanceM", "coordSource")}
                        for f in agg["facilities"]
                    ],
                }
            for dataset_id in agg["datasets"]:
                entry = manifest_entries.get((feature, dataset_id))
                if entry is not None:
                    station_sources.append(_opendata_source(entry, feature))
        raws.append(raw)
        evidence.append(ev)
        sources.append(station_sources)

    computed = compute_scores(raws)
    ranks = competition_ranks([c["scores"]["yohaku"] for c in computed])
    ranges = rank_ranges(raws)
    of = sum(1 for r in ranks if r is not None)
    stations = []
    for st, raw, calc, ev, srcs, rank, rng in zip(
        fixture["stations"], raws, computed, evidence, sources, ranks, ranges, strict=True
    ):
        stations.append(
            {
                "id": st["id"],
                "name": st["name"],
                "nameEn": st.get("nameEn"),
                "lat": st["lat"],
                "lng": st["lng"],
                "municipality": st.get("municipality"),
                "lines": st.get("lines", []),
                "raw": raw,
                "normalized": calc["normalized"],
                "semantic": {},
                "scores": calc["scores"],
                "effectiveWeights": calc["effectiveWeights"],
                "ranking": None if rank is None else {"rank": rank, "of": of, "range": list(rng)},
                "sources": srcs,
                "evidence": ev,
            }
        )

    return {
        "generatedAt": generated_at
        or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "radiusMeters": fixture["radiusMeters"],
        "isFixture": bool(fixture_features),
        "fixtureFeatures": fixture_features,
        "scoring": {"version": SCORING_VERSION, "method": SCORING_METHOD, "weights": WEIGHTS},
        "stations": stations,
    }
