"""Product-wide provenance summary for the /data page (spec 0007)."""

from collections.abc import Mapping
from typing import Any

SERVICES = [
    {
        "name": "国土数値情報 鉄道データ（N02, 国土交通省, CC BY 4.0）",
        "use": (
            "駅の位置・路線（駅マスタ, ADR 0010）。"
            "「国土数値情報（鉄道データ）」（国土交通省）を加工して作成"
        ),
        "url": "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2024.html",
    },
    {
        "name": "東京都オープンデータカタログ（CKAN / DataStore API）",
        "use": "データセットの探索・メタデータ・リソース取得",
        "url": "https://catalog.data.metro.tokyo.lg.jp",
    },
    {
        "name": "国土地理院 住所検索 API",
        "use": "住所のみの施設のジオコーディング（ADR 0007）",
        "url": "https://msearch.gsi.go.jp/address-search/AddressSearch",
    },
    {
        "name": "国土地理院 逆ジオコーダ",
        "use": "駅の 500m 圏に掛かる区市町村の特定（ADR 0008）",
        "url": "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress",
    },
]


def build_provenance(
    manifest: Mapping[str, Any],
    reports: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    ingest_by_id = {
        (feature, d["datasetId"]): d
        for feature, report in reports.items()
        for d in report.get("datasets", [])
    }
    datasets = []
    for e in manifest.get("datasets", []):
        if e["status"] != "accepted":
            continue
        d = ingest_by_id.get((e["feature"], e["datasetId"]))
        datasets.append(
            {
                "feature": e["feature"],
                "datasetId": e["datasetId"],
                "name": e["name"],
                "organization": e.get("organization"),
                "license": e.get("license"),
                "sourceUrl": e["sourceUrl"],
                "status": e["status"],
                "autoStatus": e.get("autoStatus", e["status"]),
                "reviewNote": (e.get("review") or {}).get("note"),
                "reason": e.get("reason"),
                "ingest": None
                if d is None
                else {
                    "status": d["status"],
                    "retrievedAt": d.get("retrievedAt"),
                    "sha256": d.get("sha256"),
                    "rows": d.get("rows"),
                    "located": (d.get("withSourceCoords") or 0) + (d.get("geocoded") or 0),
                    "unlocated": d.get("unlocated"),
                    "excluded": d.get("excluded"),
                    "outsideTokyo": d.get("outsideTokyo"),
                    "error": d.get("error"),
                },
            }
        )
    features = [
        {
            "key": key,
            **{
                k: v
                for k, v in stats.items()
                if k in ("candidates", "accepted", "review", "rejected")
            },
        }
        for key, stats in manifest.get("features", {}).items()
    ]
    datasets.sort(key=lambda d: (d["feature"], d["organization"] or "", d["name"]))
    return {
        "generatedAt": generated_at,
        "catalog": manifest.get("catalog"),
        "features": features,
        "datasets": datasets,
        "services": SERVICES,
    }
