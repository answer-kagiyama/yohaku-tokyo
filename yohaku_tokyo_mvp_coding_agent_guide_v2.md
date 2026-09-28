# YOHAKU TOKYO MVP 開発指示書 v2

## 0. 目的

本書は、東京都オープンデータを活用した「何もない駅」MVPを、コーディングエージェントに実装させるためのベース指示書である。

最優先事項は以下。

1. **ローカル環境で再現可能に動作するMVPを完成させる**
2. **東京都オープンデータの探索・取得・統合をできる限り自動化する**
3. **数百駅規模へ拡張可能なデータパイプラインを最初から設計する**
4. **UIは後付けにせず、最初からプロダクトとして見栄えするデザインシステムを持つ**
5. **AI/Jevに依存しすぎず、Jevがなくてもコア機能が動作する**
6. **クラウド化はローカルMVP完成後に検討する**

---

# 1. プロダクト概要

## 1.1 仮称

# YOHAKU TOKYO

キャッチコピー候補:

> 東京の「何もない」を、データで見つける。

「何もない駅」という名称は企画上の説明には使ってよいが、プロダクト名には原則使用しない。

---

## 1.2 コンセプト

東京都・区市町村のオープンデータを横断し、

> 「この駅の周辺には、行政・文化・観光・公共施設などの“目的地”がどの程度存在するか？」

を数値化する。

「何もない」は主観的な断定ではなく、内部的には以下として扱う。

> 東京都・区市町村のオープンデータ上で、駅周辺に存在する“目的地となりうる施設・機能”が相対的に少ない状態

最終スコアは原則として実データから決定論的に算出する。

---

# 2. MVPのゴール

MVP完成条件:

1. 東京都オープンデータカタログ/APIからデータセット候補を自動探索できる
2. 探索結果から利用候補データセットのmanifestを生成できる
3. manifestに基づいて元データを自動取得できる
4. Pythonでデータを正規化できる
5. 駅周辺500mの施設を空間集計できる
6. 駅ごとの特徴量を `stations.json` に出力できる
7. 数百駅規模へ拡張可能である
8. Webアプリから `stations.json` を読み込める
9. 「何もなさ指数」を表示できる
10. 各駅のスコア根拠と利用データ出典を確認できる
11. UIに最低限の完成度・独自性がある
12. テスト・lint・buildが通る
13. READMEだけで別の開発者がローカル起動できる
14. Jevなしでも動く

---

# 3. 開発原則

## 3.1 仕様駆動開発

実装前に仕様を書く。

各機能は以下の順序で進める。

1. `docs/specs/` に仕様を書く
2. Acceptance Criteriaを定義
3. データ依存を整理
4. テストケース作成
5. 実装
6. テスト
7. 仕様更新
8. README / ADR更新

「とりあえず実装」は禁止。

---

## 3.2 Vertical Slice

最初から東京都全域を処理しない。

### Phase 0
- Next.js起動
- Python起動
- サンプルJSON表示

### Phase 1
対象駅5駅:
- 秋葉原
- 御徒町
- 上野
- 神田
- 浅草橋

### Phase 2
実オープンデータ3種類程度を使う

### Phase 3
対象駅を数十駅へ

### Phase 4
数百駅へ

### Phase 5
Jev意味分類導入

---

# 4. データ探索を自動化する

## 4.1 手作業でURLを集めない

最終的に数百駅を扱うため、開発者が自治体ごとのURLを手で収集する設計は禁止。

人間が定義するのは「欲しい概念」であり、個別URLではない。

例:

```yaml
feature_definitions:
  park:
    keywords:
      - 公園
      - 児童遊園
      - 緑地

  culture:
    keywords:
      - 文化財
      - 文化施設
      - 博物館
      - 資料館

  public_facility:
    keywords:
      - 公共施設
      - 地域センター
      - 区民館

  tourism:
    keywords:
      - 観光
      - 名所
      - 観光施設
      - 観光スポット
```

---

# 5. データ取得アーキテクチャ

優先順位:

## Level 1: 東京都共通API / 統一API

共通形式で取得できる公式APIを最優先する。

理由:
- スキーマ差が小さい
- メンテナンスしやすい
- 都内全域に近いカバレッジを期待できる

---

## Level 2: オープンデータカタログ自動探索

共通APIで足りないカテゴリのみ、東京都オープンデータカタログを検索する。

探索対象:

- package / dataset metadata
- organization
- tags
- format
- resource URL
- update timestamp
- license

優先フォーマット:

