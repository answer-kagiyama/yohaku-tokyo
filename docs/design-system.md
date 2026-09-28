# Design System — YOHAKU TOKYO

> UI を追加・変更する前に必ず読むこと。shadcn/ui は **部品の土台** であり、見た目はこの文書が決める。

## 1. Concept

**「駅のカルテ」 — 都市観察の記録を、編集された統計資料として綴じる。**

| キーワード | UI への翻訳 |
| --- | --- |
| 東京の余白 | 余白そのものを主役にする。要素を詰めない。1 画面 1 主張 |
| 都市観察 / フィールドノート | 細い罫線・記入欄・観察番号（No. 001）・座標表記 |
| 編集された統計資料 | 表組み・脚注・出典・キャプション。数字は等幅で揃える |
| 駅のカルテ | 見出し → 所見（スコア）→ 検査値（特徴量）→ 出典、の固定順序 |
| 少しアナログ | 紙色の地、墨色の文字、朱の赤入れ。わずかな紙の罫 |

### Don't（禁止）

- AI チャット風 UI（吹き出し・入力欄中心・「✨」）
- 紫〜青グラデーション、ネオン、glow
- glassmorphism（backdrop-blur による半透明パネル）
- 何でも角丸・巨大な rounded card のグリッド
- 過剰な shadow、ダッシュボードテンプレート感（KPI タイルの羅列）
- Tailwind 標準色（`bg-blue-500` 等）の直接使用 — 必ず token 経由

## 2. Color tokens

`apps/web/src/styles/tokens.css` が唯一の定義元。Tailwind には `@theme inline` で公開する。

全 token は `--yk-` 接頭辞（shadcn の `--accent` 等と衝突させないため）。値は WCAG 比を実測して選定。

| token | 値 | 用途 | paper 上のコントラスト |
| --- | --- | --- | --- |
| `--yk-paper` | `#F4F1EA` | 地（warm off-white）| — |
| `--yk-paper-sunken` | `#EBE7DC` | 表のヘッダ、引用、hover 面 | — |
| `--yk-paper-raised` | `#FAF8F3` | 入力欄・ポップオーバー | — |
| `--yk-ink` | `#1E1D1B` | 本文・見出し（charcoal）| 14.9:1 |
| `--yk-ink-muted` | `#57534C` | 補足文 | 6.8:1 |
| `--yk-ink-faint` | `#655F57` | キャプション・注釈 | 5.6:1（sunken 上 5.1:1）|
| `--yk-rule` | `#D5CFC1` | 細罫線（装飾）| — |
| `--yk-rule-input` | `#857F73` | 入力欄の罫（UI 部品境界）| 3.5:1 |
| `--yk-rule-strong` | `#1E1D1B` | 見出し下の太罫・表の上下罫 | — |
| `--yk-vermilion` | `#AD3620` | **唯一のアクセント（朱）**。スコア・赤入れ・focus | 5.6:1 |
| `--yk-vermilion-soft` | `#F2E3DB` | 朱の面（選択行、ハイライト）| 朱文字 5.1:1 |
| `--yk-data` | `#3D3A35` | 特徴量バー（存在量）| 10.0:1 |
| `--yk-data-track` | `#E2DDD1` | バーのトラック | — |
| `--yk-missing` | 斜線パターン | 欠損値（0 と区別するため塗りではなく斜線）| — |

Tailwind へは `bg-paper`, `text-ink`, `text-vermilion`, `border-rule` 等として公開する。

ルール:
- アクセント（朱）は **1 画面に 1〜3 箇所**。YOHAKU SCORE・現在地・focus ring に限る。
- データバーは墨色（`--data`）。スコア以外に朱を使わない。
- 状態色（success/warning 等）は MVP では使わない。エラーは朱 + テキストで示す。
- ダークモードは MVP 対象外（紙の比喩を優先）。token 化してあるので後から追加可能。

shadcn の semantic token（`--background`, `--primary`, …）は上記へのエイリアスとして定義し、
shadcn コンポーネントが自然にこのパレットを使うようにする。

## 3. Typography

| 役割 | フォント | 用途 |
| --- | --- | --- |
| Display（和）| **Shippori Mincho B1** | 駅名・ページ見出し。資料の標題の格 |
| Body（和）| **Noto Sans JP** | 本文・UI ラベル |
| Numeric / Latin | **IBM Plex Sans**（`tabular-nums`）| スコア・数値・英字キャプション |
| Mono | **IBM Plex Mono** | 座標・ID・観察番号 |

スケール（rem）:

