import json

import pytest

from station_pipeline.discover.catalog import CkanCatalog
from station_pipeline.http import HttpClient
from station_pipeline.ridership import (
    aggregate_ridership,
    days_in_fiscal_year,
    find_yearbook,
    parse_station_table,
    station_tables,
    title_year,
)

from .ckan_fakes import fake_transport, package, resource

# Shapes observed in 東京都統計年鑑 令和6年 4-7 / 4-14 (values in thousands per year).
JR = (
    "年度,Fiscal year,系統,Line,駅,Station,マーク Mark,乗車人員 Boarding passengers／総数 Total,乗車人員 Boarding passengers／定期 Commuter Pass\n"
    "令和5,2023,東北本線,Tohoku Line,秋葉原,Akihabara,,70000,30000\n"
    "令和6,2024,総数,Total,,,,3073039,1674667\n"
    "令和6,2024,東北本線,Tohoku Line,秋葉原,Akihabara,,80819,34381\n"
    "令和6,2024,東北本線,Tohoku Line,御徒町,Okachimachi,,22989,11162\n"
)
SUBWAY = (
    "年度,Fiscal year,会社名,Company name,系統,Line,駅,Station,マーク Mark,乗車人員 Boarding passengers／総数 Total,降車人員 Alighting／総数 Total\n"
    "令和6,2024,東京地下鉄株式会社,Tokyo Metro,日比谷線,Hibiya Line,秋葉原,Akihabara,,20138,20662\n"
    "令和6,2024,東京地下鉄株式会社,Tokyo Metro,日比谷線,Hibiya Line,仲御徒町,Naka-Okachimachi,◎,7541,7652\n"
    "令和6,2024,都営,Toei Subway,大江戸線,Oedo Line,新駅,New,,-,-\n"
)
STATIONS = [
    {"id": "akihabara", "name": "秋葉原"},
    {"id": "okachimachi", "name": "御徒町"},
    {"id": "nowhere", "name": "存在しない"},
]


def test_title_year():
    assert title_year("東京都統計年鑑　令和6年　4　運輸・観光") == 2024
    assert title_year("東京都統計年鑑　平成31・令和元年　4　運輸") == 2019
    assert title_year("東京都統計年鑑　平成22年　4　運輸") == 2010
    assert title_year("運輸") is None


def test_days_in_fiscal_year():
    assert days_in_fiscal_year(2024) == 365  # Apr 2024 - Mar 2025
    assert days_in_fiscal_year(2023) == 366  # includes Feb 2024


def test_parse_takes_latest_year_and_skips_totals_and_dashes():
    year, rows = parse_station_table(JR.encode("utf-8-sig"), "JR")
    assert year == 2024
    assert [(r["station"], r["annualThousands"], r["operator"]) for r in rows] == [
        ("秋葉原", 80819, "JR東日本"),
        ("御徒町", 22989, "JR東日本"),
    ]
    _, rows = parse_station_table(SUBWAY.encode(), "subway")
    assert [r["station"] for r in rows] == ["秋葉原", "仲御徒町"]  # "-" row skipped
    assert rows[0]["operator"] == "東京地下鉄株式会社"


def test_aggregate_sums_operators_by_exact_name():
    tables = [parse_station_table(JR.encode(), "JR"), parse_station_table(SUBWAY.encode(), "S")]
    result = aggregate_ridership(STATIONS, tables, "yearbook", "t")
    by_id = {s["stationId"]: s for s in result["stations"]}
    # (80819 + 20138) thousand / 365 days
    assert by_id["akihabara"]["count"] == round(100957 * 1000 / 365)
    assert [x["line"] for x in by_id["akihabara"]["lines"]] == ["東北本線", "日比谷線"]
    # 仲御徒町 is a different station
    assert by_id["okachimachi"]["count"] == round(22989 * 1000 / 365)
    assert by_id["nowhere"] == {
        "stationId": "nowhere",
        "status": "incomplete",
        "count": None,
        "lowerBound": 0,
        "lines": [],
        "datasets": [],
    }
    assert result["fiscalYear"] == 2024


def test_unexpected_columns():
    with pytest.raises(RuntimeError, match="unexpected columns"):
        parse_station_table(b"a,b\n1,2\n", "x")


def test_find_latest_yearbook_and_tables():
    old = package(
        "y2023",
        "東京都統計年鑑　令和5年　4　運輸",
        [resource("r0", name="4-7　ＪＲの駅別乗車人員")],
        org="東京都総務局",
    )
    new = package(
        "y2024",
        "東京都統計年鑑　令和6年　4　運輸・観光",
        [
            resource("a", name="4-6　観測地点別交通量"),
            resource("b", name="4-7　ＪＲの駅別乗車人員"),
            resource("c", name="4-14　地下鉄の駅別乗降車人員"),
            resource("d", fmt="PDF", name="4-12　私鉄の駅別乗降車人員"),
        ],
        org="東京都総務局",
    )
    other = package("x", "東京都統計年鑑　令和7年　運輸", [], org="どこかの区")
    client = HttpClient(fake_transport({"東京都統計年鑑 運輸": [old, new, other]}, {}))
    catalog = CkanCatalog(client, "https://c")
    pkg = find_yearbook(catalog)
    assert pkg["name"] == "y2024"
    assert [t["id"] for t in station_tables(pkg)] == ["b", "c"]
    json.dumps(pkg)
