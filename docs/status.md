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
| 11 | Jev 導入（SemanticClassifier）| ADR 0003 | ⏳ 未着手 |
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

## 3. 未決の論点（ユーザーに相談する）

1. **「何もない」に商業施設・オフィスを含めるか** — 東京駅が 5 位（余白が大きい側）になる。丸の内のオフィス・商業は現在の 6 特徴量で数えられない。特徴量追加（商業・飲食など）か、現定義のまま注記かを決める。
2. **数百駅（Step 12）時の GSI API 負荷** — 初回ジオコーディングが数千〜1 万件規模になる。分割実行・キャッシュ共有（GCS/S3 等）・実行頻度を決める。
3. **LICENSE** — public リポジトリだがライセンスファイルがない（コードの再利用条件が未定）。
4. **指示書の公開** — `yohaku_tokyo_mvp_coding_agent_guide_v2.md` は public リポジトリに含まれている。問題があれば履歴ごと削除する。
5. **クラウド化（パイプライン）** — 案: GitHub Actions で月次 `make data` → 差分を PR → 人がレビューして merge → Vercel 自動デプロイ。未合意（ADR 未作成）。

## 4. 次にやること（候補）

| 優先 | タスク | メモ |
| --- | --- | --- |
| 高 | CI（GitHub Actions: `make test` / `make lint` / `make build`）| push には `workflow` スコープ付きトークンが必要 |
| 高 | Playwright E2E（指示書 §25: Home / Explorer / Detail / methodology / source 表示）| 現状は手動スクリーンショットで確認している（§6）|
| 中 | 「要確認（review）」データセットの人手レビュー | `data/manifests/datasets.json` の `status: review`。採否は `overrides.json` に `<feature>/<datasetId>` で書く |
| 中 | Step 11: Jev を `SemanticClassifier` として追加 | 現在は RuleBased（`discover/evaluate.py` と `ingest.matches_feature`）。Jev なしで完走すること |
| 中 | 未決論点 1 の方針決定後に特徴量の見直し | `docs/scoring.md`・`config.FEATURES`・`src/domain/features.ts` を同期 |
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
