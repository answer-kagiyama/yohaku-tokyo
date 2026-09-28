"""Step 6: facilities + stations -> per-station counts with completeness (spec 0004)."""

from collections.abc import Callable, Sequence
from typing import Any

from ..geo.municipalities import Municipality
from .coverage import municipality_coverage, station_status
from .spatial import METRIC_CRS, facilities_within

MunicipalityLookup = Callable[[float, float, float], list[Municipality]]


def aggregate_feature(
    feature: str,
    stations: Sequence[dict[str, Any]],
    facilities: Sequence[dict[str, Any]],
    report: dict[str, Any],
    municipalities_of: MunicipalityLookup,
    radius_m: float,
    generated_at: str,
    unlocated_tolerance: float = 0.0,
) -> dict[str, Any]:
    coverage = municipality_coverage(report, unlocated_tolerance)
    fetched_by_org: dict[str, set[str]] = {}
    for d in report.get("datasets", []):
        if d["status"] in ("ok", "degraded") and d.get("organization"):
            fetched_by_org.setdefault(d["organization"], set()).add(d["datasetId"])
    within = facilities_within(stations, facilities, radius_m)
    out = []
    for s in stations:
        munis = municipalities_of(s["lat"], s["lng"], radius_m)
        muni_rows = [
            {
                "code": m.code,
                "name": m.name,
                "coverage": coverage.get(m.name, {}).get("coverage", "uncovered"),
                "unlocated": coverage.get(m.name, {}).get("unlocated", 0),
            }
            for m in munis
        ]
        # No municipality found at all (all samples failed) is not evidence of anything.
        status = station_status(r["coverage"] for r in muni_rows) if muni_rows else "incomplete"
        found = within[s["id"]]
        out.append(
            {
                "stationId": s["id"],
                "status": status,
                "count": len(found) if status == "complete" else None,
                "lowerBound": len(found),
                "municipalities": muni_rows,
                "facilities": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "distanceM": f["distanceM"],
                        "coordSource": f["coordSource"],
                        "datasetId": f["datasetId"],
                        "organization": f.get("organization"),
                    }
                    for f in found
                ],
                # Datasets that found facilities here, plus the municipal datasets whose
                # completeness backs the count (they are evidence even when they found 0).
                "datasets": sorted(
                    {f["datasetId"] for f in found}
                    | {d for m in munis for d in fetched_by_org.get(m.name, set())}
                ),
            }
        )
    return {
        "feature": feature,
        "radiusMeters": radius_m,
        "crs": METRIC_CRS,
        "generatedAt": generated_at,
        "municipalitySampling": "center + 8 @ r/2 + 16 @ r (GSI reverse geocoder)",
        "unlocatedTolerance": unlocated_tolerance,
        "stations": out,
    }
