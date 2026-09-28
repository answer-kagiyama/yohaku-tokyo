# Spec 0001 — Skeleton + Design System + Sample UI（Phase 0〜Step 3）

- Status: Implemented
- Related: `docs/product.md`, `docs/architecture.md`, `docs/scoring.md`, `docs/design-system.md`

## 1. Scope

5 駅（秋葉原・御徒町・上野・神田・浅草橋）の **fixture raw 値** から、本番と同じスコアリング経路で
`stations.json` を生成し、Home / Station Explorer / Station Detail / Methodology を表示する。

実オープンデータ取得・dataset discovery・Jev・クラウド・DB・認証は対象外。

## 2. Data dependencies

| 入力 | 出力 |
| --- | --- |
| `data/fixtures/stations.raw.json`（手書き、raw 集計値のみ）| `data/processed/stations.json` |
| `data/processed/stations.json` | `apps/web/src/data/stations.json`（コピー）|

fixture の raw 値は **架空のサンプル値** であり、実データではない。`isFixture: true` を出力に含める。
fixture には欠損（`null`）を最低 1 件含め、欠損 ≠ 0 の表示を検証できるようにする。

## 3. Acceptance Criteria

### Pipeline
- [x] AC-P1: `make data` で fixture から `data/processed/stations.json` が生成され、Web にコピーされる
- [x] AC-P2: percentile rank は `docs/scoring.md` §2 に従う（同値平均順位・null 除外。spec 0005 で「有効値 3 駅未満は比較不能」に改訂）
- [x] AC-P3: YOHAKU SCORE は欠損 feature の重みを除外して再正規化し、`coverage` を出力する
- [x] AC-P4: Data Quality 違反（ID 重複・名称欠落・不正座標・0〜100 範囲外・出典なし）で失敗する
- [x] AC-P5: 同一入力から同一出力（`generatedAt` を除き決定論的）

### Web
- [x] AC-W1: `stations.json` は zod で検証され、不正なら例外（build failure）
- [x] AC-W2: Home に wordmark・コンセプトコピー・注目駅 3 件（スコア上位）・指数の説明・methodology 導線
- [x] AC-W3: Explorer で駅名（和/英）検索、スコア/駅名/各特徴量でのソート（昇降）ができる。駅名ソートは英字表記（読みの代理）順
- [x] AC-W4: Explorer は desktop で table、mobile で行リスト
- [x] AC-W5: Detail に駅名・YOHAKU SCORE・特徴量バー・raw/percentile/low/weight 表・出典・methodology
- [x] AC-W6: 欠損 feature は「欠損」と表示し、0 と異なる見た目（斜線）で描画する
- [x] AC-W7: fixture 使用中は全ページで注記を表示する
- [x] AC-W8: mobile（375px）で Detail の駅名・スコア・特徴量バーが 1 スクロール目付近に入る
- [x] AC-W9: 存在しない駅 ID は 404

### Non-functional
- [x] `make test` / `make lint` / `make build` が成功
- [x] design-system.md の Don't に抵触しない（紫グラデ・glass・pill・過剰 shadow なし）

## 4. Test cases

| 対象 | テスト |
| --- | --- |
| pytest `test_scoring.py` | percentile（昇順・同値・n=1・null）、low、yohaku 加重・再正規化・coverage 閾値 |
| pytest `test_quality.py` | 各違反の検出、正常系 |
| pytest `test_build.py` | fixture → dataset 生成、決定論性、欠損保持、Web コピー |
| Vitest `schema.test.ts` | 実 JSON の parse 成功、不正 JSON の拒否 |
| Vitest `stations.test.ts` | sort（昇降・null 末尾）、filter、dominant feature、breakdown |
| Vitest `components.test.tsx` | StationScore、FeatureBar 欠損表示、MethodologyPanel の重み表示、DataSourceList |
| Vitest `station-ledger.test.tsx` | 検索・ソート操作 |
