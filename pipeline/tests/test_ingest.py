from datetime import UTC, datetime

from station_pipeline.geo.geocode import GeocodeResult
from station_pipeline.http import HttpClient
from station_pipeline.ingest import ingest_feature
from station_pipeline.normalize.facilities import normalize_rows

NOW = datetime(2026, 9, 27, tzinfo=UTC)


def entry(dataset_id, url, status="accepted", fmt="csv", org="千代田区"):
    return {
        "datasetId": dataset_id,
        "name": dataset_id,
        "organization": org,
        "feature": "park",
        "sourceUrl": f"https://catalog/dataset/{dataset_id}",
        "resourceUrl": url,
        "format": fmt,
        "status": status,
    }


class FakeGeocoder:
    def __init__(self, known):
        self.known = known
        self.queries = []

    def geocode(self, address, municipality=None):
        self.queries.append((address, municipality))
        hit = self.known.get(address)
        if hit is None:
            return None
        return GeocodeResult(
            lat=hit[0], lng=hit[1], matched=address, precision="exact", provider="fake"
        )


def client(files):
    def transport(url):
        body = files[url]
        if isinstance(body, Exception):
            raise body
        return body

    return HttpClient(transport, sleep=lambda s: None, retries=1)


def test_normalize_rows_keeps_missing_coordinates_as_none():
    rows = normalize_rows(
        ["名称", "所在地", "緯度", "経度"],
        [
            {"名称": "A公園", "所在地": "x", "緯度": "35.7", "経度": "139.77"},
            {"名称": "B公園", "所在地": "y", "緯度": "", "経度": ""},
            {"名称": "", "所在地": "z", "緯度": "35.7", "経度": "139.7"},  # no name: skipped
            {"名称": "C公園", "所在地": "", "緯度": "0", "経度": "0"},  # invalid: not a location
        ],
        entry("d", "u"),
    )
    assert [r["name"] for r in rows] == ["A公園", "B公園", "C公園"]
    assert rows[0]["coordSource"] == "source"
    assert rows[1]["lat"] is None and rows[1]["coordSource"] is None
    assert rows[2]["lat"] is None
    assert rows[0]["id"] == "d:1"


def test_ingest_fetch_geocode_and_report(tmp_path):
    source = "名称,所在地_連結表記,緯度,経度\nA公園,東京都台東区上野1-1,35.71,139.77\n"
    address_only = (
        "名称,所在地_連結表記,緯度,経度\n"
        "宮本公園,東京都千代田区外神田二丁目16番９号,,\n"
        "謎公園,東京都千代田区不明,,\n"
    )
    manifest = {
        "datasets": [
            entry("taito", "https://f/taito.csv", org="台東区"),
            entry("chiyoda", "https://f/chiyoda.csv"),
            entry("broken", "https://f/broken.csv"),
            entry("noname", "https://f/noname.csv"),
            entry("xlsx", "https://f/x.xlsx", fmt="xlsx"),
            entry("skipped", "https://f/s.csv", status="review"),
        ]
    }
    files = {
        "https://f/taito.csv": source.encode("utf-8-sig"),
        "https://f/chiyoda.csv": address_only.encode("cp932"),
        "https://f/broken.csv": OSError("down"),
        "https://f/noname.csv": "施設,緯度\na,35\n".encode(),
    }
    geocoder = FakeGeocoder({"東京都千代田区外神田二丁目16番９号": (35.702, 139.767)})
    facilities, report = ingest_feature(manifest, "park", client(files), geocoder, tmp_path, NOW)

    by_name = {f["name"]: f for f in facilities}
    assert by_name["A公園"]["coordSource"] == "source"
    assert by_name["宮本公園"]["coordSource"] == "geocode"
    assert by_name["宮本公園"]["geocode"]["provider"] == "fake"
    assert by_name["謎公園"]["lat"] is None  # unlocated, not dropped
    # only rows without source coordinates are geocoded
    assert [q[0] for q in geocoder.queries] == [
        "東京都千代田区外神田二丁目16番９号",
        "東京都千代田区不明",
    ]

    ds = {d["datasetId"]: d for d in report["datasets"]}
    assert "skipped" not in ds  # only accepted datasets are fetched
    assert ds["taito"]["status"] == "ok" and ds["taito"]["encoding"] == "utf-8-sig"
    assert ds["chiyoda"]["encoding"] == "cp932"
    assert (ds["chiyoda"]["geocoded"], ds["chiyoda"]["unlocated"]) == (1, 1)
    assert ds["chiyoda"]["status"] == "ok"  # 50% located is not below the threshold
    assert ds["broken"]["status"] == "failed"
    assert ds["noname"]["status"] == "failed" and "name column" in ds["noname"]["error"]
    assert ds["xlsx"]["status"] == "failed" and "unsupported" in ds["xlsx"]["error"]
    assert report["totals"] == {
        "datasets": 5,
        "failed": 3,
        "degraded": 0,
        "outOfScope": 0,
        "rows": 3,
        "mergedDuplicates": 0,
        "facilities": 3,
        "located": 2,
        "unlocated": 1,
        "unlocatedByReason": {"geocode-not-found": 1},
    }

    # raw file + provenance metadata
    raw = tmp_path / "park" / "chiyoda.csv"
    assert raw.exists()
    meta = (tmp_path / "park" / "chiyoda.csv.meta.json").read_text()
    assert '"resourceUrl": "https://f/chiyoda.csv"' in meta
    assert '"sha256"' in meta and '"retrievedAt": "2026-09-27T00:00:00Z"' in meta


