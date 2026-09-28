from datetime import UTC, datetime

from station_pipeline.config import FEATURES
from station_pipeline.discover.catalog import CkanCatalog
from station_pipeline.discover.definitions import FeatureDefinition, load_definitions
from station_pipeline.discover.run import discover_feature, search_candidates
from station_pipeline.http import JsonClient

from .ckan_fakes import datastore_result, fake_transport, package, resource
from .conftest import REPO_ROOT

NOW = datetime(2026, 9, 27, tzinfo=UTC)
PARK = FeatureDefinition(
    key="park",
    label="公園",
    keywords=("公園", "緑地"),
    list_hints=("一覧",),
    exclude_keywords=("推移",),
)
FILLED = datastore_result(
    ["名称", "緯度", "経度"], [{"名称": "a", "緯度": "35.6", "経度": "139.7"}]
)


def make_catalog(search, datastore, files=None):
    client = JsonClient(fake_transport(search, datastore, files), sleep=lambda s: None)
    return CkanCatalog(client, "https://catalog.example"), client


def test_pagination_and_dedup_across_keywords():
    many = [package(f"p{i:03d}", f"公園{i}", [resource(f"r{i}")]) for i in range(150)]
    shared = package("shared", "緑地一覧", [resource("rs")])
    catalog, client = make_catalog({"公園": many + [shared], "緑地": [shared]}, {})
    found = search_candidates(catalog, PARK)
    assert len(found) == 151
    assert client.network_calls == 3  # 公園: 2 pages, 緑地: 1 page


def test_end_to_end_with_inspect_failure():
    search = {
        "公園": [
            package("good", "都市公園一覧", [resource("r-good", datastore=True)]),
            package("broken", "区立公園一覧", [resource("r-broken", datastore=True)], org="品川区"),
            package("pdf", "公園一覧", [resource("r-pdf", fmt="PDF")], org="港区"),
            package(
                "plain-csv",
                "都市公園一覧",
                [resource("r-csv", url="https://files/chiyoda.csv")],
                org="千代田区",
            ),
            package("trend", "公園数の推移", [resource("r-trend", datastore=True)], org="北区"),
        ]
    }
    datastore = {"r-good": FILLED, "r-broken": RuntimeError("datastore down")}
    chiyoda = "名称,所在地_連結表記,緯度,経度\n宮本公園,東京都千代田区外神田二丁目16番９号,,\n"
    files = {"https://files/chiyoda.csv": chiyoda.encode("cp932")}
    catalog, _ = make_catalog(search, datastore, files)
    entries = {e["datasetId"]: e for e in discover_feature(catalog, PARK, NOW)}

    assert entries["good"]["status"] == "accepted"
    assert entries["good"]["sourceUrl"] == "https://catalog.example/dataset/good"
    assert entries["good"]["inspection"]["coordFillRate"] == 1.0
    assert entries["good"]["updateFrequency"] == "随時"

    # inspect failure: location unknown (not 0), pipeline continues
    assert entries["broken"]["status"] == "review"
    assert entries["broken"]["signals"]["location"] is None
    assert "inspect 失敗" in entries["broken"]["reason"]

    # plain CSV (no DataStore) is downloaded and inspected; address-only -> geocode
    assert entries["plain-csv"]["status"] == "accepted"
    assert entries["plain-csv"]["locationSource"] == "geocode"
    assert entries["plain-csv"]["inspection"]["coordFillRate"] == 0.0

    assert entries["pdf"]["status"] == "rejected"
    assert entries["pdf"]["resourceUrl"] is None
    assert entries["trend"]["status"] == "rejected"
    assert entries["trend"]["inspection"] is None  # excluded: no API call


def test_real_definitions_file():
    defs = load_definitions(REPO_ROOT / "pipeline" / "config" / "feature_definitions.yaml")
    assert defs["park"].enabled
    assert set(defs) <= set(FEATURES)
    assert all(d.keywords for d in defs.values())
    # global excludes are merged into every feature
    assert all("統計年鑑" in d.exclude_keywords for d in defs.values())
    assert "トイレ" in defs["park"].exclude_keywords
