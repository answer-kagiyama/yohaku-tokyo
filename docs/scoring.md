# Scoring — YOHAKU SCORE（MVP 仮仕様 v0.1.0-mvp）

> 実データ確認後（Step 8）に確定する。ここに書かれた式は `pipeline/src/station_pipeline/scoring.py` と一致させること。

## 1. Features

| key | 日本語 | raw の意味 | 単位 |
| --- | --- | --- | --- |
| tourism | 観光 | 半径内の観光施設・名所数 | 件 |
| culture | 文化 | 半径内の文化財・文化施設数 | 件 |
| publicFacility | 公共施設 | 半径内の公共施設数 | 件 |
| park | 公園 | 半径内の公園・緑地数 | 件 |
| library | 図書館 | 半径内の図書館数 | 件 |
| stationUsage | 駅利用 | 1 日平均乗車人員（全社・全線の合算。JR は乗車のみ公表のため乗車に統一。spec 0005）| 人/日 |

## 2. Percentile rank（0〜100）

欠損（`null`）を除いた n 駅の値について、1 始まりの平均順位（同値は平均）を `r` とする。

```text
percentile = (r - 1) / (n - 1) * 100     (n >= 2)
percentile = null                        (raw が null)
percentile = null（全駅）                 (有効値 n < 3: 比較不能)
```

有効値が 3 駅未満の特徴量は、順位に意味がないため全駅で null とする（例: tourism が 5 駅中 1 駅だけ既知）。
そうしないと、その 1 駅だけに恣意的な percentile（旧仕様では 50）が入り、他の駅と比較条件が揃わない。

小数第 1 位で丸める。

## 3. Low score

```text
<feature>Low = 100 - percentile
```

「その特徴量が相対的に少ないほど高い」。

## 4. YOHAKU SCORE

```text
yohaku = Σ(w_f * low_f) / Σ(w_f)     （low_f が null でない f のみ）
coverage = Σ(w_f : 利用可能) / Σ(w_f : 全体)
```

| key | weight |
| --- | --- |
| tourismLow | 0.25 |
| cultureLow | 0.20 |
| publicFacilityLow | 0.15 |
| parkLow | 0.10 |
| libraryLow | 0.10 |
| stationUsageLow | 0.20 |

- 小数第 1 位で丸める。
- `coverage < 0.5` の場合は `yohaku = null`（判定不能）。
- 定義上の重みは変えない。値のない特徴量の重みは残りへ比例配分する（実効重み, ADR 0009）:
  `effective_w_f = w_f / Σ(利用可能な w)`。寄与 = 実効重み × low で、寄与の合計が YOHAKU SCORE。

## 4.1 順位と感度（v0.2.0, spec 0006）

- 順位: YOHAKU SCORE の降順、同点は同順位（1, 2, 2, 4）。null は順位なし。
- 感度: 6 つの重みを 1 つずつ ×0.5 / ×1.5 にした 12 通り + 基準で順位を計算し、各駅の最小〜最大順位を表示する。
  重みは変えない（診断値）。
- AI / LLM はこの計算に関与しない（ADR 0004）。

## 5. Dominant feature（UI 用）

percentile が最も高い feature（その駅で「相対的に目立つもの」）。同値は上表の順序で先勝ち。
すべて null なら dominant なし。
