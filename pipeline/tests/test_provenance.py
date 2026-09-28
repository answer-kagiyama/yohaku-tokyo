from station_pipeline.provenance import build_provenance

MANIFEST = {
    "catalog": "https://c",
    "features": {
        "park": {"label": "公園", "candidates": 3, "accepted": 2, "review": 0, "rejected": 1}
    },
    "datasets": [
        {
            "feature": "park",
            "datasetId": "a",
            "name": "公園一覧",
            "organization": "台東区",
            "sourceUrl": "https://c/dataset/a",
            "status": "accepted",
            "autoStatus": "accepted",
            "license": "CC-BY-4.0",
            "reason": "r",
            "review": None,
        },
        {
            "feature": "park",
            "datasetId": "b",
            "name": "区立公園",
            "organization": "文京区",
            "sourceUrl": "https://c/dataset/b",
            "status": "accepted",
            "autoStatus": "rejected",
            "review": {"status": "accepted", "note": "人手で確認"},
        },
        {
            "feature": "park",
            "datasetId": "x",
            "name": "公園トイレ",
            "organization": "練馬区",
            "sourceUrl": "https://c/dataset/x",
            "status": "rejected",
            "autoStatus": "rejected",
        },
    ],
}
REPORTS = {
    "park": {
        "datasets": [
            {
                "datasetId": "a",
                "status": "ok",
                "retrievedAt": "2026-09-28T00:00:00Z",
                "sha256": "h",
                "rows": 10,
                "withSourceCoords": 6,
                "geocoded": 3,
                "unlocated": 1,
                "excluded": 2,
                "outsideTokyo": 0,
            },
        ]
    }
}


def test_only_accepted_with_ingest_stats():
    p = build_provenance(MANIFEST, REPORTS, "t")
    assert [d["datasetId"] for d in p["datasets"]] == [
        "a",
        "b",
    ]  # sorted by organization; x not accepted
    a = next(d for d in p["datasets"] if d["datasetId"] == "a")
    assert a["ingest"]["located"] == 9
    assert a["ingest"]["rows"] == 10
    b = next(d for d in p["datasets"] if d["datasetId"] == "b")
    assert b["ingest"] is None
    assert b["reviewNote"] == "人手で確認"
    assert b["autoStatus"] == "rejected"


def test_feature_counts_and_services():
    p = build_provenance(MANIFEST, REPORTS, "t")
    assert p["features"] == [
        {"key": "park", "candidates": 3, "accepted": 2, "review": 0, "rejected": 1}
    ]
    assert any("国土地理院" in s["name"] for s in p["services"])
