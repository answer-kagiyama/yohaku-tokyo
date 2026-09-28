# ADR 0006: shadcn/ui をコンポーネントの土台として使う（見た目は独自）

- Status: Accepted
- Date: 2026-09-27

## Context
アクセシブルな部品（Radix）を短期間で揃えたい一方、既定の shadcn の見た目はテンプレート感が強く、プロダクトの世界観（駅のカルテ）に合わない。

## Decision
- shadcn/ui をコピーして `components/ui/` に置き、構造（Radix / aria）は維持したまま className とトークンを差し替える。
- 色・タイポ・角丸・罫線・影は `docs/design-system.md` と `src/styles/tokens.css` で定義する。
- ページは原則 `components/domain/` を使い、ui コンポーネントを直接乱用しない。

## Consequences
- a11y を保ちながら独自の visual language を持てる。
- shadcn の更新は手動マージになる（コピー方式の性質上許容）。

## Dependencies
| package | 理由 |
| --- | --- |
| radix-ui | shadcn の基盤。keyboard / aria 実装 |
| class-variance-authority, clsx, tailwind-merge | shadcn の variant / class 合成 |
| lucide-react | アイコン（最小限の使用）|
| zod | stations.json の実行時検証（ADR 0002）|
