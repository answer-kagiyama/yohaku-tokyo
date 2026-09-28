# ADR 0003: 意味分類は SemanticClassifier アダプタで抽象化する

- Status: Proposed（Step 11 で実装）
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