1. API / DataStore
2. JSON / GeoJSON
3. CSV
4. XLSX
5. PDFは原則除外

---

## Level 3: 候補データセット評価

探索した候補を以下で評価する。

- feature_definitionとの意味的一致
- 緯度経度有無
- 住所有無
- 施設名有無
- 更新頻度
- ライセンス
- 対象エリア
- 重複可能性
- 機械可読性

---

# 6. dataset manifest

自動探索結果は必ずmanifestとして保存する。

```text
data/manifests/datasets.json
```

例:

```json
{
  "generatedAt": "2026-09-27T00:00:00Z",
  "datasets": [
    {
      "datasetId": "example",
      "name": "○○区 公園一覧",
      "organization": "○○区",
      "feature": "park",
      "sourceUrl": "https://...",
      "resourceUrl": "https://...",
      "format": "csv",
      "status": "accepted",
      "confidence": 0.94,
      "reason": "公園施設名と位置情報を含む",
      "license": "CC BY",
      "lastModified": "..."
    }
  ]
}
```

status:

- accepted
- review
- rejected

完全自動採用だけにしない。

**自動探索 + 自動判定 + 人間がレビュー可能**

な構成にする。

---

# 7. Jevの使い方

## 7.1 JevはETL/意味理解側で使う

Jevをランキング生成器として使用しない。

推奨用途:

### A. データセット適合判定

例:

> このデータセットは park 特徴量の生成に利用可能か？

### B. スキーマ列の意味分類

例:

```text
施設名称
所在地
緯度
経度
カテゴリ
```

を自治体ごとの異なる列名から推定する。

### C. 施設カテゴリ正規化

例:

```text
○○ふれあい館
↓
community
```

### D. 補助的意味特徴

- touristy
- residential_feel
- cultural_density
- community_strength
- walkability_interest

---

## 7.2 AI Provider抽象化

必須。

```text
SemanticClassifier
├── RuleBasedClassifier
└── JevClassifier
```

Jevが利用できない場合でもパイプラインが完走すること。

---

# 8. データパイプライン

最終イメージ:

```text
東京都OD API / カタログ
        ↓
discover
        ↓
dataset-manifest.json
        ↓
fetch
        ↓
data/raw
        ↓
normalize
        ↓
classify
        ↓
geocode / coordinates
        ↓
spatial aggregate
        ↓
normalize scores
        ↓
stations.json
        ↓
Next.js
```

---

# 9. Repository Structure

```text
yohaku-tokyo/
├── README.md
├── AGENTS.md
├── Makefile
├── .env.example
│
├── docs/
│   ├── product.md
│   ├── architecture.md
│   ├── data-sources.md
│   ├── scoring.md
│   ├── design-system.md
│   ├── specs/
│   └── adr/
│
├── apps/
│   └── web/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   │   ├── ui/
│       │   │   └── domain/
│       │   ├── features/
│       │   │   └── stations/
│       │   ├── lib/
│       │   ├── domain/
│       │   ├── styles/
│       │   └── data/
│       │       └── stations.json
│       └── tests/
│
├── pipeline/
│   ├── pyproject.toml
│   ├── src/station_pipeline/
│   │   ├── discover/
│   │   ├── fetch/
│   │   ├── inspect/
│   │   ├── normalize/
│   │   ├── classify/
│   │   ├── geo/
│   │   ├── aggregate/
│   │   ├── scoring/
│   │   └── export/
│   └── tests/
│
├── data/
│   ├── manifests/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── fixtures/
│
└── scripts/
```

---

# 10. Data Policy

DBは使わない。

MVP禁止:

- PostgreSQL
- MySQL
- RDS
- Cloud SQL
- DynamoDB
- Firestore

理由:

- 読み取り中心
- 更新頻度が低い
- 数百駅程度ならJSON/Parquetで十分
- 再現性優先

---

# 11. Stations Dataset

```json
{
  "generatedAt": "...",
  "radiusMeters": 500,
  "stations": [
    {
      "id": "akihabara",
      "name": "秋葉原",
      "lat": 35.6984,
      "lng": 139.7731,
      "raw": {},
      "normalized": {},
      "semantic": {},
      "scores": {},
      "sources": []
    }
  ]
}
```

---

# 12. GIS

駅から半径500mを初期値とする。

```python
DEFAULT_RADIUS_METERS = 500
```

距離は緯度経度の単純差分で計算しない。

GeoPandas / Shapelyを使用。

---

# 13. 正規化

原則:

**Percentile Rank**

を採用。

0〜100。

理由:
- 外れ値に強い
- UIで説明しやすい