def test_degraded_when_most_rows_unlocated(tmp_path):
    csv = "名称,所在地\nA,x\nB,y\nC,z\n"
    manifest = {"datasets": [entry("d", "https://f/d.csv")]}
    _, report = ingest_feature(
        manifest, "park", client({"https://f/d.csv": csv.encode()}), FakeGeocoder({}), tmp_path, NOW
    )
    assert report["datasets"][0]["status"] == "degraded"


def test_geocode_scope_and_unlocated_reasons(tmp_path):
    csv = "名称,所在地\nA,東京都港区芝1\nB,\n"
    manifest = {"datasets": [entry("minato", "https://f/m.csv", org="港区")]}
    geocoder = FakeGeocoder({})
    facilities, report = ingest_feature(
        manifest,
        "park",
        client({"https://f/m.csv": csv.encode()}),
        geocoder,
        tmp_path,
        NOW,
        geocode_scope=frozenset({"千代田区"}),
    )
    assert geocoder.queries == []  # out of scope: no API call
    reasons = {f["name"]: f["unlocatedReason"] for f in facilities}
    assert reasons == {"A": "out-of-geocode-scope", "B": "no-address"}
    assert report["totals"]["unlocatedByReason"] == {"no-address": 1, "out-of-geocode-scope": 1}
    assert report["datasets"][0]["outOfGeocodeScope"] == 1
    # B is in scope (no address needed to be skipped) and unlocated -> degraded
    assert report["datasets"][0]["status"] == "degraded"


def test_dataset_entirely_out_of_scope_is_not_degraded(tmp_path):
    manifest = {"datasets": [entry("minato", "https://f/m.csv", org="港区")]}
    _, report = ingest_feature(
        manifest,
        "park",
        client({"https://f/m.csv": "名称,所在地\nA,東京都港区芝1\n".encode()}),
        FakeGeocoder({}),
        tmp_path,
        NOW,
        geocode_scope=frozenset({"千代田区"}),
    )
    assert report["datasets"][0]["status"] == "out-of-scope"
    assert report["totals"]["outOfScope"] == 1


def test_duplicates_across_datasets_are_merged(tmp_path):
    a = "名称,所在地,緯度,経度\n元町公園,x,35.7050,139.7600\n"
    b = "名称,所在地\n元町公園（もとまち）,東京都文京区本郷1\n"
    manifest = {
        "datasets": [
            entry("a", "https://f/a.csv", org="文京区"),
            entry("b", "https://f/b.csv", org="文京区"),
        ]
    }
    geocoder = FakeGeocoder({"東京都文京区本郷1": (35.7055, 139.7602)})  # ~60m away
    files = {"https://f/a.csv": a.encode(), "https://f/b.csv": b.encode()}
    facilities, report = ingest_feature(manifest, "park", client(files), geocoder, tmp_path, NOW)
    assert len(facilities) == 1
    assert facilities[0]["coordSource"] == "source"  # source coordinates win
    assert facilities[0]["duplicates"] == ["b:1"]
    assert report["totals"]["mergedDuplicates"] == 1


