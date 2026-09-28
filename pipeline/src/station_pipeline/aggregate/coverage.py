"""Is a municipality's data complete enough that "N facilities" (or 0) is a real count?"""

from collections.abc import Iterable, Mapping
from typing import Any

# Datasets that span municipalities (e.g. 都立公園 lists) add facilities but cannot prove
# that a municipality is covered.
CROSS_MUNICIPAL_ORGS = frozenset({"東京都", "東京都建設局"})


def municipality_coverage(
    report: Mapping[str, Any], unlocated_tolerance: float = 0.0
) -> dict[str, dict[str, Any]]:
    """organization -> {coverage: covered | partial, rows, unlocated}. Missing key = uncovered.

    A municipality whose unlocated share is within `unlocated_tolerance` still counts as covered;
    the tolerated number is returned so that it can be shown next to the count."""
    by_org: dict[str, list[Mapping[str, Any]]] = {}
    for d in report.get("datasets", []):
        org = d.get("organization")
        if org and org not in CROSS_MUNICIPAL_ORGS:
            by_org.setdefault(org, []).append(d)
    coverage = {}
    for org, datasets in by_org.items():
        fetched = [d for d in datasets if d["status"] in ("ok", "degraded")]
        if not fetched:
            continue  # failed / out-of-scope only -> uncovered
        unlocated = sum(d.get("unlocated", 0) for d in fetched)
        rows = sum(d.get("rows", 0) for d in fetched)
        degraded = any(d["status"] == "degraded" for d in fetched)
        within_tolerance = rows > 0 and unlocated / rows <= unlocated_tolerance
        covered = not degraded and (unlocated == 0 or within_tolerance)
        coverage[org] = {
            "coverage": "covered" if covered else "partial",
            "rows": rows,
            "unlocated": unlocated,
        }
    return coverage


def station_status(coverages: Iterable[str]) -> str:
    return "complete" if all(c == "covered" for c in coverages) else "incomplete"
