"""Merge the same facility listed in several datasets (e.g. a ward list and a park-type list)."""

import math
import re
import unicodedata
from typing import Any

EARTH_RADIUS_M = 6_371_008.8
# Source coordinates beat geocoded ones; exact geocodes beat partial ones.
PRIORITY = {("source", None): 0, ("geocode", "exact"): 1, ("geocode", "partial"): 2}


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def name_key(name: str) -> str:
    n = unicodedata.normalize("NFKC", name)
    n = re.sub(r"[（(].*?[）)]", "", n)  # drop parenthesized readings / notes
    return re.sub(r"\s+", "", n)


def _priority(f: dict[str, Any]) -> tuple[int, str]:
    precision = (f.get("geocode") or {}).get("precision")
    key = (f["coordSource"], precision if f["coordSource"] == "geocode" else None)
    return PRIORITY.get(key, 9), f["id"]


def dedupe_facilities(
    facilities: list[dict[str, Any]], max_distance_m: float, same_place_m: float | None = None
) -> list[dict[str, Any]]:
    """Same name within max_distance_m -> one facility. With same_place_m, anything within that
    distance is one place regardless of name (e.g. several listed items kept at one temple).
    Unlocated facilities are kept as-is (cannot be compared by distance)."""
    kept: list[dict[str, Any]] = []
    by_name: dict[str, list[dict[str, Any]]] = {}
    located = sorted((f for f in facilities if f["coordSource"]), key=_priority)
    for f in located:
        f = {**f, "duplicates": []}
        group = by_name.setdefault(name_key(f["name"]), [])
        twin = next(
            (
                g
                for g in group
                if haversine_m(g["lat"], g["lng"], f["lat"], f["lng"]) <= max_distance_m
            ),
            None,
        )
        if twin is None and same_place_m is not None:
            twin = next(
                (
                    g
                    for g in kept
                    if haversine_m(g["lat"], g["lng"], f["lat"], f["lng"]) <= same_place_m
                ),
                None,
            )
        if twin is not None:
            twin["duplicates"].append(f["id"])
            continue
        group.append(f)
        kept.append(f)
    unlocated = [{**f, "duplicates": []} for f in facilities if not f["coordSource"]]
    return sorted(kept, key=lambda f: f["id"]) + unlocated
