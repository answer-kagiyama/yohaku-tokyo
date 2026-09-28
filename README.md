# YOHAKU TOKYO

> 東京の「何もない」を、データで見つける。

東京都・区市町村のオープンデータを横断し、駅周辺 500m に“目的地となりうる施設・機能”が
どれだけあるかを数値化する MVP です。詳細は [docs/product.md](docs/product.md)。

**現在のステータス・次のタスク・未決の論点は [docs/status.md](docs/status.md)**。

**Step 10 完了**（山手線 30 駅 × 6 特徴量、うち 20 駅を判定。駅マスタは国土数値情報 N02。スコア v0.2.0: 実効重み・順位・重みへの感度。`/data` に採用データセットの台帳）。
区のオープンデータが揃わない 10 駅は「判定不能」として不足データを表示（spec 0008）。重みは据え置きで再配分（ADR 0009）。

## 必要なもの

| tool | version | 備考 |
| --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | 0.5+ | Python 3.13 は uv が自動で用意 |
| Node.js | 20.9+（24 LTS 推奨）| 無い場合 `make node` でプロジェクト内 `.tools/` に導入（Linux x64）|
| make | GNU make | |

## Quick start

```bash
make node      # (任意) Node.js が無い場合のみ。.tools/node に導入し Makefile が自動で PATH に追加
make setup     # uv sync + npm ci
make data      # fixture → data/processed/stations.json → apps/web/src/data/stations.json
make dev       # http://localhost:3000
```

## Commands

| command | 内容 |
| --- | --- |
| `make setup` | Python / Node 依存のインストール |
| `make discover` | 東京都オープンデータカタログを探索し `data/manifests/datasets.json` を生成（`FEATURE=park` で絞込）|
| `make data` | 駅マスタ（N02）→ 取得・正規化・ジオコーディング → 500m 空間集計 → 駅利用 → スコア計算 → Web へコピー（初回はネットワーク必須で数十分。2 回目以降はキャッシュで数分）|
| `make dev` | Next.js 開発サーバ |
| `make test` | pytest + Vitest |
| `make lint` | ruff + ESLint + TypeScript typecheck |
| `make build` | Next.js production build（全ページ静的生成）|

## Repository

```text
docs/                 product / architecture / scoring / design-system / specs / adr
apps/web/             Next.js (App Router) + TypeScript + Tailwind v4 + shadcn/ui (Radix)
  src/app/            Home / Station Explorer / Station Detail / Methodology
  src/components/ui/  shadcn 由来（token で再スタイル）
  src/components/domain/  StationScore, FeatureBar, DataSourceList, MethodologyPanel …
  src/domain/         型・zod schema・sort/filter/breakdown（純粋関数）
  src/styles/tokens.css   design tokens
pipeline/             Python (uv) — scoring / quality / export
data/                 fixtures / manifests / raw / interim / processed
```

## Dataset discovery

```bash
make discover                 # enabled な feature（公園・文化・公共施設・観光・図書館）を探索。初回数分、以降はキャッシュ
cd pipeline && uv run station-pipeline discover --feature park --refresh   # キャッシュを無視
```

- 探したい概念は `pipeline/config/feature_definitions.yaml`（キーワード・除外語）で定義する。URL は書かない
- 結果は `data/manifests/datasets.json`。各候補に `status`（accepted / review / rejected）・`confidence`・`reason`・`signals` が付く
- 人が判定を上書きするときは `data/manifests/overrides.json` に書く（自動判定は `autoStatus` として残る）

```json
{ "datasets": { "t131016d0000000000": { "status": "accepted", "note": "fetch 時に座標列を確認済み" } } }
```

## Station master（Step 10）

```bash
cd pipeline && uv run station-pipeline stations        # make data の最初
```

