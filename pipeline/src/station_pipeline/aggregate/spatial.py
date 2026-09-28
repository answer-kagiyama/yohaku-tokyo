"""Station-radius spatial join in a metric CRS (ADR 0008)."""

from collections.abc import Sequence
from typing import Any

import geopandas as gpd
from shapely.geometry import Point

WGS84 = "EPSG:4326"
METRIC_CRS = "EPSG:6677"  # JGD2011 / Japan Plane Rectangular CS IX (Tokyo mainland), metres


def facilities_within(
    stations: Sequence[dict[str, Any]], facilities: Sequence[dict[str, Any]], radius_m: float
) -> dict[str, list[dict[str, Any]]]:
    """station id -> located facilities within radius (inclusive), with distanceM, nearest first."""
    result: dict[str, list[dict[str, Any]]] = {s["id"]: [] for s in stations}
    located = [f for f in facilities if f.get("lat") is not None and f.get("lng") is not None]
    if not stations or not located:
        return result

    st = gpd.GeoDataFrame(
        {"station_id": [s["id"] for s in stations]},
        geometry=[Point(s["lng"], s["lat"]) for s in stations],
        crs=WGS84,
    ).to_crs(METRIC_CRS)
    fa = gpd.GeoDataFrame(
        {"idx": range(len(located))},
        geometry=[Point(f["lng"], f["lat"]) for f in located],
        crs=WGS84,
    ).to_crs(METRIC_CRS)

    joined = gpd.sjoin(fa, st, predicate="dwithin", distance=radius_m)
    station_geom = st.set_index("station_id").geometry
    for _, row in joined.iterrows():
        distance = row.geometry.distance(station_geom[row.station_id])
        f = located[row.idx]
        result[row.station_id].append({**f, "distanceM": round(float(distance), 1)})
    for items in result.values():
        items.sort(key=lambda f: (f["distanceM"], f["id"]))
    return result
