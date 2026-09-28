"""Feature definitions: the human-authored concepts to look for (no URLs)."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FeatureDefinition:
    key: str
    label: str
    keywords: tuple[str, ...]
    list_hints: tuple[str, ...] = ()
    exclude_keywords: tuple[str, ...] = ()
    exclude_facility_names: tuple[str, ...] = ()
    exclude_name_markers: tuple[str, ...] = ()
    exclude_categories: tuple[str, ...] = ()
    same_place_m: float | None = None
    include_name_keywords: tuple[str, ...] = ()
    enabled: bool = True


def load_definitions(path: Path) -> dict[str, FeatureDefinition]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw = doc["feature_definitions"]
    global_excludes = tuple(doc.get("global_exclude_keywords", []))
    defs = {}
    for key, body in raw.items():
        if not body.get("keywords"):
            raise ValueError(f"feature {key!r} has no keywords")
        defs[key] = FeatureDefinition(
            key=key,
            label=body.get("label", key),
            keywords=tuple(body["keywords"]),
            list_hints=tuple(body.get("list_hints", [])),
            exclude_keywords=tuple(body.get("exclude_keywords", [])) + global_excludes,
            exclude_facility_names=tuple(body.get("exclude_facility_names", [])),
            exclude_name_markers=tuple(body.get("exclude_name_markers", [])),
            exclude_categories=tuple(body.get("exclude_categories", [])),
            same_place_m=body.get("same_place_m"),
            include_name_keywords=tuple(body.get("include_name_keywords", [])),
            enabled=bool(body.get("enabled", True)),
        )
    return defs
