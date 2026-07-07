import json
from pathlib import Path
from typing import Any


def _read_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def get_template_status(manifest_path: Path, vector_index_path: Path) -> dict[str, object]:
    records = _read_manifest(manifest_path)
    image_count = sum(len(record.get("images", {})) for record in records)
    return {
        "manifestExists": manifest_path.exists(),
        "indexExists": vector_index_path.exists(),
        "productCount": len(records),
        "imageCount": image_count,
        "manifestPath": str(manifest_path),
        "indexPath": str(vector_index_path),
    }


def list_template_sources(source_dir: Path) -> list[dict[str, object]]:
    if not source_dir.exists():
        return []
    sources: list[dict[str, object]] = []
    for path in sorted(source_dir.glob("*.xlsx")):
        stat = path.stat()
        sources.append(
            {
                "filename": path.name,
                "size": stat.st_size,
                "updatedAt": stat.st_mtime,
                "built": True,
            }
        )
    return sources
