"""Semantic classification (ADR 0003, spec 0009). Rule-based logic lives in discover/evaluate.py
and ingest.py; a SemanticClassifier (Jev) only decides what the rules leave undecided."""

import os
from pathlib import Path

from .base import DatasetDescriptor, FacilityDescriptor, Judgement, SemanticClassifier
from .cache import JudgementCache
from .jev import JevClassifier, JevError, urllib_post

__all__ = [
    "DatasetDescriptor",
    "FacilityDescriptor",
    "Judgement",
    "SemanticClassifier",
    "JevClassifier",
    "JevError",
    "load_classifier",
]


def load_classifier(kind: str, cache_path: Path, features: list[str]) -> JevClassifier | None:
    """Jev when configured and TYPESAFE_API_KEY is set; otherwise None (rules only)."""
    if kind != "jev":
        return None
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    return JevClassifier(urllib_post(key), JudgementCache(cache_path), features)
