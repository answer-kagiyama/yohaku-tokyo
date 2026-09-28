"""JevClassifier — TypeSafe AI Jev (spec 0009). Questions and criteria are the ones validated in
the Japanese evaluation (spec 0009 §6, pipeline/scripts/jev_eval.py)."""

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .base import DatasetDescriptor, FacilityDescriptor, Judgement
from .cache import JudgementCache, cache_key

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

CRITERIA = {
    "park": "公園・児童遊園・緑地・遊び場",
    "culture": "文化財（建造物・史跡・天然記念物など）や博物館・資料館・美術館などの文化施設",
    "publicFacility": "区民館・出張所・地域センター・会館・ホールなど、住民が集まる公共の集会・交流施設",
    "tourism": "観光施設・名所・観光スポット",
    "library": "図書館",
    "none": "上のどれでもない（学校・住宅・倉庫・トイレ・事務所・スポーツ施設・福祉施設・統計・イベントなど）",
}
MIXED = "公園・図書館・区民館・学校などの複数の種類の施設が混在する施設一覧"
DATASET_CATEGORY = "このデータセットは、次のどの種類の施設を 1 行ずつ並べた一覧か"
DATASET_LIST = "このデータセットは、人が訪れる場所そのものを 1 行ずつ並べた一覧である"
FACILITY_CATEGORY = "この施設は次のどの種類として数えるべきか"

Post = Callable[[dict[str, Any]], dict[str, Any]]


class JevError(RuntimeError):
    pass


def urllib_post(api_key: str, timeout: float = 60.0) -> Post:
    def post(body: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https
            return json.load(resp)

    return post


class JevClassifier:
    name = "jev"

    def __init__(
        self,
        post: Post,
        cache: JudgementCache,
        features: Sequence[str],
        retries: int = 5,
        workers: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._post = post
        self.cache = cache
        self.criteria = {k: CRITERIA[k] for k in features} | {"none": CRITERIA["none"]}
        self._retries = retries
        self._workers = workers
        self._sleep = sleep
        self.calls = 0

    def _ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        key = cache_key(payload)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        for attempt in range(self._retries):
            try:
                self.calls += 1
                resp = self._post(payload)
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 529) and attempt < self._retries - 1:
                    self._sleep(2**attempt)
                    continue
                raise JevError(f"Jev HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt < self._retries - 1:
                    self._sleep(2**attempt)
                    continue
                raise JevError(f"Jev unreachable: {exc}") from exc
        else:  # pragma: no cover - loop always breaks or raises
            raise JevError("Jev: retries exhausted")
        entry = {"model": resp.get("model"), "answers": resp["answers"]}
        self.cache.put(key, entry)
        return entry

    def judge_dataset(self, dataset: DatasetDescriptor) -> Judgement:
        state = "\n".join(
            [
                f"データセット名: {dataset.name}",
                f"提供組織: {dataset.organization or '（不明）'}",
                f"ファイル: {', '.join(dataset.resources) or '（不明）'}",
                f"列: {', '.join(dataset.columns[:15]) or '（不明）'}",
            ]
        )
        entry = self._ask(
            {
                "model": MODEL,
                "state": state,
                "questions": {
                    "category": {
                        "type": "choice",
                        "instructions": DATASET_CATEGORY,
                        # "mixed": a mixed facility list is usable row by row (rowFilter)
                        "criteria": {**self.criteria, "mixed": MIXED},
                    },
                    "list": {"type": "noul", "instructions": DATASET_LIST},
                },
            }
        )
        a = entry["answers"]
        return Judgement(
            category=a["category"]["choice"],
            confidence=a["category"]["confidence"],
            classifier=self.name,
            model=entry.get("model"),
            list_score=a["list"]["noul"],
        )

    def _judge_facility(self, f: FacilityDescriptor) -> Judgement:
        state = "\n".join(
            [
                f"施設名: {f.name}",
                f"種別: {' / '.join(f.categories) or '（なし）'}",
                f"出典の一覧: {f.source}",
            ]
        )
        entry = self._ask(
            {
                "model": MODEL,
                "state": state,
                "questions": {
                    "category": {
                        "type": "choice",
                        "instructions": FACILITY_CATEGORY,
                        "criteria": self.criteria,
                    }
                },
            }
        )
        a = entry["answers"]["category"]
        return Judgement(a["choice"], a["confidence"], self.name, entry.get("model"))

    def judge_facilities(self, facilities: list[FacilityDescriptor]) -> list[Judgement]:
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            return list(pool.map(self._judge_facility, facilities))
