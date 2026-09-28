"""Rule-based dataset evaluation (the default SemanticClassifier side of ADR 0003).

Deterministic: same catalog metadata + same inspection + same `now` -> same result.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..inspect.schema import Inspection
from .definitions import FeatureDefinition

# Machine-readable, tabular/geo formats. Anything else (PDF, JPEG, LAS, ZIP, HTML…) is unusable.
FORMAT_SCORES: dict[str, float] = {
    "GEOJSON": 0.9,
    "JSON": 0.9,
    "CSV": 0.8,
    "KML": 0.7,
    "XLSX": 0.6,
    "XLS": 0.6,
}
DATASTORE_SCORE = 1.0
OPEN_LICENSE_IDS = {"cc-by-4.0", "cc-by", "cc-by-2.1-jp", "cc0-1.0", "cc0", "odc-by"}
OPEN_LICENSE_WORDS = ("CC BY", "CC0", "表示", "政府標準利用規約", "公共データ利用規約")

WEIGHTS = {"semantic": 0.35, "format": 0.15, "location": 0.30, "license": 0.10, "freshness": 0.10}
ACCEPT_CONFIDENCE = 0.75
ACCEPT_MIN_SEMANTIC = 0.7
ACCEPT_MIN_COORD_FILL = 0.8
ACCEPT_MIN_ADDRESS_FILL = 0.8
ACCEPT_MIN_LOCATION = 0.8
GEOCODE_LOCATION = 0.8  # usable, but geocoded points are less precise than source coordinates
UNKNOWN_LOCATION = 0.5


@dataclass(frozen=True)
class Evaluation:
    status: str  # accepted | review | rejected
    confidence: float
    location_source: str | None
    signals: dict[str, float | None]
    reason: str


def _hits(text: str, words: tuple[str, ...]) -> list[str]:
    return [w for w in words if w in text]


def semantic_signal(package: Mapping[str, Any], d: FeatureDefinition) -> tuple[float, list[str]]:
    title = package.get("title") or ""
    title_hits = _hits(title, d.keywords)
    if title_hits:
        hints = _hits(title, d.list_hints)
        if hints:
            return 1.0, [f"タイトルに「{'」「'.join(title_hits + hints)}」を含む"]
        return 0.7, [f"タイトルに「{'」「'.join(title_hits)}」を含む（一覧を示す語なし）"]
    # Packages split per category (港区の公共施設情報: 公園・児童遊園・緑地 / 図書館・… files).
    resource_hits = sorted(
        {w for r in package.get("resources", []) for w in _hits(r.get("name") or "", d.keywords)}
    )
    if resource_hits:
        return 0.7, [f"リソース名に「{'」「'.join(resource_hits)}」を含む（カテゴリ別ファイル）"]
    other = " ".join(
        [package.get("notes") or ""] + [t.get("name", "") for t in package.get("tags", [])]
    )
    other_hits = _hits(other, d.keywords)
    if other_hits:
        return 0.4, [f"説明・タグのみに「{'」「'.join(other_hits)}」を含む"]
    return 0.0, ["キーワードに一致しない"]


def pick_resource(
    package: Mapping[str, Any], keywords: tuple[str, ...] = ()
) -> tuple[dict[str, Any] | None, float | None]:
    """Best machine-readable resource: one whose name matches the feature (per-category files)
    > DataStore > format score > most recently modified."""
    best: tuple[tuple[int, float, str], dict[str, Any], float] | None = None
    for r in package.get("resources", []):
        fmt = (r.get("format") or "").strip().upper()
        score = DATASTORE_SCORE if r.get("datastore_active") else FORMAT_SCORES.get(fmt)
        if score is None or not r.get("url"):
            continue
        affinity = 1 if _hits(r.get("name") or "", keywords) else 0
        key = (affinity, score, r.get("last_modified") or r.get("metadata_modified") or "")
        if best is None or key > best[0]:
            best = (key, r, score)
    if best is None:
        return None, None
    return best[1], best[2]


def location_signal(inspection: Inspection | None) -> tuple[float | None, str | None, list[str]]:
    """(score, locationSource, reasons). Address-only rows are usable via geocoding (ADR 0007)."""
    if inspection is None:
        return None, None, ["位置情報は未検査（取得失敗または非対応形式）"]
    notes = []
    if inspection.coordFillRate is not None:
        rate = inspection.coordFillRate
        notes.append(
            f"座標充足率 {round(rate * 100)}%（{inspection.latField}・{inspection.lngField}）"
        )
        if rate >= ACCEPT_MIN_COORD_FILL:
            return 1.0, "source", notes
    address_rate = inspection.addressFillRate or 0.0
    if inspection.addressField and address_rate >= ACCEPT_MIN_ADDRESS_FILL:
        notes.append(
            f"住所充足率 {round(address_rate * 100)}%（{inspection.addressField}）。"
            "住所からジオコーディングする"
        )
        return GEOCODE_LOCATION, "geocode", notes
    if inspection.coordFillRate:
        return round(inspection.coordFillRate / ACCEPT_MIN_COORD_FILL, 3), "source", notes
    if inspection.addressField and address_rate > 0:
        notes.append(f"住所充足率 {round(address_rate * 100)}%（不足）")
        return round(address_rate * GEOCODE_LOCATION, 3), "geocode", notes
    notes.append("座標・住所とも値がない" if notes else "座標列・住所列が見つからない")
    return 0.0, None, notes


def license_signal(package: Mapping[str, Any]) -> tuple[float, str]:
    lid = (package.get("license_id") or "").lower()
    title = package.get("license_title") or ""
    if lid in OPEN_LICENSE_IDS or any(w in title for w in OPEN_LICENSE_WORDS):
        return 1.0, package.get("license_id") or title
    return 0.5, f"ライセンス不明（{package.get('license_id') or '未設定'}）"


def freshness_signal(modified: str | None, now: datetime) -> float:
    if not modified:
        return 0.3
    try:
        dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
    except ValueError:
        return 0.3
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=now.tzinfo)
    years = (now - dt).days / 365.25
    return 1.0 if years <= 2 else 0.6 if years <= 5 else 0.3


def evaluate(
    package: Mapping[str, Any],
    d: FeatureDefinition,
    resource: Mapping[str, Any] | None,
    format_score: float | None,
    inspection: Inspection | None,
    now: datetime,
) -> Evaluation:
    title = package.get("title") or ""
    semantic, reasons = semantic_signal(package, d)
    location, location_source, loc_reasons = location_signal(inspection)
    license_score, license_note = license_signal(package)
    modified = (resource or {}).get("last_modified") or package.get("metadata_modified")
    freshness = freshness_signal(modified, now)
    signals: dict[str, float | None] = {
        "semantic": semantic,
        "format": format_score or 0.0,
        "location": location,
        "license": license_score,
        "freshness": freshness,
    }
    confidence = round(
        sum(
            WEIGHTS[k] * (UNKNOWN_LOCATION if v is None and k == "location" else (v or 0.0))
            for k, v in signals.items()
        ),
        3,
    )

    excluded = _hits(title, d.exclude_keywords)
    if resource is None:
        status, reasons = "rejected", reasons + ["機械可読なリソースがない（PDF・画像等のみ）"]
    elif excluded:
        status, reasons = "rejected", reasons + [f"除外語「{'」「'.join(excluded)}」を含む"]
    elif semantic == 0:
        status = "rejected"
    else:
        fmt = "DataStore(API) 対応 " if resource.get("datastore_active") else ""
        reasons = reasons + [f"{fmt}{(resource.get('format') or '').upper()}"] + loc_reasons
        reasons.append(license_note)
        accepted = (
            confidence >= ACCEPT_CONFIDENCE
            and semantic >= ACCEPT_MIN_SEMANTIC
            and location is not None
            and location >= ACCEPT_MIN_LOCATION
        )
        status = "accepted" if accepted else "review"
    if modified:
        reasons.append(f"更新 {modified[:10]}")
    return Evaluation(
        status=status,
        confidence=confidence,
        location_source=location_source,
        signals=signals,
        reason="。".join(reasons),
    )
