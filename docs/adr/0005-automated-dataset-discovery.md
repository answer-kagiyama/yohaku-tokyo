# ADR 0005: データセットは自動探索し manifest で管理する

- Status: Accepted（Step 4 で実装。`docs/specs/0002-dataset-discovery.md`）
- Date: 2026-09-27

## Context
数百駅を扱うため、自治体ごとの URL を手作業で集める運用はスケールしない。

## Decision
人間は「欲しい概念」（feature_definitions のキーワード）だけを定義する。
東京都 OD API / カタログを自動探索し、候補を評価して `data/manifests/datasets.json` に
`status: accepted | review | rejected`、`confidence`、`reason`、出典情報とともに保存する。
完全自動採用にはせず、人間が manifest をレビュー・上書きできるようにする。

## Consequences
- 取得元（provenance）が常に追跡可能。
- 自動判定の誤りはレビューで補正する必要がある。

## Implementation notes
- 探索元は東京都オープンデータカタログの CKAN Action API（`package_search`）と DataStore API（`datastore_search`）。
  DataStore は共通形式 API（指示書 Level 1）として、サンプル行による列推定・座標充足率の測定にも使う。
- 評価は RuleBased（決定論的）。Jev による適合判定は Step 11 で `SemanticClassifier` として追加する（ADR 0003）。

## Dependencies
| package | 理由 |
| --- | --- |
| pyyaml | 人間が編集する `feature_definitions.yaml` を読むため（指示書の YAML 形式に合わせる）。HTTP は標準ライブラリ `urllib` で足りるため追加しない |
