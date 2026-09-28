from datetime import UTC, datetime

import pytest

from station_pipeline.discover.definitions import FeatureDefinition
from station_pipeline.discover.evaluate import evaluate, pick_resource
from station_pipeline.inspect.schema import inspect_datastore

from .ckan_fakes import datastore_result, package, resource

NOW = datetime(2026, 9, 27, tzinfo=UTC)
PARK = FeatureDefinition(
    key="park",
    label="公園",
    keywords=("公園", "緑地"),
    list_hints=("一覧",),
    exclude_keywords=("推移", "画像"),
)
FILLED = [{"名称": f"p{i}", "緯度": "35.6", "経度": "139.7"} for i in range(10)]
EMPTY = [{"名称": f"p{i}", "所在地": "東京都", "緯度": "", "経度": ""} for i in range(10)]


def run(pkg, records=None, fields=("名称", "所在地", "緯度", "経度")):
    res, score = pick_resource(pkg)
    insp = (
        inspect_datastore(datastore_result(list(fields), records)) if records is not None else None
    )
    return evaluate(pkg, PARK, res, score, insp, NOW)


def test_datastore_list_with_coordinates_is_accepted():
    pkg = package("a", "都市公園一覧", [resource("r1", datastore=True)])
    ev = run(pkg, FILLED)
    assert ev.status == "accepted"
    assert ev.confidence >= 0.75
    assert "座標充足率 100%" in ev.reason
    assert "DataStore" in ev.reason


def test_empty_coordinates_with_addresses_are_usable_via_geocoding():
    # Real case (Chiyoda, Ota…): 緯度/経度 columns exist but are empty; addresses are filled.
    pkg = package("a", "都市公園一覧", [resource("r1", datastore=True)])
    ev = run(pkg, EMPTY)
    assert ev.status == "accepted"
    assert ev.location_source == "geocode"
    assert ev.signals["location"] == 0.8
    assert "座標充足率 0%" in ev.reason
    assert "ジオコーディング" in ev.reason


def test_empty_coordinates_and_addresses_are_not_accepted():
    pkg = package("a", "都市公園一覧", [resource("r1", datastore=True)])
    records = [{"名称": f"p{i}", "所在地": "", "緯度": "", "経度": ""} for i in range(10)]
    ev = run(pkg, records)
    assert ev.status == "review"
    assert ev.signals["location"] == 0.0
    assert ev.location_source is None


def test_source_coordinates_are_preferred():
    pkg = package("a", "都市公園一覧", [resource("r1", datastore=True)])
    assert run(pkg, FILLED).location_source == "source"


def test_pdf_only_is_rejected():
    pkg = package("a", "公園一覧", [resource("r1", fmt="PDF"), resource("r2", fmt="JPEG")])
    ev = run(pkg)
    assert ev.status == "rejected"
    assert "機械可読なリソースがない" in ev.reason


def test_excluded_keyword_is_rejected():
    pkg = package("a", "町別の都市公園の推移", [resource("r1", datastore=True)])
    ev = run(pkg, FILLED)
    assert ev.status == "rejected"
    assert "推移" in ev.reason


def test_no_keyword_match_is_rejected():
    pkg = package("a", "保育園一覧", [resource("r1")], notes="保育園")
    assert run(pkg).status == "rejected"


def test_uninspected_csv_goes_to_review_and_says_so():
    pkg = package("a", "公園一覧", [resource("r1", fmt="CSV")])
    ev = run(pkg)
    assert ev.status == "review"
    assert ev.signals["location"] is None
    assert "未検査" in ev.reason


def test_title_without_list_hint_is_weaker():
    pkg = package("a", "区立公園", [resource("r1", datastore=True)])
    ev = run(pkg, FILLED)
    assert ev.signals["semantic"] == 0.7


def test_keyword_only_in_notes():
    pkg = package("a", "施設一覧", [resource("r1")], notes="公園を含む施設")
    ev = run(pkg)
    assert ev.signals["semantic"] == 0.4
    assert ev.status == "review"


def test_unknown_license_lowers_confidence():
    good = run(package("a", "公園一覧", [resource("r1", datastore=True)]), FILLED)
    bad = run(
        package("a", "公園一覧", [resource("r1", datastore=True)], license_id="", license_title=""),
        FILLED,
    )
    assert bad.signals["license"] == 0.5
    assert bad.confidence < good.confidence


@pytest.mark.parametrize(
    "modified, expected", [("2025-12-01", 1.0), ("2022-01-01", 0.6), ("2015-01-01", 0.3)]
)
def test_freshness(modified, expected):
    pkg = package("a", "公園一覧", [resource("r1", datastore=True, last_modified=modified)])
    assert run(pkg, FILLED).signals["freshness"] == expected


def test_pick_resource_prefers_datastore_then_format_then_recency():
    pkg = package(
        "a",
        "公園一覧",
        [
            resource("pdf", fmt="PDF"),
            resource("xlsx", fmt="XLSX"),
            resource("csv-old", fmt="CSV", last_modified="2020-01-01"),
            resource("csv-new", fmt="CSV", last_modified="2025-01-01"),
        ],
    )
    assert pick_resource(pkg)[0]["id"] == "csv-new"
    pkg["resources"].append(resource("ds", fmt="CSV", datastore=True, last_modified="2019-01-01"))
    assert pick_resource(pkg)[0]["id"] == "ds"


def test_deterministic():
    pkg = package("a", "公園一覧", [resource("r1", datastore=True)])
    assert run(pkg, FILLED) == run(pkg, FILLED)


def test_per_category_resource_is_picked_and_counts_as_semantic():
    # observed: 港区の公共施設情報 has one file per category
    pkg = package(
        "minato",
        "港区の公共施設情報",
        [
            resource("gakkou", datastore=True, name="学校教育・子どもの施設"),
            resource("kouen", name="公園・児童遊園・緑地"),
            resource("benjo", datastore=True, name="公衆便所一覧"),
        ],
        notes="港区の施設",
    )
    res, _ = pick_resource(pkg, PARK.keywords)
    assert res["id"] == "kouen"
    ev = run_with(pkg, res)
    assert ev.signals["semantic"] == 0.7
    assert "リソース名に「公園」「緑地」" in ev.reason


def run_with(pkg, res):
    from station_pipeline.discover.evaluate import FORMAT_SCORES

    return evaluate(pkg, PARK, res, FORMAT_SCORES["CSV"], None, NOW)
