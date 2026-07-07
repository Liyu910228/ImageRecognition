from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_settings(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_settings(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_json_settings(path: Path) -> None:
    if path.exists():
        path.unlink()