def test_facilities_of_other_features_are_excluded_by_name(tmp_path):
    csv = (
        "名称,緯度,経度\n"
        "神田公園出張所,35.69,139.77\n"
        "千代田図書館,35.69,139.75\n"
        "四番町図書館分室（仮）,35.69,139.74\n"
        "神田公園,35.69,139.77\n"
    )
    manifest = {"datasets": [entry("pub", "https://f/p.csv")]}
    facilities, report = ingest_feature(
        manifest,
        "park",
        client({"https://f/p.csv": csv.encode()}),
        FakeGeocoder({}),
        tmp_path,
        NOW,
        exclude_names=("図書館", "公園"),
    )
    # 神田公園出張所 is named after a district, not a park: kept
    assert [f["name"] for f in facilities] == ["神田公園出張所"]
    assert report["datasets"][0]["excluded"] == 3


def test_non_destinations_and_outside_tokyo(tmp_path):
    csv = (
        "名称,文化財分類,所在地,緯度,経度\n"
        "牛嶋神社,有形文化財（建造物）,,35.71,139.80\n"
        "小林家住宅 ※非公開,有形文化財（建造物）,,,\n"
        "組み紐・紐結び,無形文化財（工芸技術）,,,\n"
        "軽井沢少年自然の家,,長野県北佐久郡軽井沢町長倉1240,,\n"
    )
    manifest = {"datasets": [entry("c", "https://f/c.csv", org="墨田区")]}
    geocoder = FakeGeocoder({})
    facilities, report = ingest_feature(
        manifest,
        "park",  # entry() builds park entries; the filters are feature-agnostic
        client({"https://f/c.csv": csv.encode()}),
        geocoder,
        tmp_path,
        NOW,
        exclude_markers=("非公開",),
        exclude_categories=("無形",),
    )
    assert [f["name"] for f in facilities] == ["牛嶋神社", "軽井沢少年自然の家"]
    assert facilities[1]["unlocatedReason"] == "outside-tokyo"
    assert geocoder.queries == []  # never sent "東京都長野県…" to the geocoder
    d = report["datasets"][0]
    assert (d["excluded"], d["outsideTokyo"], d["unlocated"]) == (2, 1, 0)
    assert d["status"] == "ok"


def test_same_place_counts_once(tmp_path):
    csv = (
        "名称,緯度,経度\n"
        "浅草寺本堂,35.71480,139.79670\n"
        "浅草寺所蔵 絵馬,35.71481,139.79671\n"
        "伝法院,35.71300,139.79500\n"
    )
    manifest = {"datasets": [entry("c", "https://f/c.csv", org="台東区")]}
    facilities, _ = ingest_feature(
        manifest,
        "park",  # entry() builds park entries; the filters are feature-agnostic
        client({"https://f/c.csv": csv.encode()}),
        FakeGeocoder({}),
        tmp_path,
        NOW,
        same_place_m=30,
    )
    assert sorted(f["name"] for f in facilities) == ["伝法院", "浅草寺本堂"]
    assert [f["duplicates"] for f in facilities if f["name"] == "浅草寺本堂"] == [["c:2"]]


def test_include_name_keywords_align_the_concept(tmp_path):
    csv = (
        "名称,緯度,経度\n"
        "和泉橋出張所・区民館,35.698,139.775\n"
        "和泉小学校,35.699,139.776\n"
        "公衆便所（和泉橋際）,35.697,139.774\n"
        "旧万世橋出張所,35.697,139.771\n"
    )
    manifest = {"datasets": [entry("p", "https://f/p.csv")]}
    facilities, report = ingest_feature(
        manifest,
        "park",
        client({"https://f/p.csv": csv.encode()}),
        FakeGeocoder({}),
        tmp_path,
        NOW,
        include_names=("区民館", "出張所"),
        exclude_markers=("便所", "旧"),
    )
    assert [f["name"] for f in facilities] == ["和泉橋出張所・区民館"]
    assert report["datasets"][0]["excluded"] == 3


def test_row_filter_for_mixed_lists(tmp_path):
    csv = (
        "名称,種別,緯度,経度\n"
        "芝公園,公園,35.65,139.75\n"
        "港区役所,庁舎,35.65,139.75\n"
        "みなと図書館,図書館,35.66,139.74\n"
    )
    e = {**entry("m", "https://f/m.csv", org="港区"), "rowFilter": True}
    facilities, report = ingest_feature(
        {"datasets": [e]},
        "park",
        client({"https://f/m.csv": csv.encode()}),
        FakeGeocoder({}),
        tmp_path,
        NOW,
        feature_keywords=("公園", "児童遊園", "緑地"),
    )
    assert [f["name"] for f in facilities] == ["芝公園"]
    assert report["datasets"][0]["excluded"] == 2
