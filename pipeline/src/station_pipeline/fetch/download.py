"""Download dataset resources into data/raw with provenance metadata."""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..http import HttpClient


@dataclass(frozen=True)
class RawFile:
    path: Path
    datasetId: str
    resourceUrl: str
    retrievedAt: str
    sha256: str
    bytes: int


def raw_path(raw_dir: Path, entry: dict[str, Any]) -> Path:
    ext = (entry.get("format") or "bin").lower()
    return raw_dir / entry["feature"] / f"{entry['datasetId']}.{ext}"


def fetch_resource(
    client: HttpClient, entry: dict[str, Any], raw_dir: Path, now: datetime
) -> RawFile:
    body = client.get_bytes(entry["resourceUrl"])
    path = raw_path(raw_dir, entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    meta = RawFile(
        path=path,
        datasetId=entry["datasetId"],
        resourceUrl=entry["resourceUrl"],
        retrievedAt=now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        sha256=hashlib.sha256(body).hexdigest(),
        bytes=len(body),
    )
    meta_dict = {k: v for k, v in asdict(meta).items() if k != "path"}
    path.with_suffix(path.suffix + ".meta.json").write_text(
        json.dumps(meta_dict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return meta
