"""Orchestrates discovery for one feature: search -> pick -> inspect -> evaluate -> dedupe."""

import logging
from datetime import datetime
from typing import Any

from ..http import HttpError
from ..inspect.schema import Inspection, inspect_datastore, inspect_rows
from ..inspect.tabular import TabularError, parse_table
from .catalog import CkanCatalog
from .definitions import FeatureDefinition
from .evaluate import evaluate, pick_resource, semantic_signal
from .manifest import mark_duplicates

log = logging.getLogger(__name__)

SAMPLE_ROWS = 50


def search_candidates(catalog: CkanCatalog, d: FeatureDefinition) -> list[dict[str, Any]]:
    packages: dict[str, dict[str, Any]] = {}
    for keyword in d.keywords:
        for p in catalog.search(keyword):
            packages.setdefault(p["id"], p)
    return sorted(packages.values(), key=lambda p: p["name"])


def inspect_resource(catalog: CkanCatalog, resource: dict[str, Any]) -> Inspection | None:
    """DataStore: sample via API. Plain CSV: download (cached) and sample. Others: not inspected."""
    if resource.get("datastore_active"):
        return inspect_datastore(catalog.datastore_sample(resource["id"]))
    if (resource.get("format") or "").strip().upper() in ("CSV", "GEOJSON", "JSON"):
        body = catalog.client.get_bytes(resource["url"])
        fields, records, _ = parse_table(body, resource.get("format"))
        return inspect_rows(fields, records[:SAMPLE_ROWS], len(records))
    return None


def discover_feature(
    catalog: CkanCatalog, d: FeatureDefinition, now: datetime
) -> list[dict[str, Any]]:
    entries = []
    for p in search_candidates(catalog, d):
        resource, format_score = pick_resource(p, d.keywords)
        semantic, _ = semantic_signal(p, d)
        inspection: Inspection | None = None
        inspect_error = None
        excluded = any(w in (p.get("title") or "") for w in d.exclude_keywords)
        # Only spend network calls on plausible candidates.
        if resource is not None and semantic >= 0.7 and not excluded:
            try:
                inspection = inspect_resource(catalog, resource)
            except (HttpError, RuntimeError, KeyError, TabularError) as exc:
                inspect_error = str(exc)
                log.warning("inspect failed for %s: %s", p["name"], exc)

        ev = evaluate(p, d, resource, format_score, inspection, now)
        org = p.get("organization") or {}
        entries.append(
            {
                "datasetId": p["name"],
                "name": p.get("title") or p["name"],
                "organization": org.get("title"),
                "feature": d.key,
                "sourceUrl": catalog.dataset_page(p["name"]),
                "resourceUrl": resource.get("url") if resource else None,
                "resourceId": resource.get("id") if resource else None,
                "format": (resource.get("format") or "").lower() if resource else None,
                "datastoreActive": bool(resource and resource.get("datastore_active")),
                "locationSource": ev.location_source,
                # The title does not name the concept (a mixed facility list or a per-category
                # file): ingest keeps only rows whose name / category matches the feature.
                "rowFilter": not any(w in (p.get("title") or "") for w in d.keywords),
                "status": ev.status,
                "autoStatus": ev.status,
                "confidence": ev.confidence,
                "reason": ev.reason + (f"。inspect 失敗: {inspect_error}" if inspect_error else ""),
                "signals": ev.signals,
                "inspection": inspection.to_dict() if inspection else None,
                "license": p.get("license_id") or p.get("license_title"),
                "lastModified": (resource or {}).get("last_modified") or p.get("metadata_modified"),
                "updateFrequency": next(
                    (x["value"] for x in p.get("extras", []) if x.get("key") == "更新頻度"), None
                ),
                "duplicateOf": None,
            }
        )
    return mark_duplicates(entries)
