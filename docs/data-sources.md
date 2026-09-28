# Data sources

| 状態 | 内容 |
| --- | --- |
| 現在 | 6 特徴量すべて東京都オープンデータ。`data/fixtures/stations.raw.json` は駅マスタ（名称・座標・路線）として使用 |
| Step 4 ✅ | park の候補を自動探索し `data/manifests/datasets.json` に記録（ADR 0005, spec 0002）。人手の判定は `data/manifests/overrides.json` |

出典は各駅の `sources[]` に保持し、UI の「出典」セクションに必ず表示する。
`kind` が `fixture` 以外の出典は `url` 必須（pipeline の Data Quality で検査）。

## Step 5 で使用している外部サービス

| サービス | 用途 | 備考 |
| --- | --- | --- |
| 東京都オープンデータカタログ（CKAN）| 探索・メタデータ・リソース取得 | CC BY 4.0 のデータセットが中心 |
| 国土地理院 住所検索 API | 住所のみの施設のジオコーディング | ADR 0007。結果に provider / 一致住所 / 精度を記録 |
| 東京都統計年鑑（運輸・観光）| 駅利用（駅別乗車人員）| spec 0005。最新年のパッケージを検索で選択 |
