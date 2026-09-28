# ADR 0001: MVP ではデータベースを使わない

- Status: Accepted
- Date: 2026-09-27

## Context
データは読み取り中心で更新頻度が低い（数日〜数ヶ月単位）。対象は最大でも数百駅。
再現性（同じ入力 → 同じ出力）を最優先したい。

## Decision
PostgreSQL / MySQL / RDS / Cloud SQL / DynamoDB / Firestore 等の DB を MVP では導入しない。
中間データは `data/` 配下の JSON（将来 Parquet）ファイルで保持する。

## Consequences
- 運用コスト・認証情報管理が不要。git diff でデータ変化を追える。
- 書き込み系機能（ユーザー投稿等）は作れない。必要になった時点で再検討する。
