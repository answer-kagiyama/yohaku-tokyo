"""Manifest assembly: duplicates, human overrides, merge with other features, write."""

import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

STATUSES = ("accepted", "review", "rejected")


def _title_key(entry: Mapping[str, Any]) -> tuple[str, str]:
    title = re.sub(r"[\s　]+", "", entry["name"])
    return (entry.get("organization") or "", title)


def mark_duplicates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the highest-confidence entry per resource URL / (org, title). Others -> duplicateOf."""
    ordered = sorted(entries, key=lambda e: (-e["confidence"], e["datasetId"]))
    seen: dict[Any, str] = {}
    for e in ordered:
        keys = [("title", _title_key(e))]
        if e.get("resourceUrl"):
            keys.append(("url", e["resourceUrl"]))
        original = next((seen[k] for k in keys if k in seen), None)
        if original is not None and e["status"] != "rejected":
            e["duplicateOf"] = original
            if e["status"] == "accepted":
                e["status"] = e["autoStatus"] = "review"
                e["reason"] += f"。{original} と重複の可能性"
        for k in keys:
            seen.setdefault(k, e["datasetId"])
    return ordered


def load_overrides(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    overrides = data.get("datasets", {})
    for dataset_id, o in overrides.items():
        if o.get("status") not in STATUSES:
            raise ValueError(f"override for {dataset_id}: invalid status {o.get('status')!r}")
    return overrides


def apply_overrides(
    entries: Iterable[dict[str, Any]], overrides: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    out = []
    for e in entries:
        e = dict(e)
        # "<feature>/<datasetId>" applies to one feature; "<datasetId>" to every feature.
        o = overrides.get(f"{e['feature']}/{e['datasetId']}") or overrides.get(e["datasetId"])
        if o:
            e["status"] = o["status"]
            e["review"] = {"status": o["status"], "note": o.get("note", "")}
        else:
            e["review"] = None
        out.append(e)
    return out


def feature_stats(entries: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(e["status"] for e in entries)
    return {"candidates": sum(counts.values()), **{s: counts.get(s, 0) for s in STATUSES}}


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    ids = set()
    for e in manifest["datasets"]:
        key = (e["feature"], e["datasetId"])
        if key in ids:
            raise ValueError(f"duplicate manifest entry: {key}")
        ids.add(key)
        for field in ("reason", "sourceUrl", "status", "autoStatus", "signals"):
            if not e.get(field):
                raise ValueError(f"{e['datasetId']}: missing {field}")
        if e["status"] == "accepted" and not e.get("resourceUrl"):
            raise ValueError(f"accepted dataset without source: {e['datasetId']}")


def merge_manifest(
    existing: Mapping[str, Any] | None,
    feature: str,
    feature_meta: Mapping[str, Any],
    entries: list[dict[str, Any]],
    generated_at: str,
    catalog: str,
) -> dict[str, Any]:
    """Replace this feature's entries; keep every other feature untouched."""
    others = [e for e in (existing or {}).get("datasets", []) if e["feature"] != feature]
    features = dict((existing or {}).get("features", {}))
    features[feature] = {**feature_meta, **feature_stats(entries)}
    manifest = {
        "generatedAt": generated_at,
        "catalog": catalog,
        "classifier": "rule-based",
        "features": dict(sorted(features.items())),
        "datasets": others + entries,
    }
    validate_manifest(manifest)
    return manifest


def read_manifest(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_manifest(manifest: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
