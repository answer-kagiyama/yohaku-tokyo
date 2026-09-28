# Spec 0003 — Fetch + Normalize + Geocode（Step 5: park）

- Status: Implemented
- Related: spec 0002, ADR 0005, ADR 0007（geocoding）

## 1. Scope

manifest で `accepted` の park データセットを取得し、施設レコードを共通スキーマに正規化する。
座標が無く住所だけの行は、国土地理院の住所検索 API でジオコーディングする。
空間集計（500m 判定）は Step 6。Web 表示の数値はまだ fixture。

## 2. Discovery の変更（spec 0002 の改訂）

| 変更 | 理由 |
| --- | --- |
| DataStore 非対応の CSV も、候補（semantic ≥ 0.7・除外語なし）ならダウンロードして inspect する | 千代田区などが「未検査 → review」に留まっていたため |
| 座標が空でも **住所充足率 ≥ 80%** なら location = 0.8（`locationSource: "geocode"`）とし、accepted になり得る | ジオコーディング導入（ADR 0007）により住所のみでも利用可能になったため |

実データでの確認事項: 千代田区 都市公園一覧（22 件）は `緯度`/`経度` 列が全件空、住所は全件あり。

## 3. Pipeline

```text
manifest (accepted, feature=park)
  ─▶ fetch     resourceUrl をダウンロード → data/raw/park/<datasetId>.<ext> + .meta.json（URL, 取得日時, sha256, bytes）
  ─▶ parse     CSV（UTF-8 BOM / CP932 自動判定）→ 行
  ─▶ normalize 列推定（名称・緯度・経度・住所）→ Facility
  ─▶ geocode   座標が無く住所がある行のみ（GSI）
  ─▶ data/interim/park/facilities.json + report.json
```

## 4. Facility schema

```jsonc
{
  "id": "<datasetId>:<行番号>",
  "feature": "park",
  "name": "宮本公園",
  "address": "東京都千代田区外神田二丁目16番９号" | null,
  "lat": 35.702072 | null, "lng": 139.76712 | null,   // null = 位置不明（0 ではない）
  "coordSource": "source" | "geocode" | null,
  "geocode": { "provider": "gsi", "matched": "東京都千代田区外神田二丁目１６番９号", "precision": "exact" | "partial" } | null,
  "datasetId": "...", "organization": "千代田区", "sourceUrl": "...", "resourceUrl": "..."
}
```

## 5. Geocoding rules（GSI 住所検索 API）

`GET https://msearch.gsi.go.jp/address-search/AddressSearch?q=<住所>`

- 住所のクリーニング: 複数地域（`/`・`・`・`;` 区切り）は先頭のみ、末尾の「ほか・他・先」を除去、重複した区市町村名を除去。
- 区市町村名が無ければ組織名を補う（組織が区市町村のときのみ。「東京都建設局」などは補わない）→「東京都」を補う。
- 比較は正規形で行う: NFKC・空白除去、漢数字の丁目を算用数字に、「丁目・番地・番・号」とハイフン類を `-` に統一
  （実測: 元データ `両国3－13－9` に対し API は `両国三丁目１３番９号` を返す）。
- `partial` は区切り位置での前方一致のみ（`銀座1-2` は `銀座1-25-2` に一致しない、町名 `芝` は `芝公園1` に一致しない）。
- **API は存在しない住所にも区市町村の代表点を返す**（実測: `東京都千代田区存在しない町99` → `東京都千代田区`）。
  返却 `title` から「東京都」と区市町村名を除いた残りが空なら **不採用**（`coordSource: null`）。
- `title` が正規化後の問い合わせと一致 → `exact`、問い合わせの前方一致（丁目・町字まで）→ `partial`、それ以外 → 不採用。
- 座標は東京都の範囲（緯度 20–36.5, 経度 136–154）外なら不採用。
- 応答は `data/interim/geocode-cache/` にキャッシュ。リクエスト間隔 0.3 秒。

## 6. Quality

- 名称列が見つからないデータセット → そのデータセットは `failed`（report に記録）。パイプライン全体は継続。
- ダウンロード失敗 → `failed`。**施設 0 件とは扱わない**（Step 6 で「そのエリアは欠損」と扱う材料になる）。
- report.json に dataset ごとの `rows / withSourceCoords / geocoded / unlocated / status` を出力。
- 座標付き施設の割合（ジオコーディング範囲内の行に対して）が 50% 未満なら `status: "degraded"`。
  全行がジオコーディング範囲外なら `status: "out-of-scope"`（意図的な未処理であり品質低下ではない）。
- 位置不明の施設には必ず `unlocatedReason`（`no-address` / `out-of-geocode-scope` / `geocode-not-found` / `geocode-error`）を付ける。
- 同名（括弧内の読み等を除いて正規化）かつ 150m 以内の施設は 1 件に統合し、統合元を `duplicates` に記録する
  （例: 文京区の「都市公園一覧」と「区立公園・児童遊園一覧」の重複掲載）。優先度: 元データ座標 > exact > partial。

## 6.1 Scope（`pipeline/config/pipeline.yaml`）

ジオコーディングは対象 5 駅の 500m 圏に掛かる区（千代田・台東・中央・文京・墨田）と東京都建設局に限定する。
全都分（約 4,500 行）を一度に GSI へ問い合わせることを避けるため。対象駅の拡大（Step 10）に合わせて広げる。

## 7. Acceptance Criteria

- [x] AC-F1: `make data` で accepted の park データセットが取得・正規化され、facilities.json と report.json が出力される
- [x] AC-F2: 生データと取得メタデータ（URL・取得日時・sha256）が data/raw に保存される
- [x] AC-F3: CP932 と UTF-8 (BOM) の CSV を読める
- [x] AC-F4: 座標のない行は住所からジオコーディングされ、`coordSource: "geocode"` と一致精度が記録される
- [x] AC-F5: 区市町村レベルの粗い結果は採用しない（lat/lng = null）
- [x] AC-F6: 取得失敗・名称列なしは dataset 単位で failed として report に残り、全体は完走する
- [x] AC-F7: 秋葉原・神田の周辺（千代田区）の公園が座標付きで得られる
- [x] AC-F8: テストはネットワークなしで動く

## 8. 実行結果（2026-09-27, park）

| 指標 | 値 |
| --- | --- |
| 取得データセット | 44（failed 0 / degraded 0 / out-of-scope 22）|
| 行 → 施設 | 6,284 行 → 重複統合 188 → 6,096 施設 |
| 位置あり | 1,850（元データ座標 + ジオコーディング）|
| 位置不明 | 4,246（すべて `out-of-geocode-scope`。`geocode-not-found` 0）|
| 所要時間 | 初回 約 2 分、以降キャッシュで約 10 秒 |

ジオコーディングの改善経緯: 初回は 230 件中 208 件が not-found。原因は (1) 組織名「東京都建設局」を住所に前置していた、
(2) `3－13－9` と `三丁目１３番９号` の表記差、(3) 「先」「;」を含む住所。修正後 0 件。

参考（半径 500m, 直線距離による概算。正式な空間集計は Step 6）: 秋葉原 6・御徒町 3・上野 1・神田 5・浅草橋 7 件。
秋葉原には 佐久間公園・和泉公園・芳林公園・秋葉原公園・淡路公園・練塀公園 が入り、区境をまたぐ集計もできている。
