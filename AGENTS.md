# AGENTS.md — コーディングエージェント向けルール

作業前に必ず読むもの:
1. `yohaku_tokyo_mvp_coding_agent_guide_v2.md`（開発指示書）
2. `docs/product.md`, `docs/architecture.md`, `docs/scoring.md`
3. UI を触る場合は `docs/design-system.md`
4. 関連する `docs/specs/*` と `docs/adr/*`

## 進め方（仕様駆動）
spec → Acceptance Criteria → データ依存 → テスト → 実装 → テスト → spec/README/ADR 更新。

## 必須
- コアロジック（scoring / quality / domain）にはテストを書く
- 外部 dependency を追加したら理由を ADR または docs に記録する
- データ項目を推測しない。欠損は `null`（0 にしない）
- provenance（出典）を失わない
- Python の `config.FEATURES` と TS の `src/domain/features.ts` を同期させる
- UI は `components/domain/` を使い、色・サイズは token（`bg-paper`, `text-ink`, `text-vermilion`, `text-label` …）のみ
- 独自の text-* token を増やしたら `src/lib/utils.ts` の `createCn` にも登録する

## 禁止
DB / cloud deploy / auth / microservices / Kubernetes / Terraform / AI agent architecture /
AI による最終スコア / 紫グラデ・glassmorphism・AI チャット風 UI / default shadcn look のまま完成扱い

## コマンド
`make setup | data | dev | test | lint | build`（詳細は README）
