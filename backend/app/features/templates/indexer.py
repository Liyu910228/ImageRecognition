from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.features.recognition.product_tags import extract_product_tags
from app.features.recognition.matcher import image_features


def build_feature_index(manifest_path: Path, index_path: Path) -> int:
    records: list[dict[str, Any]] = json.loads(manifest_path.read_text(encoding="utf-8"))
    index: list[dict[str, Any]] = []
    for record in records:
        for view, image_path in record["images"].items():
            template_path = Path(image_path)
            if not template_path.exists():
                continue
            template_hash, template_hist = image_features(template_path)
            index.append(
                {
                    "hash": str(template_hash),
                    "histogram": template_hist,
                    "product_code": record["product_code"],
                    "product_name": record["product_name"],
                    "package_type": record["package_type"],
                    "tags": record.get(
                        "tags",
                        extract_product_tags(record.get("product_name", ""), record.get("product_code", ""), record.get("package_type", "")),
                    ),
                    "view": view,
                    "image_path": str(template_path),
                    "source_workbook": record["source_workbook"],
                    "sheet": record["sheet"],
                    "row": int(record["row"]),
                }
            )

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return len(index)
