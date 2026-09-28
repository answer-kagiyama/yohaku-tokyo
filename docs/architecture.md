# Architecture

## 1. Overview

```text
東京都OD カタログ (CKAN + DataStore)   ✅ Step 4
        ↓ discover (search → inspect → evaluate → overrides)
data/manifests/datasets.json            ✅ Step 4 (park)
        ↓ ingest: fetch → parse → normalize → geocode (GSI) → dedupe   ✅ Step 5 (park)
data/raw/<feature>/ + data/interim/<feature>/facilities.json, report.json
        ↓ aggregate: EPSG:6677 + sjoin dwithin 500m、圏内区市町村の網羅性判定   ✅ Step 6 (park)
data/processed/aggregates/<feature>.json
        ↓
data/processed/stations.master.json   (駅マスタ: config の駅名 + N02 座標・路線 + 年鑑の英語名, spec 0008)
（data/fixtures/stations.raw.json は 5 駅のテスト用 fixture）
        ↓ scoring (percentile rank → weighted "low" score)
data/processed/stations.json
        ↓ export (copy + validate)
apps/web/src/data/stations.json + provenance.json（採用データセットの台帳, spec 0007）
        ↓ import (build 時に zod で検証)
Next.js (静的生成: Home / Explorer / Detail / Methodology / Data)
```

現段階では「raw 集計値」を fixture で差し替え、**スコアリング以降は本番と同じコード経路**を通す。
Step 5〜7 で fixture の代わりに実データ集計結果が入る。

## 2. Components

### pipeline/ (Python 3.13 + uv)

| module | 役割 | 状態 |
| --- | --- | --- |
| `station_pipeline.config` | 半径・重み・feature 定義 | ✅ |
| `station_pipeline.scoring` | percentile rank / low score / YOHAKU SCORE | ✅ |
| `station_pipeline.quality` | Data Quality 検査（ID 重複・座標・0〜100 範囲・出典） | ✅ |
| `station_pipeline.export` | processed JSON 書き出し・Web へのコピー | ✅ |
| `station_pipeline.cli` | `build-fixture` / `export-web` | ✅ |
| `station_pipeline.http` | キャッシュ・リトライ付き JSON クライアント（urllib）| ✅ |
| `station_pipeline.discover` | feature 定義読込・CKAN 探索・RuleBased 評価・manifest | ✅ |
| `station_pipeline.inspect` | 列名推定（緯度/経度/名称/住所）・座標充足率 | ✅ |
| `station_pipeline.fetch` | リソース取得 + 取得メタデータ（URL・日時・sha256）| ✅ |
| `station_pipeline.inspect.tabular` | CSV 読込（UTF-8 BOM / CP932 判定）| ✅ |
| `station_pipeline.normalize` | 行 → Facility、同一施設の統合 | ✅ |
| `station_pipeline.geo.geocode` | GSI 住所検索（ADR 0007）。区市町村レベルの結果は不採用 | ✅ |
| `station_pipeline.ingest` | Step 5 のオーケストレーション・report | ✅ |
| `station_pipeline.aggregate` | 500m 空間結合・区市町村の網羅性・駅ごとの集計（ADR 0008）| ✅ |
| `station_pipeline.geo.municipalities` | 逆ジオコーダで圏内の区市町村を特定 | ✅ |
| `station_pipeline.build` | fixture + 実データ集計 → stations.json（evidence・出典付き）| ✅ |
| `station_pipeline.stations.master` | 駅マスタ（N02 + 年鑑 + 逆ジオコーダ, ADR 0010）| ✅ |
| `station_pipeline.ridership` | 駅利用（統計年鑑の駅別表）| ✅ |
| `station_pipeline.provenance` | データ台帳（/data）| ✅ |
| `classify/` | 空パッケージ（Step 11: Jev） | ⏳ |

外部依存は `pyyaml`（ADR 0005）と `geopandas` / `shapely` / `pyproj`（ADR 0008）。運用設定は `pipeline/config/pipeline.yaml`。

### apps/web/ (Next.js App Router + TypeScript)

```text
src/
├── app/                      ルーティングのみ（薄く保つ）
├── components/ui/            shadcn/ui 由来。トークンで再スタイル済み
├── components/domain/        StationScore, FeatureBar, DataSourceList, MethodologyPanel, ...
├── features/stations/        Explorer のクライアント状態（検索・ソート）
├── domain/                   型・zod schema・純粋関数（sort/filter/breakdown）
├── lib/                      utils (cn), データローダ
├── styles/                   tokens.css（design tokens）
└── data/stations.json        pipeline 出力のコピー
```

- 全ページ静的生成（`generateStaticParams`）。サーバ API は持たない。
- `stations.json` は build 時に zod で検証。スキーマ不一致は build failure。

## 3. Data contract — `stations.json`

```jsonc
{
  "generatedAt": "ISO8601",
  "radiusMeters": 500,
  "isFixture": true,                 // サンプルデータなら true。UI に明示
  "scoring": {
    "version": "0.1.0-mvp",
    "method": "percentile-rank",
    "weights": { "tourismLow": 0.25, ... }
  },
  "stations": [
    {
      "id": "akihabara",
      "name": "秋葉原",
      "nameEn": "Akihabara",
      "lat": 35.6984, "lng": 139.7731,
      "municipality": "千代田区",
      "lines": ["JR山手線", ...],
      "raw":        { "tourism": 14, ..., "library": null },   // null = 欠損（0 ではない）
      "normalized": { "tourism": 75.0, ... },                  // percentile 0〜100 / null
      "semantic":   {},                                        // Step 11 (Jev) で使用
      "scores":     { "yohaku": 21.4, "tourismLow": 25.0, ... },
      "sources":    [ { "id", "name", "organization", "url", "license", "features", "kind" } ]
    }
  ]
}
```

feature キー: `tourism`, `culture`, `publicFacility`, `park`, `library`, `stationUsage`。
Python 側 `station_pipeline.config.FEATURES` と TS 側 `src/domain/features.ts` が同一集合であることを
両側のテストで保証する（fixture を共有入力にする）。

## 4. Principles

- DB なし（ADR 0001）。JSON 事前計算（ADR 0002）。
- AI は最終スコアに関与しない（ADR 0004）。
- 欠損 ≠ 0。欠損 feature は重みを再配分し、`coverage` を併記する（`docs/scoring.md`）。
