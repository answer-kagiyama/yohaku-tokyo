# Spec 0004 — Spatial Aggregate（Step 6: park）

- Status: Implemented
- Related: spec 0003, ADR 0004, ADR 0007, ADR 0008

## 1. Scope

Step 5 の施設（`data/interim/park/facilities.json`）を、各駅から半径 500m で空間集計し、
`stations.json` の `raw.park` を **実データ** に置き換える。他の特徴量は引き続き fixture。

## 2. Distance

- 距離は緯度経度の単純差分で計算しない（指示書 §12）。
- GeoPandas / Shapely で、駅と施設を **JGD2011 / 平面直角座標系 IX 系（EPSG:6677, 単位 m）** に投影し、
  `sjoin(predicate="dwithin", distance=500)` で判定する。境界上（ちょうど 500m）は含む。
- IX 系は東京都本土（区部・多摩）用。島しょ部の駅を扱う段階で系の切替を検討する。

## 3. Completeness（欠損 ≠ 0）

駅の 500m 圏に掛かる区市町村を、国土地理院 逆ジオコーダ
（`mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress`）で求める。

- サンプル点: 中心 + 半径 250m 上 8 点 + 半径 500m 上 16 点 = 25 点。応答はキャッシュ。
- 海上など区市町村が返らない点は無視する。
- 限界: 25 点の間をすり抜ける小さな区域は検出できない（report に明記）。

圏内の区市町村ごとに、その区市町村の park データの状態を判定する:

| 状態 | 条件 |
| --- | --- |
| covered | その組織の accepted データセットが 1 件以上取得済み（status `ok`）で、位置不明の施設が 0 件 |
| partial | 取得済みだが位置不明の施設がある（圏内に入る可能性を否定できない）|
| uncovered | accepted データセットがない、または取得失敗・範囲外（`out-of-scope`）のみ |

駅の集計ステータス:

| status | 条件 | `raw.park` |
| --- | --- | --- |
| complete | 圏内の全区市町村が covered | 圏内の施設数 |
| incomplete | 1 つでも partial / uncovered | **null（欠損）**。下限値 `lowerBound` は evidence に残す |

東京都建設局（都立公園）のように区市町村をまたぐデータセットは補助情報として集計に含めるが、
区市町村の covered 判定には使わない（区市町村リスト側に都立公園が含まれていない可能性があるため、区市町村の網羅性の根拠にならない）。

## 4. Output

`data/processed/aggregates/park.json`:

```jsonc
{
  "feature": "park", "radiusMeters": 500, "crs": "EPSG:6677", "generatedAt": "...",
  "stations": [{
    "stationId": "akihabara",
    "status": "complete" | "incomplete",
    "count": 6 | null,
    "lowerBound": 6,
    "municipalities": [{ "code": "13101", "name": "千代田区", "coverage": "covered" }],
    "facilities": [{ "id", "name", "distanceM", "coordSource", "datasetId", "organization" }],
    "datasets": ["t131016d..."]
  }]
}
```

## 5. stations.json の変更（Web 契約）

- `raw.park` / `normalized.park` / スコアは実データの値から計算される（計算式は不変）。
- `sources`: park に寄与したデータセットを `kind: "opendata"`（`url` = カタログのデータセットページ）として追加。
  fixture ソースの `features` から park を外す。
- `evidence.park`（任意）: `status`, `radiusMeters`, `count`, `lowerBound`, `facilities`（名称・距離・座標の出所）。
- データセット全体: `fixtureFeatures`（まだ架空値の特徴量キー）。`isFixture` は fixture 特徴量が残る間 true。

## 6. Acceptance Criteria

- [x] AC-A1: `make data` で park の集計が行われ、5 駅の `raw.park` が実データになる
- [x] AC-A2: 距離判定は投影座標系（EPSG:6677）+ GeoPandas の dwithin で行う
- [x] AC-A3: 境界ちょうど 500m は含み、500m を超えるものは含まない（テストで検証）
- [x] AC-A4: 圏内の区市町村が uncovered / partial なら `raw.park` は null（0 にしない）
- [x] AC-A5: park の出典データセットが駅の `sources` に URL 付きで載る
- [x] AC-A6: Web の Detail で、park の根拠（施設名・距離）と出典が確認できる
- [x] AC-A7: fixture の特徴量が残っていることを UI に明示する
- [x] AC-A8: テストはネットワークなしで動く

## 7. 実行結果（2026-09-28, park）

| 駅 | status | 公園数 | 圏内の区市町村 |
| --- | --- | --- | --- |
| 秋葉原 | complete | 6 | 千代田区・文京区・台東区 |
| 御徒町 | complete | 3 | 千代田区・文京区・台東区 |
| 上野 | complete | 1 | 台東区 |
| 神田 | complete | 5 | 千代田区・中央区 |
| 浅草橋 | complete | 7 | 千代田区・中央区・台東区・墨田区 |

逆ジオコーダ 125 回（初回のみ、以降キャッシュ）。UI 確認: 駅詳細に「根拠」セクション（施設名・距離・座標の出所・区市町村の網羅状況）、
出典に区ごとのデータセット（カタログへのリンク付き）、検査値・内訳表で fixture の特徴量に「サンプル」表示。
