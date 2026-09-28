"""Operational settings (pipeline/config/pipeline.yaml)."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Settings:
    geocode_scope: frozenset[str] | None  # None = auto (from the station master); empty = all
    geocode_extra: frozenset[str]
    dedupe_max_distance_m: float
    unlocated_tolerance: float = 0.0


def load_settings(path: Path) -> Settings:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Settings(
        geocode_scope=None
        if doc.get("geocode", {}).get("scope") == "auto"
        else frozenset(doc.get("geocode", {}).get("scope") or []),
        geocode_extra=frozenset(doc.get("geocode", {}).get("extra") or []),
        dedupe_max_distance_m=float(doc.get("dedupe", {}).get("max_distance_m", 150)),
        unlocated_tolerance=float(doc.get("coverage", {}).get("unlocated_tolerance", 0.0)),
    )
