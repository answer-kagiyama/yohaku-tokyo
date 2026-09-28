# Spec 0002 — Dataset Discovery MVP（Step 4: park）

- Status: Implemented
- Related: ADR 0003, ADR 0005, `docs/architecture.md`, `docs/data-sources.md`

## 1. Scope

人間が定義した「欲しい概念」（`pipeline/config/feature_definitions.yaml`）から、
東京都オープンデータカタログ（CKAN）を **自動探索 → 自動評価 → manifest 生成** する。
今回は `park` 1 カテゴリのみ。データ本体の取得（fetch）・正規化は Step 5。

## 2. Source API

東京都オープンデータカタログ `https://catalog.data.metro.tokyo.lg.jp` の CKAN Action API。

| API | 用途 |
| --- | --- |
| `package_search?q=<keyword>&rows=100&start=n` | キーワードごとの候補探索（ページング）|
| `datastore_search?resource_id=<id>&limit=50` | DataStore 有効リソースの **列名 + サンプル行**（軽量 inspect）|

- CKAN DataStore は共通形式の API（指示書 Level 1）であり、カタログ検索（Level 2）と同じ基盤で扱える。
- 実データで確認した事実: 列に `緯度`/`経度` があっても **値が空** のデータセットがある（例: 大田区 都市公園一覧）。
  → 列の有無ではなく **サンプル行の座標充足率** で位置情報を評価する。

## 3. Pipeline

```text
feature_definitions.yaml ─▶ search (keyword ごと, ページング, package id で重複排除)
  ─▶ pre-filter (タイトル/タグ/説明のキーワード一致・除外語)
  ─▶ pick best resource (DataStore > JSON/GeoJSON > CSV > XLSX, PDF 除外)
  ─▶ inspect (DataStore のみ: 列名推定・座標充足率)
  ─▶ evaluate (signals → confidence → autoStatus + reason)
  ─▶ duplicate check
  ─▶ apply human overrides (data/manifests/overrides.json)
  ─▶ data/manifests/datasets.json
```

## 4. Evaluation（RuleBased, 決定論的）

| signal | 0〜1 | 根拠 |
| --- | --- | --- |
| semantic | タイトルに概念語 + 一覧語 1.0 / タイトルに概念語のみ 0.7 / 説明・タグ・リソース名のみ 0.4 / なし 0 | keywords, list_hints |
| format | DataStore 1.0 / JSON・GeoJSON 0.9 / CSV 0.8 / KML 0.7 / XLSX・XLS 0.6 / PDF・画像・LAS・ZIP・HTML は利用不可 | 機械可読性 |
| location | 座標充足率（≥0.8 → 1.0、それ未満は比例）/ 住所列のみ 0.5 / なし 0 / 未検査 null | inspect |
| license | CC BY・CC0・政府標準利用規約 1.0 / 不明 0.5 | license_id / title |
| freshness | 2 年以内 1.0 / 5 年以内 0.6 / それ以上 0.3 | metadata_modified |

`confidence = 0.35·semantic + 0.15·format + 0.30·location + 0.10·license + 0.10·freshness`
（location が null のときは 0.5 として計算し、reason に「未検査」と明記）

| autoStatus | 条件 |
| --- | --- |
| rejected | 機械可読リソースなし / 除外語（feature 固有 + `global_exclude_keywords`）がタイトルに含まれる / semantic = 0 |
| accepted | confidence ≥ 0.75 かつ semantic ≥ 0.7 かつ サンプル行の座標充足率 ≥ 80%（座標が実際に入っている）|
| review | それ以外 |

重複: 同一 resource URL、または（組織, 正規化タイトル）が同じもの → 低い方を review にし `duplicateOf` を記録。

## 5. Human review

`data/manifests/overrides.json`:

```json
{ "datasets": { "<datasetId>": { "status": "rejected", "note": "理由" } } }
```

- override があれば `status` はそれに従い、`autoStatus` と `review.note` を残す（自動判定の履歴を失わない）。
- 再探索しても override は保持される。

## 6. Manifest（`data/manifests/datasets.json`）

```jsonc
{
  "generatedAt": "...", "catalog": "https://catalog.data.metro.tokyo.lg.jp",
  "classifier": "rule-based",
  "features": { "park": { "keywords": [...], "candidates": 42, "accepted": 5, "review": 10, "rejected": 27 } },
  "datasets": [{
    "datasetId", "name", "organization", "feature",
    "sourceUrl", "resourceUrl", "resourceId", "format", "datastoreActive",
    "status", "autoStatus", "confidence", "reason",
    "signals": { "semantic", "format", "location", "license", "freshness" },
    "inspection": { "fields", "latField", "lngField", "nameField", "addressField", "sampleSize", "coordFillRate", "total" } | null,
    "license", "lastModified", "updateFrequency", "duplicateOf", "review"
  }]
}
```

別 feature を探索しても、他 feature のエントリは保持する。

## 7. Robustness

- HTTP はタイムアウト・リトライ（3 回, 指数バックオフ）・リクエスト間隔 0.3s。
- レスポンスは `data/interim/catalog-cache/` にキャッシュ（`--refresh` で無視）。再実行はオフラインで再現可能。
- inspect 失敗は location = null（**0 にしない**）とし、reason に記録。

## 8. Acceptance Criteria

- [x] AC-D1: `make discover` で park の manifest が生成される
- [x] AC-D2: キーワードごとの検索結果を package id で重複排除し、ページングで全件取得する
- [x] AC-D3: PDF のみのデータセットは rejected
- [x] AC-D4: 座標列があっても値が空なら accepted にならない
- [x] AC-D5: すべてのエントリに reason / signals / sourceUrl がある（accepted は resourceUrl 必須）
- [x] AC-D6: overrides が status に反映され、autoStatus が保持される
- [x] AC-D7: 他 feature のエントリを消さない
- [x] AC-D8: inspect 失敗は location = null として扱い、パイプラインは完走する
- [x] AC-D9: テストはネットワークなし（fake transport）で動く

## 9. 初回実行結果（2026-09-27, park）

| 指標 | 値 |
| --- | --- |
| 候補（公園・児童遊園・緑地の検索結果を統合）| 703 |
| accepted | 12（新宿・文京・台東・江東・渋谷・杉並区ほか。すべて「都市公園・都立公園一覧」で座標入り）|
| review | 94（うち 24 件は座標列が空で住所のみ → Step 5 でジオコーディングが必要）|
| rejected | 597（キーワード不一致・PDF/画像のみ・除外語）|
| 所要時間 / API 呼び出し | 約 27 秒 / 48 回（2 回目以降はキャッシュで 0 回）|

調整の経緯: 初回は「公園トイレ一覧」が accepted、統計年鑑・審議会資料などが review に大量に入ったため、
park の除外語と `global_exclude_keywords` を追加した（review 173 → 94）。

MVP 対象 5 駅との関係: 台東区（御徒町・上野・浅草橋）は accepted。
千代田区（秋葉原・神田）は DataStore 非対応の CSV のため「位置情報未検査 → review」。Step 5 の fetch 時に inspect する。
