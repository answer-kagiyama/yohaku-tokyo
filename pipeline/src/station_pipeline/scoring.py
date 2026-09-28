"""Deterministic scoring (docs/scoring.md). No AI is involved here (ADR 0004)."""

from collections.abc import Mapping, Sequence
from typing import Any

from .config import FEATURES, MIN_COMPARABLE_VALUES, MIN_COVERAGE, WEIGHTS

Number = int | float


def percentile_ranks(values: Sequence[Number | None], min_values: int = 1) -> list[float | None]:
    """Percentile rank 0-100 using average ranks for ties. None stays None (missing != 0).
    With fewer than `min_values` valid values nothing is ranked (all None)."""
    present = sorted((v, i) for i, v in enumerate(values) if v is not None)
    result: list[float | None] = [None] * len(values)
    n = len(present)
    if n == 0 or n < min_values:
        return result
    if n == 1:
        result[present[0][1]] = 50.0
        return result

    pos = 0
    while pos < n:
        end = pos
        while end + 1 < n and present[end + 1][0] == present[pos][0]:
            end += 1
        avg_rank = (pos + end) / 2 + 1  # 1-based average rank
        pct = round((avg_rank - 1) / (n - 1) * 100, 1)
        for k in range(pos, end + 1):
            result[present[k][1]] = pct
        pos = end + 1
    return result


def low_score(percentile: float | None) -> float | None:
    return None if percentile is None else round(100 - percentile, 1)


def yohaku_score(
    lows: Mapping[str, float | None], weights: Mapping[str, float] = WEIGHTS
) -> tuple[float | None, float]:
    """Weighted mean of available low scores. Returns (score, coverage)."""
    total = sum(weights.values())
    available = {k: w for k, w in weights.items() if lows.get(k) is not None}
    covered = sum(available.values())
    coverage = round(covered / total, 3)
    if coverage < MIN_COVERAGE:
        return None, coverage
    score = sum(lows[k] * w for k, w in available.items()) / covered  # type: ignore[operator]
    return round(score, 1), coverage


def effective_weights(
    lows: Mapping[str, float | None], weights: Mapping[str, float] = WEIGHTS
) -> dict[str, float | None]:
    """Weights after redistributing those of unavailable features (ADR 0009)."""
    covered = sum(w for k, w in weights.items() if lows.get(k) is not None)
    return {
        k: (round(w / covered, 4) if lows.get(k) is not None and covered else None)
        for k, w in weights.items()
    }


def _lows(raws: Sequence[Mapping[str, Any]]) -> list[tuple[dict, dict]]:
    columns = {
        f: percentile_ranks([r.get(f) for r in raws], MIN_COMPARABLE_VALUES) for f in FEATURES
    }
    out = []
    for i in range(len(raws)):
        normalized = {f: columns[f][i] for f in FEATURES}
        out.append((normalized, {f"{f}Low": low_score(normalized[f]) for f in FEATURES}))
    return out


def compute_scores(raws: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Compute normalized percentiles and scores for every station, in input order."""
    results = []
    for normalized, lows in _lows(raws):
        score, coverage = yohaku_score(lows)
        results.append(
            {
                "normalized": normalized,
                "scores": {"yohaku": score, **lows, "coverage": coverage},
                "effectiveWeights": effective_weights(lows),
            }
        )
    return results


def competition_ranks(scores: Sequence[float | None]) -> list[int | None]:
    """Descending (bigger YOHAKU = rank 1). Ties share a rank (1, 2, 2, 4). None -> None."""
    present = [s for s in scores if s is not None]
    return [None if s is None else 1 + sum(1 for o in present if o > s) for s in scores]


SENSITIVITY_FACTORS = (0.5, 1.5)


def rank_ranges(raws: Sequence[Mapping[str, Any]]) -> list[tuple[int, int] | None]:
    """Min/max rank of each station when each weight alone is scaled ×0.5 / ×1.5 (spec 0006)."""
    lows = [low for _, low in _lows(raws)]
    variants = [dict(WEIGHTS)] + [
        {**WEIGHTS, key: WEIGHTS[key] * f} for key in WEIGHTS for f in SENSITIVITY_FACTORS
    ]
    seen: list[list[int]] = [[] for _ in raws]
    for weights in variants:
        ranks = competition_ranks([yohaku_score(low, weights)[0] for low in lows])
        for i, r in enumerate(ranks):
            if r is not None:
                seen[i].append(r)
    return [(min(r), max(r)) if r else None for r in seen]
