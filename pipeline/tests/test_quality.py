import copy

import pytest

from station_pipeline.quality import DataQualityError, validate_dataset


def _valid():
    return {
        "generatedAt": "2026-09-27T00:00:00Z",
        "radiusMeters": 500,
        "isFixture": True,
        "scoring": {"version": "x", "method": "percentile-rank", "weights": {}},
        "stations": [
            {
                "id": "a",
                "name": "A",
                "lat": 35.7,
                "lng": 139.7,
                "raw": {"tourism": 1},
                "normalized": {"tourism": 50.0},
                "semantic": {},
                "scores": {"yohaku": 50.0, "tourismLow": 50.0, "coverage": 1.0},
                "sources": [{"id": "s", "name": "S", "kind": "fixture"}],
            }
        ],
    }


def test_valid_dataset_passes():
    validate_dataset(_valid())


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d["stations"].append(copy.deepcopy(d["stations"][0])), "duplicate station id"),
        (lambda d: d["stations"][0].update(name=""), "name missing"),
        (lambda d: d["stations"][0].update(lat=95), "invalid coordinates"),
        (lambda d: d["stations"][0].update(lng=None), "invalid coordinates"),
        (lambda d: d["stations"][0]["scores"].update(yohaku=100.5), "score out of range"),
        (lambda d: d["stations"][0]["normalized"].update(tourism=-1), "normalized out of range"),
        (lambda d: d["stations"][0].update(sources=[]), "no sources"),
        (lambda d: d.pop("radiusMeters"), "schema mismatch"),
        (lambda d: d["stations"][0].pop("raw"), "schema mismatch"),
    ],
)
def test_violations_fail(mutate, message):
    data = _valid()
    mutate(data)
    with pytest.raises(DataQualityError, match=message):
        validate_dataset(data)


def test_null_scores_are_allowed():
    data = _valid()
    data["stations"][0]["scores"]["yohaku"] = None
    data["stations"][0]["normalized"]["tourism"] = None
    validate_dataset(data)


def test_accepted_source_without_url_fails():
    data = _valid()
    data["stations"][0]["sources"] = [{"id": "s", "name": "S", "kind": "opendata", "url": None}]
    with pytest.raises(DataQualityError, match="source without url"):
        validate_dataset(data)
