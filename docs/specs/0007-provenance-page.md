# Spec 0007 — Data provenance page（Step 9）

- Status: Implemented
- Related: spec 0002〜0006

## 1. Scope

駅ごとの根拠・出典（spec 0004〜0006）に加え、プロダクト全体で
「どのデータセットを、いつ取得し、何件使い、何を除外し、なぜ採用したか」を一覧できる `/data` ページを作る。

## 2. Data

pipeline の `export-web` が `apps/web/src/data/provenance.json` を書き出す（manifest + ingest report から生成）。

```jsonc
{
  "generatedAt": "...", "catalog": "https://catalog.data.metro.tokyo.lg.jp",
  "features": [{ "key": "park", "candidates": 703, "accepted": 44, "review": 53, "rejected": 606 }],
  "datasets": [{
    "feature", "datasetId", "name", "organization", "license", "sourceUrl",
    "status", "autoStatus", "reviewNote", "reason",
    "ingest": { "status", "retrievedAt", "sha256", "rows", "located", "unlocated", "excluded", "outsideTokyo" } | null
  }],
  "services": [{ "name", "use", "url" }]
}
```

- 採用（accepted）のデータセットだけを載せる（review / rejected は件数のみ）。
- `ingest` が null = 駅マスタや年鑑など施設リスト以外の出典。

## 3. UI（`/data`）

- feature ごとに: 探索件数（候補・採用・要確認・不採用）→ 採用データセットの表
  （組織・名称（カタログへのリンク）・取得日・行数・位置あり・除外・状態）。
- 人手レビューで上書きしたものは「人手で採用」と注記。
- 外部サービス（国土地理院 API 等）の一覧。
- desktop は表、mobile は表を横スクロール（design-system §8）。
- フッターと算出方法ページから導線。

## 4. Acceptance Criteria

- [x] AC-V1: `make data` で provenance.json が生成され、zod で検証される
- [x] AC-V2: `/data` に feature ごとの探索件数と採用データセットの表が出る
- [x] AC-V3: 各データセットにカタログへのリンク・取得日時・行数・位置あり件数が表示される
- [x] AC-V4: 人手レビュー（overrides）の採用が区別して表示される
