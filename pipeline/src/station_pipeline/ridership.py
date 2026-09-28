"""stationUsage from the Tokyo Statistical Yearbook station tables (spec 0005 §4).

JR publishes boardings only, subways/private railways publish boardings and alightings, so the
comparable measure is boardings: all operators and lines at a station name, per day.
"""

import re
from collections.abc import Sequence
from datetime import date
from typing import Any

from .discover.catalog import CkanCatalog
from .inspect.tabular import parse_csv

YEARBOOK_QUERY = "東京都統計年鑑 運輸"
YEARBOOK_ORG = "東京都総務局"
TABLE_MARKERS = ("駅別乗車人員", "駅別乗降車人員")
ERA_START = {"令和": 2018, "平成": 1988}


class RidershipError(RuntimeError):
    pass


def title_year(title: str) -> int | None:
    """ "東京都統計年鑑　令和6年　4　運輸・観光" -> 2024 (元年 = 1)."""
    m = re.search(r"(令和|平成)(元|\d+)年", title)
    if not m:
        return None
    n = 1 if m.group(2) == "元" else int(m.group(2))
    return ERA_START[m.group(1)] + n


def find_yearbook(catalog: CkanCatalog) -> dict[str, Any]:
    candidates = []
    for p in catalog.search(YEARBOOK_QUERY):
        org = (p.get("organization") or {}).get("title")
        year = title_year(p.get("title") or "")
        if org == YEARBOOK_ORG and "運輸" in (p.get("title") or "") and year:
            candidates.append((year, p["metadata_modified"], p))
    if not candidates:
        raise RidershipError("no statistical yearbook (transport) found in the catalog")
    return max(candidates, key=lambda c: (c[0], c[1]))[2]


def station_tables(package: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        r
        for r in package.get("resources", [])
        if any(m in (r.get("name") or "") for m in TABLE_MARKERS)
        and (r.get("format") or "").upper() == "CSV"
    ]


def _column(fields: Sequence[str], predicate) -> str | None:
    return next((f for f in fields if predicate(f)), None)


def parse_station_table(body: bytes, table_name: str) -> tuple[int, list[dict[str, Any]]]:
    """-> (latest fiscal year, rows of that year with a station name)."""
    fields, records, _ = parse_csv(body)
    fy = _column(fields, lambda f: "Fiscal year" in f)
    station = _column(fields, lambda f: f == "駅")
    station_en = _column(fields, lambda f: f == "Station")
    boarding = _column(fields, lambda f: f.startswith("乗車人員") and "総数" in f)
    line = _column(fields, lambda f: f == "系統")
    company = _column(fields, lambda f: f == "会社名")
    if not (fy and station and boarding):
        raise RidershipError(f"unexpected columns in {table_name}: {fields}")
    years = [int(r[fy]) for r in records if r.get(fy, "").isdigit()]
    if not years:
        raise RidershipError(f"no fiscal year rows in {table_name}")
    latest = max(years)
    rows = []
    for r in records:
        if r.get(fy) != str(latest) or not r.get(station):
            continue
        value = (r.get(boarding) or "").replace(",", "")
        if not value.isdigit():
            continue  # e.g. "-" for a station not yet open
        rows.append(
            {
                "station": r[station],
                "stationEn": (r.get(station_en) or None) if station_en else None,
                "operator": (r.get(company) if company else None) or "JR東日本",
                "line": r.get(line) or "",
                "annualThousands": int(value),
                "table": table_name,
            }
        )
    return latest, rows


def days_in_fiscal_year(year: int) -> int:
    return (date(year + 1, 4, 1) - date(year, 4, 1)).days


def aggregate_ridership(
    stations: Sequence[dict[str, Any]],
    tables: Sequence[tuple[int, list[dict[str, Any]]]],
    dataset_id: str,
    generated_at: str,
) -> dict[str, Any]:
    fiscal_year = max(y for y, _ in tables)
    rows = [r for y, table in tables if y == fiscal_year for r in table]
    days = days_in_fiscal_year(fiscal_year)
    out = []
    for s in stations:
        lines = [r for r in rows if r["station"] == s["name"]]
        annual = sum(r["annualThousands"] for r in lines)
        count = round(annual * 1000 / days) if lines else None
        out.append(
            {
                "stationId": s["id"],
                "status": "complete" if lines else "incomplete",
                "count": count,
                "lowerBound": count or 0,
                "lines": [
                    {k: r[k] for k in ("operator", "line", "annualThousands")} for r in lines
                ],
                "datasets": [dataset_id] if lines else [],
            }
        )
    return {
        "feature": "stationUsage",
        "kind": "ridership",
        "measure": "1日平均乗車人員（全社・全線の合算）",
        "fiscalYear": fiscal_year,
        "daysInFiscalYear": days,
        "generatedAt": generated_at,
        "stations": out,
    }


def manifest_entry(catalog: CkanCatalog, package: dict[str, Any], tables: list[dict[str, Any]]):
    return {
        "datasetId": package["name"],
        "name": package["title"],
        "organization": (package.get("organization") or {}).get("title"),
        "feature": "stationUsage",
        "sourceUrl": catalog.dataset_page(package["name"]),
        "resourceUrl": tables[0]["url"],
        "resourceId": tables[0].get("id"),
        "format": "csv",
        "datastoreActive": False,
        "locationSource": None,
        "status": "accepted",
        "autoStatus": "accepted",
        "confidence": 1.0,
        "reason": "東京都統計年鑑（運輸）の最新年パッケージ。駅別表: "
        + "・".join(t["name"] for t in tables),
        "signals": {"semantic": 1.0, "format": 0.8, "location": None, "license": 1.0},
        "inspection": None,
        "license": package.get("license_id"),
        "lastModified": package.get("metadata_modified"),
        "updateFrequency": None,
        "duplicateOf": None,
        "review": None,
    }


def english_names(tables: Sequence[tuple[int, list[dict[str, Any]]]]) -> dict[str, str]:
    """Station name -> English, from the JR table (first spelling wins)."""
    names: dict[str, str] = {}
    for _, rows in tables:
        for r in rows:
            if r.get("stationEn") and r["operator"] == "JR東日本":
                names.setdefault(r["station"], r["stationEn"])
    return names


def load_tables(catalog: CkanCatalog) -> tuple[dict[str, Any], list, list]:
    package = find_yearbook(catalog)
    tables = station_tables(package)
    parsed = [parse_station_table(catalog.client.get_bytes(t["url"]), t["name"]) for t in tables]
    return package, tables, parsed
