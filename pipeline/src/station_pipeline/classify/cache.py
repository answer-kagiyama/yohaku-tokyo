"""Judgement cache: same input -> same stored answer, no API call (reproducibility + cost).

Stored under data/processed/semantic/ and committed, so other environments reuse it."""

import hashlib
import json
import threading
from pathlib import Path
from typing import Any


def cache_key(payload: dict[str, Any]) -> str:
    """Key on what is asked (state + questions), not on the model alias."""
    stable = json.dumps(
        {"state": payload["state"], "questions": payload["questions"]},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(stable.encode()).hexdigest()


class JudgementCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        if path.exists():
            self._entries = json.loads(path.read_text(encoding="utf-8")).get("entries", {})
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            hit = self._entries.get(key)
            if hit is None:
                self.misses += 1
            else:
                self.hits += 1
            return hit

    def put(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            body = {"entries": dict(sorted(self._entries.items()))}
        self.path.write_text(
            json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
