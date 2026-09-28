# Status & Handoff

> 最終更新: 2026-09-28 / 作業を始めるエージェントは、まずこのファイルと `AGENTS.md` を読むこと。

## 1. 現在地

**Step 10 完了**（指示書 §31 の Step 1〜10）。山手線 30 駅 × 6 特徴量を東京都オープンデータ等から算出し、20 駅を判定済み。

| Step | 内容 | 仕様 | 状態 |
| --- | --- | --- | --- |
| 1〜3 | Skeleton / Design System / Sample UI | spec 0001 | ✅ |
| 4 | Dataset Discovery（CKAN 探索 → manifest）| spec 0002, ADR 0005 | ✅ |
| 5 | Fetch + Normalize + Geocode（GSI）| spec 0003, ADR 0007 | ✅ |
| 6 | Spatial Aggregate（EPSG:6677, 500m, 網羅性判定）| spec 0004, ADR 0008 | ✅ |
| 7 | 5 カテゴリ + 駅利用（統計年鑑）| spec 0005 | ✅ |
| 8 | Scoring v0.2.0（実効重み・順位・感度）| spec 0006, ADR 0009 | ✅ |
| 9 | データ台帳 `/data` | spec 0007 | ✅ |
| 10 | 駅マスタ（N02）・山手線 30 駅 | spec 0008, ADR 0010 | ✅ |
| 11 | Jev 導入（SemanticClassifier）| spec 0009, ADR 0003 | ✅ v1 実装（要確認データセットの判定・混在リストの行分類）。判定結果はレビュー待ち |
| 12 | 数百駅 | — | ⏳ 未着手 |

テスト: pytest 183 / Vitest 68。`make test` / `make lint` / `make build` が通る状態でコミット済み。

## 2. ユーザー判断の記録（再確認不要）

| 日付 | 論点 | 決定 | 記録 |
| --- | --- | --- | --- |
| 2026-09-27 | 住所のみの施設 | 国土地理院 住所検索 API でジオコーディング | ADR 0007 |
| 2026-09-28 | 観光の重み（25%）| 据え置き。値のない特徴量の重みは残りへ再配分 | ADR 0009 |
| 2026-09-28 | 駅マスタ | 国土数値情報 鉄道データ（N02）| ADR 0010 |
| 2026-09-28 | 数十駅の範囲 | 山手線 30 駅 | spec 0008 |
| 2026-09-28 | データ不足の駅 | 厳密なまま「判定不能」と表示（基準を緩めない）| spec 0008 §6 |
| 2026-09-28 | リポジトリ | public。生データ・API キャッシュはコミットしない | README「Data sources」|
| 2026-09-28 | Web 公開 | Vercel（Root Directory = `apps/web`, Framework = Next.js）| 本ファイル §5 |
| 2026-09-28 | 作業場所 | 当面はローカルで作業（クラウドエージェント移行は後で）| — |
| 2026-09-28 | Jev | 仕様・活用方法は Claude が調査・検討。API キーはユーザーが発行 | spec 0009 |
| 2026-09-28 | 商業施設・オフィス | 別の特徴量として数える方向（東京駅が「余白が大きい」側に出る問題への対応）| 本ファイル §4 |
| 2026-09-28 | LICENSE | 当面不要 | — |
| 2026-09-28 | 指示書 | public リポジトリで公開したままでよい | — |

## 2.1 レビュー待ち（エージェントの判断）

エージェントが下した判断（overrides、評価セットの正解ラベルなど）は、ユーザーがレビューするまでここに載せる。

| 対象 | 判断 | 状態 |
| --- | --- | --- |
| overrides: 文京区「文化・スポーツ施設」を culture に採用 | エージェント | ✅ ユーザー承認 2026-09-28 |
| overrides: 品川区「文化財」（遺跡一覧）を不採用 | エージェント | ✅ ユーザー承認 2026-09-28 |
| Jev による要確認データセットの採否（採用 3・不採用 92、`docs/reviews/2026-09-28-jev-datasets.md`）| Jev（エージェント）| ⏳ レビュー待ち |
| 文京区「文化・スポーツ施設」: Jev がシビックホール・アカデミー各館を公共施設と判定し、文化は 0 件 → 文京区の文化を「欠損」扱いに（御徒町・秋葉原・巣鴨の文化が欠損、巣鴨は判定不能に）| エージェント | ⏳ レビュー待ち |
| Jev 評価セットの正解ラベル（`pipeline/tests/fixtures/jev_eval/`）| エージェント | ✅ ユーザー確認 2026-09-28（スポーツ施設=none、博物館等=tourism、寺社所蔵品=曖昧、で合意）|

