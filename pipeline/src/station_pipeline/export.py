"""Write processed datasets and copy them to the web app."""

import json
import shutil
from pathlib import Path
from typing import Any

from .quality import validate_dataset


def write_dataset(data: dict[str, Any], path: Path) -> None:
    validate_dataset(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_web(processed: Path, destination: Path) -> None:
    validate_dataset(json.loads(processed.read_text(encoding="utf-8")))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(processed, destination)