| token | size / line-height | 用途 |
| --- | --- | --- |
| `text-score` | 4.5rem → md: 6rem / 1 | 詳細ページの YOHAKU SCORE |
| `text-display` | 2.75rem → md: 4rem / 1.1 | 駅名（詳細）|
| `text-title` | 1.75rem / 1.3 | ページ見出し |
| `text-heading` | 1.125rem / 1.5 | セクション見出し |
| `text-body` | 0.9375rem / 1.8 | 本文（和文は行間広め）|
| `text-label` | 0.8125rem / 1.5 | UI ラベル |
| `text-caption` | 0.6875rem / 1.4, `letter-spacing: 0.12em`, 大文字 | 英字キャプション（`YOHAKU SCORE`, `No. 003`）|

階層ルール: **大きいスコア数値 ≫ 駅名 ≫ データラベル ≫ 注釈**。同じ画面で 4 段以上のサイズを混ぜない。

## 4. Spacing

4px グリッド。セクション間は大きく取り「余白」を演出する。

| 用途 | 値 |
| --- | --- |
| 行内 | 4 / 8px |
| 行間（リスト・表の行）| 12〜16px |
| ブロック間 | 32px |
| セクション間 | 64px（mobile 48px）|
| ページ左右 gutter | 20px（mobile）/ 40px（desktop）|
| 本文最大幅 | 42rem、レイアウト最大幅 72rem |

## 5. Radius

| token | 値 | 用途 |
| --- | --- | --- |
| `--radius-sm` | 2px | 表・バー・バッジ（ほぼ四角）|
| `--radius-md` | 4px | ボタン・入力欄 |
| `--radius-lg` | 6px | ポップオーバー・シート（上限）|

pill 型（`rounded-full`）は使わない。

## 6. Shadow / Border

- **shadow は原則使わない。** 区切りは罫線で表現する。
- 例外: ポップオーバー／セレクトの浮き上がりに `--shadow-pop`（1 段、ごく薄い）。
- 罫線: 通常 1px `--rule`。セクション見出し下と表の上下は 1px〜2px `--rule-strong`（統計表の「表罫」）。

## 7. Components

### shadcn 由来（`components/ui/`）— token で再スタイル済み
Button, Badge, Input, Select, Separator, Table（Tooltip は mobile で機能しないため MVP では不採用）

- Button: `default`（墨ベタ）/ `outline`（罫線）/ `ghost` / `link`（下線）。朱ベタのボタンは作らない。
- Badge: 四角（2px）、罫線のみ。塗りは `--paper-sunken`。

### Domain（`components/domain/`）— ページはこちらを使う
| component | 役割 |
| --- | --- |
| `Wordmark` | 「YOHAKU TOKYO」ロゴタイプ + 余白記号 |
| `SiteHeader` / `SiteFooter` | ナビゲーション |
| `FixtureNotice` | サンプルデータ使用中の注記（脚注風）|
| `StationScore` | YOHAKU SCORE の大きな数値 + 評語（余白 大/中/小）|
| `ScoreMeter` | 一覧用の細い横棒スコア |
| `FeatureBar` | 特徴量 1 行（ラベル・raw・percentile バー・欠損表示）|
| `FeatureBreakdownTable` | raw / percentile / low / weight / 寄与 の統計表 |
| `DataSourceList` | 出典リスト（脚注番号付き）|
| `MethodologyPanel` | 算出方法の説明 |
| `StationLedger` | Explorer の表（desktop: table / mobile: 行リスト）|
| `SectionHeading` | 英字キャプション + 和文見出し + 太罫 |

### Chart style
- 横棒のみ（MVP）。高さ 6〜8px、角 2px、トラックあり。
- バーの長さ = percentile（0〜100）。値ラベルは右端に等幅数字。
- 欠損は斜線パターンのトラック + 「欠損」ラベル。**0 と同じ見た目にしない。**

### Icon usage
- Lucide、stroke 1.5、サイズ 16px。装飾目的では使わない（矢印・外部リンク・検索・並べ替えのみ）。

## 8. Responsive rules

| breakpoint | 方針 |
| --- | --- |
| < 640px（mobile）| 1 カラム。Explorer は行リスト。詳細は **駅名 + スコア + 特徴量バー** が 1 スクロール目に入る |
| 640〜1023px（tablet）| 1 カラム、表は横スクロール可 |
| ≥ 1024px（desktop）| 詳細は 2 カラム（左: 見出し・スコア、右: 検査値）。Explorer は table |

- タップ領域は 44px 以上。
- 表は `overflow-x: auto` のコンテナに入れ、ページ本体を横スクロールさせない。

## 9. Accessibility

- Radix の keyboard / aria 挙動を壊さない（ui/ コンポーネントの構造は維持し、className のみ変更）。
- focus visible: 2px 朱の outline + 2px offset。
- コントラスト: 本文 AA 以上（上表の token は検証済み値で選定）。
- バーには数値テキストを併記し、色や長さだけに意味を持たせない。
- `prefers-reduced-motion` で transition を無効化。
- 見出し階層（h1 → h2 → h3）を飛ばさない。

## 10. Motion

CSS transition のみ（150ms, ease-out）。hover の色・下線の変化程度。Motion 系ライブラリは導入しない。
