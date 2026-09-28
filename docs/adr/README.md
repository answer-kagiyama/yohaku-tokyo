# Architecture Decision Records

| No. | Title | Status |
| --- | --- | --- |
| [0001](0001-no-database.md) | MVP ではデータベースを使わない | Accepted |
| [0002](0002-precomputed-json.md) | 駅データは事前計算した JSON として配信する | Accepted |
| [0003](0003-semantic-classifier-adapter.md) | 意味分類は SemanticClassifier アダプタで抽象化する | Proposed |
| [0004](0004-no-ai-final-score.md) | AI に最終スコア・ランキングを決めさせない | Accepted |
| [0005](0005-automated-dataset-discovery.md) | データセットは自動探索し manifest で管理する | Accepted |
| [0006](0006-shadcn-as-component-foundation.md) | shadcn/ui をコンポーネントの土台として使う | Accepted |
| [0007](0007-gsi-geocoding.md) | 住所のみの施設は国土地理院 住所検索 API でジオコーディングする | Accepted |
| [0008](0008-spatial-aggregation.md) | 空間集計は GeoPandas + 平面直角座標系 IX 系、網羅性は逆ジオコーダで判定する | Accepted |
| [0009](0009-weight-renormalization.md) | 欠損・比較不能な特徴量の重みは残りへ再配分し、定義上の重みは変えない | Accepted |
| [0010](0010-station-master-n02.md) | 駅マスタは国土数値情報「鉄道データ」（N02）から作る | Accepted |
