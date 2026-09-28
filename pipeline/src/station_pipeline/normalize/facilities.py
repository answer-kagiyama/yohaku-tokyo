"""Rows from heterogeneous municipal CSVs -> a common Facility record."""

from collections.abc import Mapping, Sequence
from typing import Any

from ..inspect.schema import (
    ADDRESS_NAMES,
    CATEGORY_NAMES,
    LAT_NAMES,
    LNG_NAMES,
    NAME_NAMES,
    TOKYO_LAT,
    TOKYO_LNG,
    find_field,
)


class NormalizeError(ValueError):
    pass


def _coord(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def valid_coords(lat: float | None, lng: float | None) -> bool:
    return (
        lat is not None
        and lng is not None
        and TOKYO_LAT[0] <= lat <= TOKYO_LAT[1]
        and TOKYO_LNG[0] <= lng <= TOKYO_LNG[1]
    )


def normalize_rows(
    fields: Sequence[str], records: Sequence[Mapping[str, str]], entry: Mapping[str, Any]
) -> list[dict[str, Any]]:
    name_f = find_field(fields, NAME_NAMES)
    if name_f is None:
        raise NormalizeError(f"name column not found in {list(fields)}")
    lat_f, lng_f = find_field(fields, LAT_NAMES), find_field(fields, LNG_NAMES)
    addr_f = find_field(fields, ADDRESS_NAMES)
    # Every column that looks like a category (a list can have 大分類 and 小分類).
    category_fs = [f for f in fields if find_field([f], CATEGORY_NAMES)]

    out = []
    for i, row in enumerate(records, start=1):
        name = (row.get(name_f) or "").strip()
        if not name:
            continue  # a row without a name is not a facility
        lat = _coord(row.get(lat_f)) if lat_f else None
        lng = _coord(row.get(lng_f)) if lng_f else None
        has_coords = valid_coords(lat, lng)
        address = (row.get(addr_f) or "").strip() if addr_f else ""
        out.append(
            {
                "id": f"{entry['datasetId']}:{i}",
                "feature": entry["feature"],
                "name": name,
                "address": address or None,
                "lat": lat if has_coords else None,
                "lng": lng if has_coords else None,
                "coordSource": "source" if has_coords else None,
                "geocode": None,
                "categories": [row[c] for c in category_fs if row.get(c)],
                "datasetId": entry["datasetId"],
                "organization": entry.get("organization"),
                "sourceUrl": entry["sourceUrl"],
                "resourceUrl": entry["resourceUrl"],
            }
        )
    return out