---

# 14. スコア

MVP仮仕様:

```text
tourismLow        25%
cultureLow        20%
publicFacilityLow 15%
parkLow           10%
libraryLow        10%
stationUsageLow   20%
```

実データ確認後に確定。

AIに直接ランキングさせない。

---

# 15. Frontend Technology

## Core

- Next.js
- TypeScript
- React
- App Router

## UI

- shadcn/ui
- Radix Primitives
- Tailwind CSS
- Lucide Icons

## Chart

必要になった場合のみ:
- Recharts

## Animation

原則CSS transition。

Motion系ライブラリは、本当にUX上必要な場合のみ追加。

---

# 16. shadcn/ui採用方針

shadcn/uiは「完成デザイン」ではなく、コンポーネント実装の土台として使う。

**shadcn/uiのデフォルト見た目をそのまま使用してはいけない。**

以下をプロジェクト独自に定義する。

- color tokens
- typography
- radius
- shadow
- spacing
- border
- card density
- chart style
- icon usage

---

# 17. デザインコンセプト

## 17.1 キーワード

- 東京の余白
- 都市観察
- 編集された統計資料
- フィールドノート
- 駅のカルテ
- 少しアナログ
- 落ち着いたデータビジュアライゼーション

避ける:

- AIチャット風
- 紫〜青グラデーション
- glassmorphism多用
- ネオン
- 過度なカードUI
- 何でも角丸
- 過剰なshadow
- dashboardテンプレート感

---

# 18. Visual Direction

## Color

原則ニュートラル基調。

例:

- warm off-white
- charcoal
- muted gray
- 1色だけアクセント

アクセント色はデザイン実装時に決める。

Tailwind標準カラーを直接大量使用せずCSS variablesでtoken化する。

例:

```css
:root {
  --background: ...;
  --foreground: ...;
  --muted: ...;
  --accent: ...;
  --border: ...;
}
```

---

## Typography

日本語本文は読みやすさ優先。

英数字・スコアには視認性の高いSansを使用。

重要:

- 大きいスコア数値
- 小さい注釈
- 駅名
- データラベル

の階層を明確にする。

---

## Shape

角丸は控えめ。

例:

- button: medium
- cards: small-medium
- data table: nearly square

すべてを巨大なrounded cardにしない。

---

# 19. UIコンポーネント設計

shadcn/uiから利用候補:

- Button
- Card
- Tabs
- Tooltip
- Sheet
- Dialog
- Select
- Separator
- Table
- Badge
- Progress
- Skeleton
- Command

ただしdomain componentで包む。

例:

```text
components/ui/
  shadcn由来

components/domain/
  StationSummaryCard
  StationScore
  FeatureBar
  DataSourceList
  MethodologyPanel
```

アプリ全体でshadcn componentを直接乱用しない。

---

# 20. MVP画面

## Home

目的:
プロダクトの世界観を一発で伝える。

含む:

- ロゴ / wordmark
- コンセプトコピー
- 注目駅3〜5件
- 「何もなさ指数」の説明
- methodology導線

ダッシュボード風にしない。

---

## Station Explorer

駅一覧。

- compact list
- score
- dominant feature
- sort
- search

カードグリッドだけにしない。

デスクトップではtable/list寄りを優先。

---

## Station Detail

「駅のカルテ」として見せる。

例:

```text
秋葉原

YOHAKU SCORE
21.4

目的地密度
████████

文化
██████

公園
███

観光
████████
```

さらに:

- raw data
- percentile
- source
- methodology

を確認可能。

---

# 21. Responsive Design

Desktop firstではなくresponsive前提。

最低対応:

- mobile
- tablet
- desktop

スマホでも駅詳細の主要情報が1スクロール目で把握できること。

---

# 22. Accessibility

Radix/shadcnのaccessibilityを壊さない。

必須:

- keyboard navigation
- focus visible
- semantic HTML
- contrast
- aria label
- reduced motion考慮

---

# 23. UI Storybookについて

MVPではStorybookは必須にしない。

代わりに:

```text
/design
```

または開発用routeで主要UIパーツを一覧表示できるページを作ってもよい。

ただし過剰なら不要。

---

# 24. デザイン仕様書

`docs/design-system.md` を必ず作る。

含める:

- design concept
- colors
- typography
- spacing
- radius
- shadows
- components
- do / don't
- responsive rules

コーディングエージェントはUI追加前にこれを読むこと。

---

# 25. テスト

## Python

