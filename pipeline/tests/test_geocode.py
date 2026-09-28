import json

import pytest

from station_pipeline.geo.geocode import (
    GsiGeocoder,
    below_municipality,
    classify_match,
    complete_address,
)
from station_pipeline.http import HttpClient


def gsi(features):
    body = [
        {"geometry": {"coordinates": [lng, lat]}, "properties": {"title": title}}
        for title, lat, lng in features
    ]
    return lambda url: json.dumps(body).encode()


def geocoder(features):
    return GsiGeocoder(HttpClient(gsi(features), sleep=lambda s: None))


def test_exact_match():
    g = geocoder([("東京都千代田区外神田二丁目１６番９号", 35.702072, 139.76712)])
    r = g.geocode("東京都千代田区外神田二丁目16番９号")
    assert r is not None
    assert (r.lat, r.lng, r.precision, r.provider) == (35.702072, 139.76712, "exact", "gsi")


def test_partial_match_at_chome_level():
    g = geocoder([("東京都千代田区外神田二丁目", 35.70, 139.77)])
    r = g.geocode("東京都千代田区外神田二丁目16番9号")
    assert r is not None and r.precision == "partial"


def test_municipality_centroid_is_rejected():
    # Observed: the API answers unknown addresses with the ward's representative point.
    g = geocoder([("東京都千代田区", 35.69389, 139.753616)])
    assert g.geocode("東京都千代田区存在しない町99") is None


def test_unrelated_match_is_rejected():
    g = geocoder([("東京都台東区上野一丁目", 35.70, 139.77)])
    assert g.geocode("東京都千代田区外神田二丁目16番9号") is None


def test_outside_tokyo_is_rejected():
    g = geocoder([("東京都千代田区外神田二丁目", 0.0, 0.0)])
    assert g.geocode("東京都千代田区外神田二丁目1") is None


def test_no_results():
    assert geocoder([]).geocode("東京都千代田区外神田二丁目1") is None


def test_takes_first_acceptable_candidate():
    g = geocoder([("東京都千代田区", 35.6, 139.7), ("東京都千代田区外神田二丁目", 35.70, 139.77)])
    r = g.geocode("東京都千代田区外神田二丁目1")
    assert r is not None and r.matched == "東京都千代田区外神田二丁目"


@pytest.mark.parametrize(
    "address, municipality, expected",
    [
        ("東京都千代田区外神田2-16-9", "千代田区", "東京都千代田区外神田2-16-9"),
        ("千代田区外神田2-16-9", "千代田区", "東京都千代田区外神田2-16-9"),
        ("外神田２－１６－９", "千代田区", "東京都千代田区外神田2-16-9"),
        ("外神田 2-16-9", None, "東京都外神田2-16-9"),
    ],
)
def test_complete_address(address, municipality, expected):
    assert complete_address(address, municipality) == expected


@pytest.mark.parametrize(
    "matched, rest",
    [
        ("東京都武蔵村山市", ""),  # regex-based splitting would wrongly leave "山市"
        ("東京都東村山市本町", "本町"),
        ("東京都西多摩郡瑞穂町", ""),
        ("東京都千代田区外神田二丁目", "外神田二丁目"),
    ],
)
def test_below_municipality(matched, rest):
    assert below_municipality(matched) == rest


def test_classify_match_normalizes_width():
    assert (
        classify_match("東京都千代田区外神田2丁目16番9号", "東京都千代田区外神田２丁目１６番９号")
        == "exact"
    )


@pytest.mark.parametrize(
    "query, matched, expected",
    [
        # Observed: source data uses "3－13－9", the API answers "三丁目１３番９号"
        ("東京都墨田区両国3－13－9", "東京都墨田区両国三丁目１３番９号", "exact"),
        ("東京都中央区日本橋兜町15-3", "東京都中央区日本橋兜町１５番３号", "exact"),
        (
            "東京都千代田区神田佐久間町三丁目21番地",
            "東京都千代田区神田佐久間町三丁目２１番地",
            "exact",
        ),
        ("東京都千代田区隼町４番３号", "東京都千代田区隼町４番", "partial"),
        ("東京都千代田区外神田2-16-9", "東京都千代田区外神田二丁目", "partial"),
        # prefix without a boundary is NOT a match: 銀座1-2 is not 銀座1-25-2
        ("東京都中央区銀座1-25-2", "東京都中央区銀座一丁目２番", None),
        ("東京都墨田区両国3-13-9", "東京都墨田区", None),
        ("東京都千代田区外神田2-16-9", "東京都千代田区外神田", "partial"),
        ("東京都港区芝公園1-1", "東京都港区芝", None),
    ],
)
def test_classify_match_canonical_forms(query, matched, expected):
    assert classify_match(query, matched) == expected


@pytest.mark.parametrize(
    "address, organization, expected",
    [
        # organization is not a municipality and the address already has one
        ("港区六本木七丁目ほか", "東京都建設局", "東京都港区六本木七丁目"),
        (
            "武蔵野市御殿山一丁目/三鷹市井の頭三丁目ほか",
            "東京都建設局",
            "東京都武蔵野市御殿山一丁目",
        ),
        ("あきる野市二宮・平沢", "東京都建設局", "東京都あきる野市二宮"),
        ("台東区上野公園ほか", "東京都建設局", "東京都台東区上野公園"),
        ("外神田2-16-9", "千代田区", "東京都千代田区外神田2-16-9"),
        ("東京都中央区京橋1-19-13先", "中央区", "東京都中央区京橋1-19-13"),
        # observed in 豊島区 文化財一覧: address + full-width space + place name
        ("豊島区長崎1-9-2\u3000金剛院", "豊島区", "東京都豊島区長崎1-9-2"),
        ("豊島区池袋本町3-14-1　氷川神社境内", "豊島区", "東京都豊島区池袋本町3-14-1"),
        ("東京都 千代田区 外神田2-16-9", "千代田区", "東京都千代田区外神田2-16-9"),
        (
            "東京都中央区八丁堀2-1-12先;東京都中央区八丁堀3-1-20先",
            "中央区",
            "東京都中央区八丁堀2-1-12",
        ),
        (
            "東京都千代田区千代田区富士見二丁目他・東京都新宿区市谷本村町他",
            "千代田区",
            "東京都千代田区富士見二丁目",
        ),
    ],
)
def test_complete_address_cleans_multi_area_addresses(address, organization, expected):
    assert complete_address(address, organization) == expected
