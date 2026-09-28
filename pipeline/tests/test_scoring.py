import pytest

from station_pipeline.config import FEATURES, WEIGHTS
from station_pipeline.scoring import (
    compute_scores,
    low_score,
    percentile_ranks,
    yohaku_score,
)


class TestPercentileRanks:
    def test_ascending_values_span_0_to_100(self):
        assert percentile_ranks([10, 20, 30]) == [0.0, 50.0, 100.0]

    def test_order_is_preserved(self):
        assert percentile_ranks([30, 10, 20]) == [100.0, 0.0, 50.0]

    def test_ties_get_average_rank(self):
        # ranks: 1, 2.5, 2.5, 4 -> (r-1)/3*100
        assert percentile_ranks([1, 5, 5, 9]) == [0.0, 50.0, 50.0, 100.0]

    def test_single_value_is_50(self):
        assert percentile_ranks([42]) == [50.0]

    def test_none_is_excluded_and_stays_none(self):
        assert percentile_ranks([10, None, 30]) == [0.0, None, 100.0]

    def test_zero_is_a_value_not_missing(self):
        assert percentile_ranks([0, None, 5]) == [0.0, None, 100.0]

    def test_all_none(self):
        assert percentile_ranks([None, None]) == [None, None]

    def test_rounded_to_one_decimal(self):
        assert percentile_ranks([1, 2, 3, 4]) == [0.0, 33.3, 66.7, 100.0]

    def test_empty(self):
        assert percentile_ranks([]) == []

    def test_too_few_values_are_not_ranked(self):
        # tourism known for 1 of 5 stations: a rank of 50 would be meaningless
        assert percentile_ranks([8, None, None, None, None], min_values=3) == [None] * 5
        assert percentile_ranks([1, 2, None], min_values=3) == [None] * 3
        assert percentile_ranks([1, 2, 3], min_values=3) == [0.0, 50.0, 100.0]


class TestLowScore:
    def test_inverts_percentile(self):
        assert low_score(25.0) == 75.0

    def test_none_passthrough(self):
        assert low_score(None) is None


class TestYohakuScore:
    def test_weights_sum_to_one(self):
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)
        assert set(WEIGHTS) == {f"{f}Low" for f in FEATURES}

    def test_weighted_average(self):
        lows = {f"{f}Low": 100.0 for f in FEATURES}
        lows["tourismLow"] = 0.0  # weight 0.25
        score, coverage = yohaku_score(lows)
        assert score == 75.0
        assert coverage == 1.0

    def test_missing_feature_is_renormalized(self):
        lows = {f"{f}Low": 50.0 for f in FEATURES}
        lows["libraryLow"] = None  # weight 0.10
        score, coverage = yohaku_score(lows)
        assert score == 50.0
        assert coverage == 0.9

    def test_low_coverage_yields_none(self):
        lows = {f"{f}Low": None for f in FEATURES}
        lows["tourismLow"] = 80.0  # 0.25 only
        lows["cultureLow"] = 80.0  # +0.20 = 0.45 < 0.5
        score, coverage = yohaku_score(lows)
        assert score is None
        assert coverage == 0.45


class TestComputeScores:
    def test_scores_all_stations(self):
        raws = [{f: 1 for f in FEATURES}, {f: 2 for f in FEATURES}, {f: 3 for f in FEATURES}]
        result = compute_scores(raws)
        assert result[0]["normalized"]["tourism"] == 0.0
        assert result[0]["scores"]["yohaku"] == 100.0
        assert result[2]["scores"]["yohaku"] == 0.0
        assert result[2]["scores"]["coverage"] == 1.0

    def test_feature_known_for_too_few_stations_is_dropped_for_everyone(self):
        raws = [{f: i for f in FEATURES} for i in range(1, 5)]
        for r in raws[1:]:
            r["tourism"] = None
        result = compute_scores(raws)
        assert all(r["normalized"]["tourism"] is None for r in result)
        assert all(r["scores"]["coverage"] == 0.75 for r in result)

    def test_missing_raw_key_is_treated_as_missing(self):
        raws = [{"tourism": 1}, {"tourism": 2}, {"tourism": 3}]
        result = compute_scores(raws)
        assert result[0]["normalized"]["culture"] is None
        assert result[0]["scores"]["cultureLow"] is None


from station_pipeline.scoring import competition_ranks, effective_weights, rank_ranges  # noqa: E402


class TestEffectiveWeights:
    def test_sum_to_one_over_available(self):
        lows = {f"{f}Low": 50.0 for f in FEATURES}
        lows["tourismLow"] = None
        ew = effective_weights(lows)
        assert ew["tourismLow"] is None
        assert sum(v for v in ew.values() if v is not None) == pytest.approx(1.0, abs=1e-3)
        assert ew["cultureLow"] == pytest.approx(0.2 / 0.75, abs=1e-3)

    def test_contributions_add_up_to_score(self):
        lows = {
            "tourismLow": None,
            "cultureLow": 10.0,
            "publicFacilityLow": 90.0,
            "parkLow": 40.0,
            "libraryLow": 70.0,
            "stationUsageLow": 0.0,
        }
        score, _ = yohaku_score(lows)
        ew = effective_weights(lows)
        total = sum(ew[k] * v for k, v in lows.items() if v is not None)
        assert total == pytest.approx(score, abs=0.1)


class TestCompetitionRanks:
    def test_descending_with_ties_and_none(self):
        assert competition_ranks([50.0, 80.0, 50.0, None, 10.0]) == [2, 1, 2, None, 4]

    def test_empty(self):
        assert competition_ranks([]) == []


class TestRankRanges:
    def test_includes_base_rank_and_is_deterministic(self):
        raws = [
            {
                "tourism": None,
                "culture": 2,
                "publicFacility": 0,
                "park": 3,
                "library": 0,
                "stationUsage": 62984,
            },
            {
                "tourism": None,
                "culture": 2,
                "publicFacility": 1,
                "park": 5,
                "library": 2,
                "stationUsage": 119055,
            },
            {
                "tourism": None,
                "culture": 2,
                "publicFacility": 2,
                "park": 7,
                "library": 1,
                "stationUsage": 80140,
            },
            {
                "tourism": 8,
                "culture": 4,
                "publicFacility": 2,
                "park": 1,
                "library": 1,
                "stationUsage": 263129,
            },
            {
                "tourism": None,
                "culture": 1,
                "publicFacility": 6,
                "park": 6,
                "library": 2,
                "stationUsage": 338658,
            },
        ]
        base = competition_ranks([r["scores"]["yohaku"] for r in compute_scores(raws)])
        ranges = rank_ranges(raws)
        assert ranges == rank_ranges(raws)
        for rank, (lo, hi) in zip(base, ranges, strict=True):
            assert lo <= rank <= hi

    def test_clear_winner_is_stable(self):
        raws = [{f: 1 for f in FEATURES}, {f: 5 for f in FEATURES}, {f: 9 for f in FEATURES}]
        assert rank_ranges(raws) == [(1, 1), (2, 2), (3, 3)]

    def test_station_without_score(self):
        raws = [{f: i for f in FEATURES} for i in range(1, 4)] + [{f: None for f in FEATURES}]
        assert rank_ranges(raws)[-1] is None
