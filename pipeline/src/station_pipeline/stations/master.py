"""Build the station master from human-defined names + MLIT N02 + the statistical yearbook.

Only the station names are authored by hand. Coordinates and lines come from N02, English names
(and therefore ids) from the yearbook JR table. A name that cannot be resolved fails the build:
never guess a station."""

import json
import re
import zipfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..geo.municipalities import Municipality

OPERATOR_SHORT = {
    "東日本旅客鉄道": "JR",
    "東海旅客鉄道": "JR東海",
    "東京地下鉄": "東京メトロ",
    "東京都": "都営",
    "首都圏新都市鉄道": "",
    "東京臨海高速鉄道": "",
    "東京モノレール": "",
    "ゆりかもめ": "",
}


class StationMasterError(ValueError):
    pass


def load_n02(zip_path: Path, member: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as z:
        return json.loads(z.read(member))["features"]


def slug(english: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", english.lower()).strip("-")
    if not s:
        raise StationMasterError(f"cannot make an id from {english!r}")
    return s


def line_label(operator: str, line: str) -> str:
    """'東京地下鉄', '2号線日比谷線' -> '東京メトロ日比谷線'."""
    line = re.sub(r"^\d+号線", "", line)
    return f"{OPERATOR_SHORT.get(operator, operator)}{line}"


def _midpoint(feature: Mapping[str, Any]) -> tuple[float, float]:
    coords = feature["geometry"]["coordinates"]
    lng = sum(c[0] for c in coords) / len(coords)
    lat = sum(c[1] for c in coords) / len(coords)
    return lat, lng


def resolve_station(
    name: str, operator: str, features: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    own = [
        f
        for f in features
        if f["properties"]["N02_005"] == name and f["properties"]["N02_004"] == operator
    ]
    if not own:
        raise StationMasterError(f"{name}: not found for {operator} in N02")
    points = [_midpoint(f) for f in own]
    lat = round(sum(p[0] for p in points) / len(points), 6)
    lng = round(sum(p[1] for p in points) / len(points), 6)
    groups = {f["properties"]["N02_005g"] for f in own}
    lines = []
    for f in features:
        p = f["properties"]
        if p["N02_005g"] in groups:
            label = line_label(p["N02_004"], p["N02_003"])
            if label not in lines:
                lines.append(label)
    return {"lat": lat, "lng": lng, "lines": lines, "n02Groups": sorted(groups)}


MunicipalityAt = Callable[[float, float], Municipality | None]
MunicipalitiesWithin = Callable[[float, float, float], list[Municipality]]


def build_master(
    names: Sequence[str],
    operator: str,
    features: Sequence[Mapping[str, Any]],
    english: Mapping[str, str],
    municipality_at: MunicipalityAt,
    municipalities_within: MunicipalitiesWithin,
    radius_m: float,
    source: Mapping[str, Any],
) -> dict[str, Any]:
    if len(set(names)) != len(names):
        raise StationMasterError("duplicate station names in config")
    stations = []
    for name in names:
        if name not in english:
            raise StationMasterError(f"{name}: no English name in the yearbook JR table")
        resolved = resolve_station(name, operator, features)
        here = municipality_at(resolved["lat"], resolved["lng"])
        area = municipalities_within(resolved["lat"], resolved["lng"], radius_m)
        stations.append(
            {
                "id": slug(english[name]),
                "name": name,
                "nameEn": english[name],
                "lat": resolved["lat"],
                "lng": resolved["lng"],
                "municipality": here.name if here else None,
                "lines": resolved["lines"],
                "areaMunicipalities": [m.name for m in area],
                "n02Groups": resolved["n02Groups"],
                "raw": {},
            }
        )
    ids = [s["id"] for s in stations]
    if len(set(ids)) != len(ids):
        raise StationMasterError(f"duplicate ids: {ids}")
    return {
        "description": "Station master (spec 0008). Coordinates/lines: MLIT N02; raw: aggregates.",
        "radiusMeters": radius_m,
        "sources": [
            {
                "id": "mlit-n02",
                "name": source["name"],
                "organization": source["publisher"],
                "url": source["page"],
                "license": source["license"],
                "features": [],
                "kind": "opendata",
            }
        ],
        "stations": stations,
    }


def geocode_scope(master: Mapping[str, Any], extra: Sequence[str] = ()) -> frozenset[str]:
    return frozenset(
        {m for s in master["stations"] for m in s.get("areaMunicipalities", [])} | set(extra)
    )
