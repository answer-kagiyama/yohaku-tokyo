# ADR 0003: 意味分類は SemanticClassifier アダプタで抽象化する

- Status: Proposed（Step 11。調査・設計は spec 0009、日本語での検証待ち）
- Date: 2026-09-27

## Context
施設カテゴリ正規化・スキーマ列の意味推定に Jev（AI）を使いたいが、Jev が利用できない環境でも pipeline は完走する必要がある。

## Decision
```text
SemanticClassifier (interface)
├── RuleBasedClassifier   ← デフォルト。キーワード辞書ベース
└── JevClassifier         ← 任意。利用不可なら RuleBased にフォールバック
```
分類結果には使用した classifier 名と confidence を必ず記録する。

## Consequences
- Jev なしで全機能が動く。
- 分類の差異を比較・評価できる。

## Update 2026-09-28（調査結果）
- Jev は TypeSafe AI の判断専用モデル（choice / score / noul を確率・確信度付きで返す。文章は生成しない）。詳細は spec 0009。
- 日本語対応が公式に記載されていないため、導入前に正解付きの評価セットで検証する。
- 確信度が高い判定だけを採用し、低いものはルールの結果か「要確認」に残す。人の判断（overrides）が常に優先。
- Jev の判定は分類器名・モデルの版・確信度とともに保存し、同じ入力では再利用する。