- discovery
- manifest generation
- fetch
- schema inspect
- normalize
- coordinates
- 500m判定
- aggregation
- percentile
- score
- export
- missing data

## TypeScript

- JSON parsing
- sort
- StationSummary
- StationDetail
- methodology rendering

## E2E

Playwright:

1. Home
2. Explorer
3. Station Detail
4. methodology
5. source表示

---

# 26. Data Quality

以下で失敗時はpipelineをfailさせる。

- station ID duplicate
- station name missing
- invalid coordinates
- score outside 0-100
- normalized outside 0-100
- accepted dataset without source
- schema mismatch

重要:

**データ取得失敗を「施設数0」と解釈しない。**

---

# 27. CLI

```bash
make setup
make discover
make data
make dev
make test
make lint
make build
```

## discover

- ODカタログ探索
- dataset候補評価
- manifest生成

## data

- accepted dataset取得
- normalize
- classify
- aggregate
- export
- Webへcopy

---

# 28. ADR

最低限:

- 0001-no-database
- 0002-precomputed-json
- 0003-semantic-classifier-adapter
- 0004-no-ai-final-score
- 0005-automated-dataset-discovery
- 0006-shadcn-as-component-foundation

---

# 29. コーディングエージェントのルール

必須:

- 変更前にspec/ADRを読む
- 実装前に短いplan
- コアロジックにはtest
- 外部dependency追加理由を記録
- データ項目を推測しない
- 自動採用理由をmanifestに残す
- provenanceを失わない
- UI変更時はdesign-system.mdに従う

禁止:

- いきなり全都データ
- DB導入
- cloud deploy
- auth
- microservices
- Kubernetes
- Terraform
- AI agent architecture
- default shadcn lookのまま完成扱い
- AIチャット画面中心のUX

---

# 30. Definition of Done

- `make setup`
- `make discover`
- `make data`
- `make dev`
- `make test`
- `make lint`
- `make build`

がローカルで成功。

さらに:

- manifestが生成される
- 取得元を追跡可能
- stations.json生成
- 駅一覧表示
- 駅詳細表示
- score根拠表示
- mobile対応
- design-system.md準拠
- Jevなしでも動作

---

# 31. 推奨実装順序

## Step 1
Skeleton

- docs
- Next.js
- Python
- Makefile

## Step 2
Design System

- shadcn init
- tokens
- typography
- core components
- design-system.md

## Step 3
Sample UI

5駅fixtureでHome / Explorer / Detail。

## Step 4
Dataset Discovery MVP

1カテゴリだけ。

例: park

カタログ検索 → manifest。

## Step 5
Fetch + Normalize

## Step 6
Spatial Aggregate

## Step 7
3〜5カテゴリへ拡大

## Step 8
Scoring

## Step 9
Data provenance UI

## Step 10
数十駅へ

## Step 11
Jev導入

## Step 12
数百駅へ

---

# 32. クラウド化

ローカルMVP完成後。

候補:

## GCP

```text
Cloud Run
 ├ Next.js
 └ stations.json
```

## AWS

```text
App Runner
 ├ Next.js
 └ stations.json
```

データ更新を自動化する段階でCloud Storage / S3等を検討する。

---

# 33. 最初にコーディングエージェントへ渡すタスク

```text
YOHAKU TOKYO MVPのPhase 0〜Step 3までを実装してください。

必ず本指示書を最初に読み、仕様駆動で進めてください。

今回の範囲:

1. docs/product.md
2. docs/architecture.md
3. docs/design-system.md
4. ADR 0001〜0006の雛形
5. apps/web: Next.js + TypeScript
6. shadcn/ui初期設定
7. CSS design tokens
8. pipeline: Python + uv
9. dataディレクトリ
10. 5駅のfixture stations.json
11. Home
12. Station Explorer
13. Station Detail
14. pytest
15. Vitest
16. Makefile
17. README

UI要件:

- shadcn/uiを土台にする
- shadcnのデフォルトデザインをそのまま使わない
- docs/design-system.mdでvisual languageを先に定義する
- 「都市観察 / 編集された統計資料 / 駅のカルテ」をデザインテーマとする
- AIチャット風・紫グラデーション・glassmorphismは禁止
- mobile / desktopの両方を成立させる

まだ実装しないもの:

- 実オープンデータ取得
- dataset discovery
- Jev
- AWS/GCP
- DB
- 認証

実装前に以下を提示してください:

- planned files
- repository structure
- design direction
- implementation order

完了時:

- 主要変更
- UI設計
- tests
- 未実装事項
- 次のStep
```

次タスクでDataset Discoveryを実装する。
