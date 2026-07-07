#!/usr/bin/env python3
"""Match an uploaded product image against the extracted template library.

This is a local baseline matcher. It combines perceptual hash distance and
simple color histogram distance, then returns the most likely product, package
type and template view. In production, replace `image_features` with a
multimodal embedding model while keeping the same manifest format.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class TemplateMatch:
    score: float
    product_code: str
    product_name: str
    package_type: str
    view: str
    image_path: str
    source_workbook: str
    sheet: str
    row: int


def average_hash(path: Path, size: int = 16) -> int:
    with Image.open(path) as img:
        gray = ImageOps.exif_transpose(img).convert("L").resize((size, size))
        pixels = list(getattr(gray, "get_flattened_data", gray.getdata)())
    avg = sum(pixels) / len(pixels)
    bits = 0
    for pixel in pixels:
        bits = (bits << 1) | int(pixel >= avg)
    return bits


def color_histogram(path: Path, bins: int = 8) -> list[float]:
    with Image.open(path) as img:
        rgb = ImageOps.exif_transpose(img).convert("RGB").resize((160, 160))
        hist = [0] * (bins * 3)
        for r, g, b in getattr(rgb, "get_flattened_data", rgb.getdata)():
            hist[r * bins // 256] += 1
            hist[bins + g * bins // 256] += 1
            hist[2 * bins + b * bins // 256] += 1
    total = sum(hist) or 1
    return [v / total for v in hist]


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def euclidean_distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def image_features(path: Path) -> tuple[int, list[float]]:
    return average_hash(path), color_histogram(path)


def load_templates(manifest_path: Path) -> list[dict[str, Any]]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_template_path(image_path: str, manifest_path: Path) -> Path:
    template_path = Path(image_path)
    if template_path.is_absolute() or template_path.exists():
        return template_path
    fallback = manifest_path.parent.parent.parent / template_path
    return fallback if fallback.exists() else template_path


def build_feature_index(manifest_path: Path, index_path: Path) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for record in load_templates(manifest_path):
        for view, image_path in record["images"].items():
            template_path = resolve_template_path(image_path, manifest_path)
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
                    "view": view,
                    "image_path": str(template_path),
                    "source_workbook": record["source_workbook"],
                    "sheet": record["sheet"],
                    "row": int(record["row"]),
                }
            )

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return index


def load_or_build_index(manifest_path: Path, index_path: Path, rebuild: bool) -> list[dict[str, Any]]:
    if not rebuild and index_path.exists():
        return json.loads(index_path.read_text(encoding="utf-8"))
    return build_feature_index(manifest_path, index_path)


def match_image(
    upload_path: Path,
    manifest_path: Path,
    index_path: Path,
    top_k: int,
    rebuild_index: bool,
) -> list[TemplateMatch]:
    upload_hash, upload_hist = image_features(upload_path)
    matches: list[TemplateMatch] = []

    for template in load_or_build_index(manifest_path, index_path, rebuild_index):
        template_hash = int(template["hash"])
        template_hist = template["histogram"]
        hash_distance = hamming_distance(upload_hash, template_hash) / 256
        color_distance = euclidean_distance(upload_hist, template_hist)
        score = max(0.0, 1.0 - (0.75 * hash_distance + 1.8 * color_distance))
        matches.append(
            TemplateMatch(
                score=score,
                product_code=template["product_code"],
                product_name=template["product_name"],
                package_type=template["package_type"],
                view=template["view"],
                image_path=template["image_path"],
                source_workbook=template["source_workbook"],
                sheet=template["sheet"],
                row=int(template["row"]),
            )
        )

    return sorted(matches, key=lambda item: item.score, reverse=True)[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser(description="Match an uploaded image to product templates.")
    parser.add_argument("image", type=Path, help="Uploaded image path")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("outputs/product_templates/manifest.json"),
        help="Template manifest path generated by extract_excel_templates.py",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("outputs/product_templates/feature_index.json"),
        help="Cached template feature index path",
    )
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    results = match_image(args.image, args.manifest, args.index, args.top_k, args.rebuild_index)
    print(
        json.dumps(
            [result.__dict__ for result in results],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
