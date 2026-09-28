# ADR 0004: AI に最終スコア・ランキングを決めさせない

- Status: Accepted
- Date: 2026-09-27

## Context
「何もない」は主観に寄りやすい。AI に直接ランキングさせると再現性・説明可能性が失われる。

## Decision
YOHAKU SCORE は実データから決定論的に算出する（`docs/scoring.md`）。
AI の用途はデータセット適合判定・列の意味分類・カテゴリ正規化・補助的意味特徴（`semantic`）に限定し、
`semantic` の値は YOHAKU SCORE の計算式に入れない。

## Consequences
- 同じ入力から常に同じスコアが出る。各スコアは raw → percentile → low → 加重平均で説明できる。
