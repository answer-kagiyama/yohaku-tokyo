import json
import urllib.error

import pytest

from station_pipeline.classify.base import DatasetDescriptor, FacilityDescriptor
from station_pipeline.classify.cache import JudgementCache
from station_pipeline.classify.jev import JevClassifier, JevError


def fake_api(answer_for):
    """answer_for(state_text) -> (category, confidence, list_score). Records calls."""
    calls = []

    def post(body: dict) -> dict:
        calls.append(body)
        category, confidence, list_score = answer_for(body["state"])
        answers = {
            "category": {
                "type": "choice",
                "choice": category,
                "confidence": confidence,
                "probabilities": {category: confidence},
            }
        }
        if "list" in body["questions"]:
            answers["list"] = {"type": "noul", "noul": list_score}
        return {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 100}}

    return post, calls


FEATURES = ("park", "culture", "publicFacility", "tourism", "library")


def test_dataset_judgement_and_cache(tmp_path):
    post, calls = fake_api(lambda s: ("park", 0.97, 0.8) if "公園一覧" in s else ("none", 0.9, 0.1))
    cache = JudgementCache(tmp_path / "cache.json")
    jev = JevClassifier(post, cache, FEATURES)
    ds = DatasetDescriptor(
        name="公園一覧", organization="大田区", resources=["公園一覧"], columns=["名称"]
    )
    j = jev.judge_dataset(ds)
    assert (j.category, j.confidence, j.list_score) == ("park", 0.97, 0.8)
    assert j.classifier == "jev" and j.model == "jev-1.13.0"
    assert "公園一覧" in calls[0]["state"] and "大田区" in calls[0]["state"]
    assert set(calls[0]["questions"]["category"]["criteria"]) == set(FEATURES) | {"none", "mixed"}

    # same input -> cache, no API call; cache survives reload
    jev.judge_dataset(ds)
    cache.save()
    again = JevClassifier(post, JudgementCache(tmp_path / "cache.json"), FEATURES)
    again.judge_dataset(ds)
    assert len(calls) == 1


def test_facilities_batch(tmp_path):
    post, calls = fake_api(lambda s: ("park", 0.9, 0) if "公園" in s else ("none", 0.8, 0))
    jev = JevClassifier(post, JudgementCache(tmp_path / "c.json"), FEATURES)
    items = [
        FacilityDescriptor(
            name="芝公園", categories=["公園・児童遊園・緑地"], source="港区の公共施設情報"
        ),
        FacilityDescriptor(name="港区役所", categories=[], source="港区の公共施設情報"),
    ]
    out = jev.judge_facilities(items)
    assert [j.category for j in out] == ["park", "none"]
    assert all("list" not in c["questions"] for c in calls)  # facilities: category only


def test_retries_on_rate_limit_then_fails(tmp_path):
    attempts = {"n": 0}

    def post(body):
        attempts["n"] += 1
        raise urllib.error.HTTPError("u", 429, "Too Many", {}, None)

    jev = JevClassifier(
        post, JudgementCache(tmp_path / "c.json"), FEATURES, retries=3, sleep=lambda s: None
    )
    with pytest.raises(JevError):
        jev.judge_dataset(DatasetDescriptor(name="x", organization="y", resources=[], columns=[]))
    assert attempts["n"] == 3


def test_client_error_is_not_retried(tmp_path):
    attempts = {"n": 0}

    def post(body):
        attempts["n"] += 1
        raise urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)

    jev = JevClassifier(post, JudgementCache(tmp_path / "c.json"), FEATURES, sleep=lambda s: None)
    with pytest.raises(JevError, match="401"):
        jev.judge_dataset(DatasetDescriptor(name="x", organization="y", resources=[], columns=[]))
    assert attempts["n"] == 1


def test_cache_file_is_stable_json(tmp_path):
    post, _ = fake_api(lambda s: ("none", 0.9, 0.1))
    cache = JudgementCache(tmp_path / "c.json")
    JevClassifier(post, cache, FEATURES).judge_dataset(
        DatasetDescriptor(name="統計", organization="都", resources=[], columns=[])
    )
    cache.save()
    data = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
    ((key, entry),) = data["entries"].items()
    assert len(key) == 64 and entry["model"] == "jev-1.13.0" and "answers" in entry
