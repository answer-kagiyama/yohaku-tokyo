# station-pipeline

YOHAKU TOKYO のデータパイプライン。現段階（Phase 0〜Step 3）は fixture の raw 値から
スコアを計算し `stations.json` を出力する。

```bash
uv sync
uv run station-pipeline build-fixture   # data/fixtures -> data/processed
uv run station-pipeline export-web      # data/processed -> apps/web/src/data
uv run pytest
```
