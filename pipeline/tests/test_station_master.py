import pytest

from station_pipeline.geo.municipalities import Municipality
from station_pipeline.stations.master import (
    StationMasterError,
    build_master,
    geocode_scope,
    line_label,
    resolve_station,
    slug,
)


def feat(name, operator, line, group, coords):
    return {
        "properties": {"N02_003": line, "N02_004": operator, "N02_005": name, "N02_005g": group},
        "geometry": {"type": "LineString", "coordinates": coords},
    }


# Shapes observed in N02-24: 上野 has JR + Metro in one group; 京成上野 is a separate group.
FEATURES = [
    feat("上野", "東日本旅客鉄道", "東北線", "003505", [[139.776, 35.713], [139.778, 35.715]]),
    feat("上野", "東日本旅客鉄道", "東北線", "003505", [[139.777, 35.714], [139.777, 35.714]]),
    feat("上野", "東京地下鉄", "3号線銀座線", "003505", [[139.7775, 35.7115], [139.7777, 35.7117]]),
    feat(
        "上野", "東京地下鉄", "2号線日比谷線", "003505", [[139.7775, 35.7125], [139.7777, 35.7127]]
    ),
    feat("京成上野", "京成電鉄", "本線", "003521", [[139.773, 35.711], [139.773, 35.712]]),
    feat(
        "高輪ゲートウェイ",
        "東日本旅客鉄道",
        "東海道線",
        "009999",
        [[139.740, 35.635], [139.740, 35.636]],
    ),
    feat("東京", "東京地下鉄", "4号線丸ノ内線", "001234", [[139.766, 35.681], [139.766, 35.682]]),
]
SOURCE = {"name": "N02", "publisher": "国土交通省", "license": "CC BY 4.0", "page": "https://n02"}


def test_slug_and_line_label():
    assert slug("Takanawa Gateway") == "takanawa-gateway"
    assert slug("Shin-Okubo") == "shin-okubo"
    assert line_label("東京地下鉄", "2号線日比谷線") == "東京メトロ日比谷線"
    assert line_label("東日本旅客鉄道", "東北線") == "JR東北線"
    assert line_label("京成電鉄", "本線") == "京成電鉄本線"


def test_resolve_uses_operator_points_and_group_lines():
    r = resolve_station("上野", "東日本旅客鉄道", FEATURES)
    # mean of the two JR midpoints only (subway platforms do not move the station point)
    assert (r["lat"], r["lng"]) == (35.714, 139.777)
    assert r["lines"] == ["JR東北線", "東京メトロ銀座線", "東京メトロ日比谷線"]  # not 京成
    assert r["n02Groups"] == ["003505"]


def test_unknown_or_other_operator_only_fails():
    with pytest.raises(StationMasterError, match="not found"):
        resolve_station("存在しない", "東日本旅客鉄道", FEATURES)
    with pytest.raises(StationMasterError, match="not found"):
        resolve_station("東京", "東日本旅客鉄道", FEATURES)  # only a Metro feature


def run(names, english):
    return build_master(
        names,
        "東日本旅客鉄道",
        FEATURES,
        english,
        lambda lat, lng: Municipality("13106", "台東区"),
        lambda lat, lng, r: [Municipality("13106", "台東区"), Municipality("13105", "文京区")],
        500,
        SOURCE,
    )


def test_build_master():
    m = run(["上野", "高輪ゲートウェイ"], {"上野": "Ueno", "高輪ゲートウェイ": "Takanawa Gateway"})
    ueno, tgw = m["stations"]
    assert (ueno["id"], ueno["municipality"]) == ("ueno", "台東区")
    assert ueno["areaMunicipalities"] == ["台東区", "文京区"]
    assert tgw["id"] == "takanawa-gateway"
    assert m["sources"][0]["kind"] == "opendata" and m["sources"][0]["license"] == "CC BY 4.0"
    assert geocode_scope(m, ["東京都建設局"]) == {"台東区", "文京区", "東京都建設局"}


def test_missing_english_name_fails():
    with pytest.raises(StationMasterError, match="English"):
        run(["上野"], {})


def test_duplicate_names_fail():
    with pytest.raises(StationMasterError, match="duplicate"):
        run(["上野", "上野"], {"上野": "Ueno"})