- 対象駅は `pipeline/config/stations.yaml` に**駅名だけ**を書く（現在: 山手線 30 駅）
- 座標・路線は国土数値情報「鉄道データ」（N02, 国土交通省, CC BY 4.0）、英語名は東京都統計年鑑から取得
- 出力: `data/processed/stations.master.json`。ジオコーディング範囲は各駅の 500m 圏に掛かる区から自動で決まる

出典表示: 「国土数値情報（鉄道データ）」（国土交通省）を加工して作成

## Ingest（Step 5）

```bash
cd pipeline && uv run station-pipeline ingest            # make data の前半
```

- 生データ: `data/raw/<feature>/<datasetId>.<ext>` + `.meta.json`（URL・取得日時・sha256）
- 正規化結果: `data/interim/<feature>/facilities.json`（施設ごとの座標・出典・`coordSource`・`unlocatedReason`）
- 品質レポート: `data/interim/<feature>/report.json`
- ジオコーディング対象の区は `pipeline/config/pipeline.yaml` の `geocode.scope`（`auto` = 駅マスタの 500m 圏の区）

## Spatial aggregate（Step 6）

```bash
cd pipeline && uv run station-pipeline aggregate      # make data に含まれる
cd pipeline && uv run station-pipeline ridership      # 駅利用: 東京都統計年鑑の駅別表（make data に含まれる）
```

- 駅と施設を EPSG:6677（平面直角座標系 IX 系, m）に投影し、GeoPandas の `dwithin 500m` で判定
- 圏内に掛かる区市町村を国土地理院 逆ジオコーダで特定し、その区市町村のデータが揃っていなければ件数は **null（欠損）**
- 結果: `data/processed/aggregates/<feature>.json`。Web の駅詳細「根拠」に施設名・距離・座標の出所を表示

## Data flow

```text
stations  : config の駅名 + N02 + 統計年鑑          ─▶ data/processed/stations.master.json
discover  : CKAN 探索 → 評価 → overrides            ─▶ data/manifests/datasets.json
ingest    : 取得 → 正規化 → 分類 → ジオコーディング   ─▶ data/interim/<feature>/facilities.json
aggregate : 500m 空間集計 + 区の網羅性判定          ─▶ data/processed/aggregates/<feature>.json
ridership : 統計年鑑の駅別乗車人員                  ─▶ data/processed/aggregates/stationUsage.json
build     : percentile → low → YOHAKU SCORE → 品質検査 ─▶ data/processed/stations.json
export-web: Web へコピー + データ台帳               ─▶ apps/web/src/data/{stations,provenance}.json（build 時に zod で検証）
```

（`build-fixture` は駅マスタがあればそれを、無ければ 5 駅のテスト用 fixture を使う）

スコアの定義は [docs/scoring.md](docs/scoring.md)。AI は最終スコアに関与しません（[ADR 0004](docs/adr/0004-no-ai-final-score.md)）。

## Contributing

作業前に [AGENTS.md](AGENTS.md) と [docs/design-system.md](docs/design-system.md) を読んでください。

## Data sources & attribution

このリポジトリには、以下のオープンデータを加工したデータ（`data/manifests/`, `data/processed/`, `apps/web/src/data/`）が含まれます。
生データ（`data/raw/`）と API 応答のキャッシュ（`data/interim/`）はコミットしていません（`make data` で再取得）。

| 出典 | ライセンス | 表示 |
| --- | --- | --- |
| 東京都オープンデータカタログ掲載の各データセット（東京都・区市町村）| CC BY 4.0（データセットごとに `data/manifests/datasets.json` の `license` を参照）| 各データセットの提供組織・名称・URL は `/data`（データ台帳）と各駅の出典欄に記載 |
| 国土数値情報 鉄道データ（N02） | CC BY 4.0 | 「国土数値情報（鉄道データ）」（国土交通省）を加工して作成 |
| 東京都統計年鑑（運輸・観光）| CC BY 4.0 | 東京都総務局「東京都統計年鑑」を加工して作成 |

位置情報の補完に国土地理院の住所検索 API・逆ジオコーダを利用しています（応答は再配布していません）。
