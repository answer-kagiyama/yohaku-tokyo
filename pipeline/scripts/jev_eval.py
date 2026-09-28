"""Jev (TypeSafe AI) evaluation spike — spec 0009 §3.

Not part of the pipeline and not run in tests: it calls the real API (TYPESAFE_API_KEY).
Usage: cd pipeline && uv run python scripts/jev_eval.py [--repeats 3]
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from station_pipeline.discover.definitions import load_definitions
from station_pipeline.ingest import is_excluded_name, matches_feature

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "pipeline" / "tests" / "fixtures" / "jev_eval"
OUT = ROOT / "data" / "interim" / "jev-eval"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
FEATURES = ["park", "culture", "publicFacility", "tourism", "library"]

CRITERIA = {
    "ja": {
        "park": "公園・児童遊園・緑地・遊び場",
        "culture": "文化財（建造物・史跡・天然記念物など）や博物館・資料館・美術館などの文化施設",
        "publicFacility": "区民館・出張所・地域センター・会館・ホールなど、住民が集まる公共の集会・交流施設",
        "tourism": "観光施設・名所・観光スポット",
        "library": "図書館",
        "none": "上のどれでもない（学校・住宅・倉庫・トイレ・事務所・スポーツ施設・福祉施設・統計・イベントなど）",
    },
    "en": {
        "park": "A park, children's playground or green space",
        "culture": "A cultural property (building, historic site, natural monument) or a museum / archive / art museum",
        "publicFacility": "A community hall or civic center where residents gather (区民館, 出張所, 会館, ホール)",
        "tourism": "A tourist attraction, sightseeing spot or famous place",
        "library": "A library",
        "none": "None of the above (school, housing, storage, toilet, office, sports, welfare, statistics, events, etc.)",
    },
}
QUESTIONS = {
    "facility": {
        "ja": (
            "この施設は次のどの種類として数えるべきか",
            "一般の人が目的地として訪れることができる、実在の場所・施設である",
        ),
        "en": (
            "Which kind of place should this facility be counted as",
            "This is a real place that members of the public can visit as a destination",
        ),
    },
    "dataset": {
        "ja": (
            "このデータセットは、次のどの種類の施設を 1 行ずつ並べた一覧か",
            "このデータセットは、人が訪れる場所そのものを 1 行ずつ並べた一覧である",
        ),
        "en": (
            "Which kind of places does this dataset list, one place per row",
            "This dataset is a list of places that people visit, one place per row",
        ),
    },
}


def load(name):
    return [
        json.loads(line)
        for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines()
        if line
    ]


def state_for(kind, item):
    if kind == "facility":
        return f"施設名: {item['name']}\n種別: {item['categories'] or '（なし）'}\n出典の一覧: {item['source']}"
    cols = ", ".join(item["columns"]) if item["columns"] else "（不明）"
    return f"データセット名: {item['name']}\n提供組織: {item['organization']}\n列: {cols}"


def request(kind, item, lang, key):
    choice_q, noul_q = QUESTIONS[kind][lang]
    body = {
        "model": "jev-latest",
        "state": state_for(kind, item),
        "questions": {
            "category": {"type": "choice", "instructions": choice_q, "criteria": CRITERIA[lang]},
            "destination": {"type": "noul", "instructions": noul_q},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(5):
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            data["_latency"] = time.monotonic() - t0
            return data
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 529):
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("rate limited")


def rule_facility(item, defs):
    """Current rule-based answer: the first feature whose filters would count the facility."""
    f = {"name": item["name"], "categories": [item["categories"]] if item["categories"] else []}
    for key in FEATURES:
        d = defs[key]
        if is_excluded_name(f["name"], d.exclude_facility_names):
            continue
        if any(m in f["name"] for m in d.exclude_name_markers):
            continue
        if any(w in c for c in f["categories"] for w in d.exclude_categories):
            continue
        if d.include_name_keywords and not any(w in f["name"] for w in d.include_name_keywords):
            continue
        if matches_feature(f, d.keywords, d.include_name_keywords):
            return key
    return "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise SystemExit("TYPESAFE_API_KEY is not set (.env)")
    defs = load_definitions(ROOT / "pipeline" / "config" / "feature_definitions.yaml")
    sets = {"facility": load("facilities.jsonl"), "dataset": load("datasets.jsonl")}

    jobs = []
    for kind, items in sets.items():
        for i in range(len(items)):
            for r in range(args.repeats):
                jobs.append((kind, i, "ja", r))
            jobs.append((kind, i, "en", 0))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda j: (j, request(j[0], sets[j[0]][j[1]], j[2], key)), jobs))

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"raw-{stamp}.json").write_text(
        json.dumps([{"job": j, "response": r} for j, r in results], ensure_ascii=False, indent=1)
    )

    by = {}
    for (kind, i, lang, _rep), resp in results:
        by.setdefault((kind, i, lang), []).append(resp)

    summary = {"generatedAt": stamp, "model": results[0][1]["model"], "sets": {}}
    for kind, items in sets.items():
        rows = []
        for i, item in enumerate(items):
            ja = by[(kind, i, "ja")]
            en = by[(kind, i, "en")][0]
            pred = [r["answers"]["category"]["choice"] for r in ja]
            rule = rule_facility(item, defs) if kind == "facility" else item["rule"]
            rows.append(
                {
                    "name": item["name"],
                    "label": item["label"],
                    "ambiguous": item.get("ambiguous", False),
                    "jev": pred[0],
                    "jevConfidence": ja[0]["answers"]["category"]["confidence"],
                    "jevStable": len(set(pred)) == 1,
                    "jevEn": en["answers"]["category"]["choice"],
                    "destination": ja[0]["answers"]["destination"]["noul"],
                    "destinationLabel": item.get("destination"),
                    "rule": rule,
                }
            )
        scored = [r for r in rows if not r["ambiguous"]]
        n = len(scored)

        def acc(field, rs=scored):
            return round(sum(r[field] == r["label"] for r in rs) / max(len(rs), 1), 3)

        gates = {}
        for t in (0.5, 0.6, 0.7, 0.8, 0.9):
            kept = [r for r in scored if r["jevConfidence"] >= t]
            gates[str(t)] = {"coverage": round(len(kept) / n, 3), "accuracy": acc("jev", kept)}
        dest = [r for r in scored if r["destinationLabel"] is not None]
        summary["sets"][kind] = {
            "items": len(rows),
            "scored": n,
            "accuracy": {"jevJa": acc("jev"), "jevEn": acc("jevEn"), "rule": acc("rule")},
            "stableRate": round(sum(r["jevStable"] for r in rows) / len(rows), 3),
            "confidenceGates": gates,
            "destinationAccuracy@0.5": round(
                sum((r["destination"] >= 0.5) == r["destinationLabel"] for r in dest)
                / max(len(dest), 1),
                3,
            )
            if dest
            else None,
            "confusionJa": Counter(
                f"{r['label']}->{r['jev']}" for r in scored if r["jev"] != r["label"]
            ).most_common(),
            "ruleMistakesFixedByJev": [
                r["name"] for r in scored if r["rule"] != r["label"] and r["jev"] == r["label"]
            ],
            "jevMistakesWhereRuleRight": [
                r["name"] for r in scored if r["jev"] != r["label"] and r["rule"] == r["label"]
            ],
            "rows": rows,
        }
    tokens = sum(r["usage"]["input_tokens"] for _, r in results)
    summary["calls"] = len(results)
    summary["inputTokens"] = tokens
    summary["costUsd"] = round(tokens / 1e6 * 0.042, 4)
    summary["latencyP50"] = round(sorted(r["_latency"] for _, r in results)[len(results) // 2], 3)
    (OUT / f"summary-{stamp}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    for kind, s in summary["sets"].items():
        print(f"== {kind}: {s['scored']} scored / {s['items']}")
        print(
            "   accuracy",
            s["accuracy"],
            "stable",
            s["stableRate"],
            "dest@0.5",
            s["destinationAccuracy@0.5"],
        )
        print("   gates", s["confidenceGates"])
        print("   jev errors", s["confusionJa"])
        print("   rule mistakes fixed by jev", s["ruleMistakesFixedByJev"])
        print("   jev mistakes where rule right", s["jevMistakesWhereRuleRight"])
    print(
        "calls",
        summary["calls"],
        "tokens",
        tokens,
        "cost $",
        summary["costUsd"],
        "p50",
        summary["latencyP50"],
    )
    print("wrote", OUT / f"summary-{stamp}.json")


if __name__ == "__main__":
    main()
