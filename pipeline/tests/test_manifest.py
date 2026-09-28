import json

import pytest

from station_pipeline.discover.manifest import (
    apply_overrides,
    load_overrides,
    mark_duplicates,
    merge_manifest,
    validate_manifest,
)


def entry(dataset_id, status="accepted", confidence=0.9, feature="park", **kw):
    return {
        "datasetId": dataset_id,
        "name": kw.pop("name", dataset_id),
        "organization": kw.pop("organization", "大田区"),
        "feature": feature,
        "sourceUrl": f"https://catalog/dataset/{dataset_id}",
        "resourceUrl": kw.pop("resourceUrl", f"https://x/{dataset_id}.csv"),
        "status": status,
        "autoStatus": status,
        "confidence": confidence,
        "reason": "r",
        "signals": {"semantic": 1.0},
        "duplicateOf": None,
        **kw,
    }


def test_duplicate_resource_url_is_demoted():
    a = entry("a", confidence=0.9, resourceUrl="https://x/same.csv", name="公園一覧")
    b = entry("b", confidence=0.8, resourceUrl="https://x/same.csv", name="公園一覧 (再掲)")
    out = {e["datasetId"]: e for e in mark_duplicates([b, a])}
    assert out["a"]["status"] == "accepted"
    assert out["b"]["status"] == "review"
    assert out["b"]["autoStatus"] == "review"
    assert out["b"]["duplicateOf"] == "a"


def test_same_title_in_different_orgs_is_not_duplicate():
    a = entry("a", name="都市公園・都立公園一覧", organization="大田区")
    b = entry("b", name="都市公園・都立公園一覧", organization="品川区")
    out = mark_duplicates([a, b])
    assert all(e["duplicateOf"] is None for e in out)


def test_same_title_same_org_is_duplicate():
    a = entry("a", name="公園一覧", confidence=0.9)
    b = entry("b", name="公園 一覧", confidence=0.7)
    out = {e["datasetId"]: e for e in mark_duplicates([a, b])}
    assert out["b"]["duplicateOf"] == "a"


def test_overrides_keep_auto_status(tmp_path):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps({"datasets": {"a": {"status": "rejected", "note": "古い"}}}))
    out = apply_overrides([entry("a"), entry("b")], load_overrides(path))
    by_id = {e["datasetId"]: e for e in out}
    assert by_id["a"]["status"] == "rejected"
    assert by_id["a"]["autoStatus"] == "accepted"
    assert by_id["a"]["review"] == {"status": "rejected", "note": "古い"}
    assert by_id["b"]["review"] is None


def test_invalid_override_status(tmp_path):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps({"datasets": {"a": {"status": "maybe"}}}))
    with pytest.raises(ValueError):
        load_overrides(path)


def test_missing_overrides_file(tmp_path):
    assert load_overrides(tmp_path / "none.json") == {}


def test_merge_keeps_other_features():
    existing = {
        "features": {"culture": {"candidates": 1}},
        "datasets": [entry("c", feature="culture"), entry("old-park")],
    }
    m = merge_manifest(
        existing, "park", {"label": "公園"}, [entry("p")], "2026-09-27T00:00:00Z", "cat"
    )
    ids = sorted(e["datasetId"] for e in m["datasets"])
    assert ids == ["c", "p"]
    assert set(m["features"]) == {"culture", "park"}
    assert m["features"]["park"]["accepted"] == 1


def test_accepted_without_resource_fails():
    with pytest.raises(ValueError, match="without source"):
        validate_manifest({"datasets": [entry("a", resourceUrl=None)]})


def test_feature_scoped_override(tmp_path):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps({"datasets": {"culture/a": {"status": "accepted", "note": "x"}}}))
    park = entry("a", status="rejected", feature="park")
    culture = entry("a", status="rejected", feature="culture")
    out = apply_overrides([park, culture], load_overrides(path))
    assert [e["status"] for e in out] == ["rejected", "accepted"]
