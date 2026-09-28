"""Shared constants. Must stay in sync with docs/scoring.md and apps/web/src/domain/features.ts."""

DEFAULT_RADIUS_METERS = 500

SCORING_VERSION = "0.2.0"
SCORING_METHOD = "percentile-rank"

# Order matters: it is the tie-break order for the dominant feature.
FEATURES: tuple[str, ...] = (
    "tourism",
    "culture",
    "publicFacility",
    "park",
    "library",
    "stationUsage",
)

WEIGHTS: dict[str, float] = {
    "tourismLow": 0.25,
    "cultureLow": 0.20,
    "publicFacilityLow": 0.15,
    "parkLow": 0.10,
    "libraryLow": 0.10,
    "stationUsageLow": 0.20,
}

# Below this share of available weight, the YOHAKU SCORE is not computed.
MIN_COVERAGE = 0.5

# A feature with fewer valid values than this cannot be ranked meaningfully: every station gets
# null for it (e.g. tourism known for 1 of 5 stations). docs/scoring.md §2.
MIN_COMPARABLE_VALUES = 3
