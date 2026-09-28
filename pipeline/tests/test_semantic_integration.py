from datetime import UTC, datetime

from station_pipeline.classify import JevError, Judgement, load_classifier
from station_pipeline.discover.run import apply_semantic
from station_pipeline.http import HttpClient
from station_pipeline.ingest import ingest_feature

NOW = datetime(2026, 9, 28, tzinfo=UTC)


class FakeClassifier:
    name = "jev"

    def __init__(self, dataset=None, facility=None, fail=False):
        self.dataset = dataset
        self.facility = facility or (lambda f: Judgement("none", 0.9, "jev", "jev-1.13.0"))
        self.fail = fail
        self.seen = []

    def judge_dataset(self, d):
        self.seen.append(d)
        if self.fail:
            raise JevError("Jev HTTP 529")
        return self.dataset

    def judge_facilities(self, fs):
        if self.fail:
            raise JevError("Jev HTTP 529")
        return [self.facility(f) for f in fs]


def review_entry(location=1.0):
    return {
        "feature": "park",
        "status": "review",
        "autoStatus": "review",
        "reason": "タイトルに「公園」を含む（一覧を示す語なし）",
        "signals": {"location": location},
        "inspection": {"fields": ["名称", "所在地", "緯度", "経度"]},
    }


PKG = {
    "name": "p",
    "title": "公園・緑地",
    "organization": {"title": "杉並区"},
    "resources": [{"name": "公園・緑地"}],
}


def judge(category, conf, list_score):
    return Judgement(category, conf, "jev", "jev-1.13.0", list_score)


def run(entry, j, **kw):
    c = FakeClassifier(dataset=j, **kw)
    apply_semantic(entry, PKG, c, 0.7, 0.45, 0.8)
    return entry, c


def test_review_accepted_when_confident_list_and_location_ok():
    e, c = run(review_entry(), judge("park", 1.0, 0.63))
    assert (e["status"], e["autoStatus"]) == ("accepted", "accepted")
    assert e["semantic"]["category"] == "park" and e["semantic"]["listScore"] == 0.63
    assert "jev: park" in e["reason"] and "採用" in e["reason"]
    assert c.seen[0].columns == ["名称", "所在地", "緯度", "経度"]
    assert c.seen[0].organization == "杉並区"


def test_statistics_table_is_rejected_by_list_score():
    # observed: 「公園の数と面積」 -> jev says park with high confidence but list score is low
    e, _ = run(review_entry(), judge("park", 1.0, 0.2))
    assert e["status"] == "rejected"


def test_other_category_is_rejected():
    e, _ = run(review_entry(), judge("library", 0.97, 0.8))
    assert e["status"] == "rejected"


def test_low_confidence_stays_review():
    e, _ = run(review_entry(), judge("park", 0.55, 0.8))
    assert e["status"] == "review" and "判断が分かれる" in e["reason"]


def test_middle_list_score_stays_review():
    # observed: 江戸川区 文化財一覧 -> culture 1.00, list 0.38 (objects mixed with places)
    e, _ = run(review_entry(), judge("park", 1.0, 0.38))
    assert e["status"] == "review"


def test_mixed_facility_list_is_accepted_with_row_filter():
    # observed: 葛飾区 区内施設一覧 / 目黒区 公共施設 — parks mixed with other facilities
    e, _ = run(review_entry(), judge("mixed", 0.9, 0.9))
    assert e["status"] == "accepted" and e["rowFilter"] is True


def test_location_insufficient_stays_review():
    e, _ = run(review_entry(location=0.0), judge("park", 1.0, 0.8))
    assert e["status"] == "review" and "位置情報が不足" in e["reason"]


def test_classifier_failure_keeps_rule_result():
    e, _ = run(review_entry(), None, fail=True)
    assert e["status"] == "review" and "jev 失敗" in e["reason"]
    assert "semantic" not in e


def test_no_api_key_means_rules_only(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert load_classifier("jev", tmp_path / "c.json", ["park"]) is None
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    assert load_classifier("none", tmp_path / "c.json", ["park"]) is None
    assert load_classifier("jev", tmp_path / "c.json", ["park"]).name == "jev"


def entry(url):
    return {
        "datasetId": "m",
        "name": "港区の公共施設情報",
        "organization": "港区",
        "feature": "park",
        "sourceUrl": "https://c/m",
        "resourceUrl": url,
        "format": "csv",
        "status": "accepted",
        "rowFilter": True,
    }


def client(files):
    return HttpClient(lambda url: files[url], sleep=lambda s: None, retries=1)


class NoGeocoder:
    def geocode(self, address, municipality=None):
        return None


CSV = (
    "名称,種別,緯度,経度\n"
    "芝公園,公園・児童遊園・緑地,35.655,139.749\n"
    "みなと科学館,郷土歴史館,35.64,139.74\n"
    "旧芝公園管理棟,公園・児童遊園・緑地,35.655,139.749\n"
)


def test_ingest_uses_classifier_for_mixed_lists_after_hard_rules(tmp_path):
    fac = FakeClassifier(
        facility=lambda f: Judgement(
            "park" if "公園" in f.name else "culture", 0.95, "jev", "jev-1.13.0"
        )
    )
    facilities, report = ingest_feature(
        {"datasets": [entry("https://f/m.csv")]},
        "park",
        client({"https://f/m.csv": CSV.encode()}),
        NoGeocoder(),
        tmp_path,
        NOW,
        exclude_markers=("旧",),
        classifier=fac,
    )
    # 旧… removed by the hard rule before the classifier; みなと科学館 is culture -> not a park
    assert [f["name"] for f in facilities] == ["芝公園"]
    assert facilities[0]["semantic"]["classifier"] == "jev"
    assert report["datasets"][0]["classifiedBy"] == "jev"
    assert report["datasets"][0]["excluded"] == 2


def test_ingest_falls_back_to_rules_when_classifier_fails(tmp_path):
    facilities, report = ingest_feature(
        {"datasets": [entry("https://f/m.csv")]},
        "park",
        client({"https://f/m.csv": CSV.encode()}),
        NoGeocoder(),
        tmp_path,
        NOW,
        feature_keywords=("公園",),
        classifier=FakeClassifier(fail=True),
    )
    assert report["datasets"][0]["classifiedBy"] == "rule"
    assert sorted(f["name"] for f in facilities) == ["旧芝公園管理棟", "芝公園"]


def test_mixed_list_without_matching_rows_does_not_cover_the_municipality(tmp_path):
    from station_pipeline.aggregate.coverage import municipality_coverage

    csv = "名称,緯度,経度\n文京シビックホール,35.70,139.75\nアカデミー湯島,35.70,139.76\n"
    e = {**entry("https://f/b.csv"), "organization": "文京区", "feature": "culture"}
    fac = FakeClassifier(facility=lambda f: Judgement("publicFacility", 0.9, "jev", "m"))
    facilities, report = ingest_feature(
        {"datasets": [e]},
        "culture",
        client({"https://f/b.csv": csv.encode()}),
        NoGeocoder(),
        tmp_path,
        NOW,
        classifier=fac,
    )
    assert facilities == []
    assert report["datasets"][0]["status"] == "no-matching-rows"
    assert "文京区" not in municipality_coverage(report)  # -> uncovered, i.e. missing, not 0
