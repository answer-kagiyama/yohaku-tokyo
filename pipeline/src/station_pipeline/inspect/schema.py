"""Lightweight schema inspection: guess key columns and measure how filled they really are.

Column names differ per municipality. Presence of a `緯度` column does not mean it is populated,
so coordinates are judged by the fill rate of valid values in sample rows.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

LAT_NAMES = ("緯度", "lat", "latitude", "y座標", "緯度(世界測地系)")
LNG_NAMES = ("経度", "lng", "lon", "long", "longitude", "x座標", "経度(世界測地系)")
# Observed: 館名 (都公立図書館オールガイド), ページタイトル / タイトル (港区の公共施設情報)
NAME_NAMES = (
    "名称",
    "施設名",
    "施設名称",
    "公園名",
    "館名",
    "名前",
    "ページタイトル",
    "タイトル",
    "name",
)
CATEGORY_NAMES = ("文化財分類", "種類", "種別", "分類", "カテゴリ", "大分類", "小分類", "category")
ADDRESS_NAMES = ("所在地_連結表記", "所在地", "住所", "所在地_全体", "address")

# Tokyo incl. islands (Ogasawara ~ 24-27N, 136-154E); generous but rejects swapped/zero values.
TOKYO_LAT = (20.0, 36.5)
TOKYO_LNG = (136.0, 154.0)


@dataclass(frozen=True)
class Inspection:
    fields: list[str]
    latField: str | None
    lngField: str | None
    nameField: str | None
    addressField: str | None
    sampleSize: int
    coordFillRate: float | None
    addressFillRate: float | None
    total: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(name: str) -> str:
    return name.strip().lower().replace(" ", "").replace("　", "")


def find_field(fields: Sequence[str], candidates: Iterable[str]) -> str | None:
    """Exact (normalized) match, then prefix (`緯度(世界測地系)`), then a `_`-qualified suffix
    (`観光ポイント_緯度`)."""
    normalized = {_norm(f): f for f in fields}
    cands = [_norm(c) for c in candidates]
    for c in cands:
        if c in normalized:
            return normalized[c]
    for c in cands:
        for n, original in normalized.items():
            if n.startswith(c):
                return original
    for c in cands:
        for n, original in normalized.items():
            if n.endswith("_" + c):
                return original
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def coord_fill_rate(records: Sequence[Mapping[str, Any]], lat: str, lng: str) -> float:
    if not records:
        return 0.0
    ok = 0
    for r in records:
        la, ln = _to_float(r.get(lat)), _to_float(r.get(lng))
        if (
            la is not None
            and ln is not None
            and TOKYO_LAT[0] <= la <= TOKYO_LAT[1]
            and TOKYO_LNG[0] <= ln <= TOKYO_LNG[1]
        ):
            ok += 1
    return round(ok / len(records), 3)


def text_fill_rate(records: Sequence[Mapping[str, Any]], field: str) -> float:
    if not records:
        return 0.0
    filled = sum(1 for r in records if str(r.get(field) or "").strip())
    return round(filled / len(records), 3)


def inspect_datastore(result: Mapping[str, Any]) -> Inspection:
    fields = [f["id"] for f in result.get("fields", []) if not f["id"].startswith("_")]
    return inspect_rows(fields, result.get("records", []), result.get("total"))


def inspect_rows(
    fields: Sequence[str], records: Sequence[Mapping[str, Any]], total: int | None
) -> Inspection:
    fields = list(fields)
    lat = find_field(fields, LAT_NAMES)
    lng = find_field(fields, LNG_NAMES)
    address = find_field(fields, ADDRESS_NAMES)
    return Inspection(
        fields=fields,
        latField=lat,
        lngField=lng,
        nameField=find_field(fields, NAME_NAMES),
        addressField=address,
        sampleSize=len(records),
        coordFillRate=coord_fill_rate(records, lat, lng) if lat and lng else None,
        addressFillRate=text_fill_rate(records, address) if address else None,
        total=total,
    )
