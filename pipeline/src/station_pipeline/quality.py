"""Data quality gate. Any violation raises and fails the pipeline."""

from typing import Any

REQUIRED_TOP = ("generatedAt", "radiusMeters", "scoring", "stations")
REQUIRED_STATION = (
    "id",
    "name",
    "lat",
    "lng",
    "raw",
    "normalized",
    "semantic",
    "scores",
    "sources",
)


class DataQualityError(ValueError):
    pass


def _in_range(v: Any) -> bool:
    return v is None or (isinstance(v, int | float) and 0 <= v <= 100)


def validate_dataset(data: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        raise DataQualityError(f"schema mismatch: missing top-level keys {missing}")

    seen: set[str] = set()
    for s in data["stations"]:
        missing = [k for k in REQUIRED_STATION if k not in s]
        if missing:
            raise DataQualityError(f"schema mismatch: station {s.get('id')} missing {missing}")
        sid = s["id"]
        if sid in seen:
            raise DataQualityError(f"duplicate station id: {sid}")
        seen.add(sid)
        if not s["name"]:
            raise DataQualityError(f"station name missing: {sid}")
        lat, lng = s["lat"], s["lng"]
        if not (
            isinstance(lat, int | float)
            and isinstance(lng, int | float)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            raise DataQualityError(f"invalid coordinates: {sid} ({lat}, {lng})")
        for key, value in s["scores"].items():
            if key != "coverage" and not _in_range(value):
                raise DataQualityError(f"score out of range: {sid}.{key}={value}")
        for key, value in s["normalized"].items():
            if not _in_range(value):
                raise DataQualityError(f"normalized out of range: {sid}.{key}={value}")
        if not s["sources"]:
            raise DataQualityError(f"no sources: {sid}")
        for src in s["sources"]:
            if src.get("kind") != "fixture" and not src.get("url"):
                raise DataQualityError(f"source without url: {sid}/{src.get('id')}")
