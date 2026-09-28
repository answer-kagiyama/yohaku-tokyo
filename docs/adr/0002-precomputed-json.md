# ADR 0002: 駅データは事前計算した JSON として配信する

- Status: Accepted
- Date: 2026-09-27

## Context
スコアは実行時に変化しない。Web 側で集計・空間演算を行う必要はない。

## Decision
Python pipeline がスコアまで計算した `stations.json` を出力し、Next.js はそれを build 時に import して静的生成する。
Web 側は zod で schema を検証し、不一致なら build を失敗させる。

## Consequences
- Web はサーバ API を持たず、静的ホスティング可能。
- データ更新には pipeline 再実行 + 再 build が必要（MVP では許容）。
- 数百駅 × 数十 feature 程度なら JSON サイズは問題にならない。超える場合は駅ごと分割を検討。
