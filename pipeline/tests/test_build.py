import json

from station_pipeline.build import build_from_fixture
from station_pipeline.config import FEATURES
from station_pipeline.export import export_web, write_dataset
from station_pipeline.quality import validate_dataset

FIXED_TIME = "2026-09-27T00:00:00Z"


def test_builds_five_stations(fixture_path):
    data = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    validate_dataset(data)
    assert [s["id"] for s in data["stations"]] == [
        "akihabara",
        "okachimachi",
        "ueno",
        "kanda",
        "asakusabashi",
    ]
    assert data["isFixture"] is True
    assert data["radiusMeters"] == 500
    assert data["generatedAt"] == FIXED_TIME


def test_every_station_has_all_feature_keys(fixture_path):
    data = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    for s in data["stations"]:
        assert set(s["raw"]) == set(FEATURES)
        assert set(s["normalized"]) == set(FEATURES)
        assert s["sources"], s["id"]


def test_missing_is_preserved_not_zero(fixture_path):
    data = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    by_id = {s["id"]: s for s in data["stations"]}
    assert by_id["asakusabashi"]["raw"]["library"] is None
    assert by_id["asakusabashi"]["normalized"]["library"] is None
    assert by_id["asakusabashi"]["scores"]["coverage"] == 0.9
    # kanda has a real 0 -> it is ranked
    assert by_id["kanda"]["raw"]["library"] == 0
    assert by_id["kanda"]["normalized"]["library"] == 0.0


def test_deterministic(fixture_path):
    a = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    b = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_ueno_is_least_yohaku(fixture_path):
    data = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    ranked = sorted(data["stations"], key=lambda s: s["scores"]["yohaku"])
    assert ranked[0]["id"] == "ueno"


def test_write_and_export(tmp_path, fixture_path):
    data = build_from_fixture(fixture_path, generated_at=FIXED_TIME)
    processed = tmp_path / "processed" / "stations.json"
    write_dataset(data, processed)
    web = tmp_path / "web" / "stations.json"
    export_web(processed, web)
    assert json.loads(web.read_text(encoding="utf-8")) == data


def _park_aggregate(akiba_status="complete", akiba_count=6):
    stations = []
    for sid in ["akihabara", "okachimachi", "ueno", "kanda", "asakusabashi"]:
        complete = sid != "akihabara" or akiba_status == "complete"
        count = akiba_count if sid == "akihabara" else 3
        stations.append(
            {
                "stationId": sid,
                "status": "complete" if complete else "incomplete",
                "count": count if complete else None,
                "lowerBound": count,
                "municipalities": [{"code": "13101", "name": "千代田区", "coverage": "covered"}],
                "facilities": [
                    {"name": "秋葉原公園", "distanceM": 120.5, "coordSource": "source", "x": 1}
                ],
                "datasets": ["chiyoda-parks"],
            }
        )
    return {"park": {"radiusMeters": 500, "stations": stations}}


MANIFEST = {
    "datasets": [
        {
            "feature": "park",
            "datasetId": "chiyoda-parks",
            "name": "都市公園・都立公園一覧",
            "organization": "千代田区",
            "sourceUrl": "https://catalog.data.metro.tokyo.lg.jp/dataset/chiyoda-parks",
            "license": "CC-BY-4.0",
        }
    ]
}


def test_real_aggregate_replaces_fixture_value(fixture_path):
    data = build_from_fixture(
        fixture_path, FIXED_TIME, aggregates=_park_aggregate(), manifest=MANIFEST
    )
    validate_dataset(data)
    akiba = next(s for s in data["stations"] if s["id"] == "akihabara")
    assert akiba["raw"]["park"] == 6
    assert akiba["evidence"]["park"]["facilities"] == [
        {"name": "秋葉原公園", "distanceM": 120.5, "coordSource": "source"}
    ]
    assert data["fixtureFeatures"] == [
        "tourism",
        "culture",
        "publicFacility",
        "library",
        "stationUsage",
    ]
    assert data["isFixture"] is True
    kinds = {s["kind"]: s for s in akiba["sources"]}
    assert kinds["opendata"]["url"].endswith("/dataset/chiyoda-parks")
    assert kinds["opendata"]["features"] == ["park"]
    assert "park" not in kinds["fixture"]["features"]


def test_incomplete_aggregate_is_missing_not_zero(fixture_path):
    data = build_from_fixture(
        fixture_path,
        FIXED_TIME,
        aggregates=_park_aggregate(akiba_status="incomplete"),
        manifest=MANIFEST,
    )
    akiba = next(s for s in data["stations"] if s["id"] == "akihabara")
    assert akiba["raw"]["park"] is None
    assert akiba["normalized"]["park"] is None
    assert akiba["evidence"]["park"]["lowerBound"] == 6


def test_without_aggregates_everything_is_fixture(fixture_path):
    data = build_from_fixture(fixture_path, FIXED_TIME)
    assert data["fixtureFeatures"] == list(FEATURES)
    assert all(s["evidence"] == {} for s in data["stations"])


def test_station_master_source_is_kept(tmp_path, fixture_path):
    import json as _json

    master = _json.loads(fixture_path.read_text(encoding="utf-8"))
    master["sources"].append(
        {
            "id": "mlit-n02",
            "name": "N02",
            "organization": "国土交通省",
            "url": "https://n02",
            "license": "CC BY 4.0",
            "features": [],
            "kind": "opendata",
        }
    )
    path = tmp_path / "master.json"
    path.write_text(_json.dumps(master, ensure_ascii=False), encoding="utf-8")
    data = build_from_fixture(path, FIXED_TIME, aggregates=_park_aggregate(), manifest=MANIFEST)
    assert any(s["id"] == "mlit-n02" for s in data["stations"][0]["sources"])
