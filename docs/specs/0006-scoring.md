# Spec 0006 — Scoring v0.2.0（Step 8）

- Status: Implemented
- Related: `docs/scoring.md`, ADR 0004, ADR 0009, spec 0005

## 1. Decisions

| 論点 | 決定 | 根拠 |
| --- | --- | --- |
| 観光の重み（25%）| **据え置き**（ユーザー判断 2026-09-28）。値のない特徴量の重みは、残りの特徴量へ比例配分（再正規化）する | 仕組みが一貫し、観光データのある区の駅が 3 駅以上になれば自動的に効き始める |
| 比較不能 | 有効値が 3 駅未満の特徴量は全駅で percentile = null | spec 0005 §5 |
| 駅利用の向き | 乗車人員が少ないほど「余白」が大きい（low = 100 − percentile）| 指示書 §14 の `stationUsageLow` |
| AI の関与 | なし | ADR 0004 |

## 2. 追加する出力

### 2.1 実効重み（effective weight）

```text
effective_w_f = w_f / Σ(w_g : low_g が null でない g)    （low_f が null なら null）
```

内訳表の「寄与」= effective_w_f × low_f。合計が YOHAKU SCORE に一致する。

### 2.2 順位

YOHAKU SCORE の降順（大きいほど余白が大きい = 1 位）。同点は同順位（競技順位: 1, 2, 2, 4）。
スコアが null の駅は順位なし。

### 2.3 重みへの感度（rank range）

6 つの重みを 1 つずつ ×0.5 と ×1.5 に変えた 12 通り + 基準 = 13 通りで全駅のスコアを計算し直し、
各駅の順位の最小〜最大を `ranking.range` とする。

- 決定論的（乱数なし）。
- 駅数が少ない間は、この幅が「この順位をどこまで信じてよいか」の目安になる。
- 重みそのものは変えない（表示用の診断値）。

## 3. stations.json の変更

```jsonc
"ranking": { "rank": 1, "of": 5, "range": [1, 1] } | null,
"effectiveWeights": { "tourismLow": null, "cultureLow": 0.2667, ... }   // station 直下（scores は 0〜100 の値のみ）
```

`scoring.version` を `0.2.0` に上げる。

## 4. UI

- 駅詳細の YOHAKU SCORE の下に「5 駅中 1 位（重みを ±50% 変えても 1〜1 位）」。
- 内訳表に「実効重み」列。定義上の重み（25% 等）と並べる。
- 算出方法ページに、重みの再配分・比較不能・感度の説明を追加。

## 5. Acceptance Criteria

- [x] AC-S1: 実効重みの合計は 1（null を除く）、寄与の合計は YOHAKU SCORE と一致（丸め誤差 ±0.1）
- [x] AC-S2: 順位は同点を同順位で扱い、null は順位なし
- [x] AC-S3: 感度は 13 通りの順位の最小〜最大で、基準順位を必ず含む
- [x] AC-S4: 重み・順位・感度が UI に表示される
- [x] AC-S5: 同じ入力から同じ出力（決定論的）
