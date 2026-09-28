from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fixture_path() -> Path:
    return REPO_ROOT / "data" / "fixtures" / "stations.raw.json"