## 3. 未決の論点（ユーザーに相談する）

1. **商業・オフィスの特徴量の中身** — 別の特徴量にする方向は決定済み。データ源（候補: 食品営業許可一覧・商店街一覧・経済センサスの町丁目別事業所数）と重みは未定。
2. **数百駅（Step 12）時の GSI API 負荷** — 初回ジオコーディングが数千〜1 万件規模になる。分割実行・キャッシュ共有・実行頻度を決める。
3. **クラウド化（パイプライン）** — 案: GitHub Actions で月次 `make data` → 差分を PR → 人がレビューして merge → Vercel 自動デプロイ。未合意（ADR 未作成）。
4. **施設データ・ジオコーディング結果のコミット** — private リポジトリ化すればコミットしてよい（ユーザー見解）。public の間は `make data` / `make refresh` の分離で対応する案。

## 4. 次にやること（候補）

| 優先 | タスク | メモ |
| --- | --- | --- |
| 高 | CI（GitHub Actions: `make test` / `make lint` / `make build`）| push には `workflow` スコープ付きトークンが必要 |
| 高 | Playwright E2E（指示書 §25: Home / Explorer / Detail / methodology / source 表示）| 現状は手動スクリーンショットで確認している（§6）|
| 中 | 「要確認（review）」データセットの人手レビュー | `data/manifests/datasets.json` の `status: review`。採否は `overrides.json` に `<feature>/<datasetId>` で書く |
| 高 | 要確認に残るデータセットの位置情報問題 | Jev でカテゴリは判定できたが、座標・住所が使えず採用できないもの（大田区 公園一覧、台東区・中央区 観光ポイント、品川区 公立図書館情報 など）|
| 中 | 商業・オフィスの特徴量（新 spec）| データ源の調査 → 相談 → `docs/scoring.md`・`config.FEATURES`・`src/domain/features.ts` を同期 |
| 低 | Step 12: 数百駅 | `pipeline/config/stations.yaml` に駅名を追加するだけで動く設計。負荷対策（論点 2）が先 |

## 5. 環境メモ（クラウドエージェント向け）

- **Web だけならネットワーク不要に近い**: 表示データ（`apps/web/src/data/*.json`）はコミット済み。`make setup` → `make test` / `make build` で完結する。
  ただし `next build` は Google Fonts（`next/font/google`）を取得するため `fonts.googleapis.com` / `fonts.gstatic.com` への通信が必要。
- **`make data` は外部通信が必須**: `catalog.data.metro.tokyo.lg.jp`、`*.metro.tokyo.lg.jp` 等の区サイト、`data.bodik.jp`、
  `msearch.gsi.go.jp`、`mreversegeocoder.gsi.go.jp`、`nlftp.mlit.go.jp`、`www.toukei.metro.tokyo.lg.jp`。
  キャッシュ（`data/interim/`）はコミットしていないため、**初回は GSI API を約 2,000 回呼び、30 分以上かかる**。むやみに再実行しない。
  pipeline の変更を検証するだけなら `make test`（ネットワーク不要の fake transport）で足りる。
- **Node**: `node` が無い環境では `make node` で `.tools/node`（v24, Linux x64）に入る。Makefile が自動で PATH に追加する。
- **uv**: Python 3.13 は uv が用意する。
- **git の作者**: このリポジトリは `answer-kagiyama` アカウントで管理している。
- **Vercel**: Root Directory = `apps/web`、Framework Preset = Next.js、Output Directory は上書きしない（`public` を指定するとビルドが失敗する）。

## 6. 作業の進め方

- 仕様駆動: spec → AC → テスト → 実装 → spec/README/ADR 更新（`AGENTS.md`）。
- 危険な操作・外部公開以外は確認を求めずに進めてよい。判断が必要な論点は、選択肢と推奨を添えてユーザーに相談する。
- UI を変えたら、本番ビルド（`next start`）を desktop 1360px と mobile 390px（必要なら 360px）で撮影して確認する。
  `document.documentElement.scrollWidth` がビューポート幅を超えないこと（横はみ出しなし）も確認する。
  Playwright の Chromium が `libasound.so.2` 不足で起動しない場合は `apt-get download libasound2t64` → `dpkg-deb -x` → `LD_LIBRARY_PATH` で回避できる。
- 実データで気づいたデータの癖（文字コード、列名、住所表記、混在リストなど）は spec の「判明した問題と対応」表に追記する。
