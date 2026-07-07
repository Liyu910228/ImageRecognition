from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from app.features.recognition.product_tags import (
    extract_product_tags,
    infer_package_type,
    is_generic_snow_brand,
    template_tags,
)


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class MatchResult:
    score: float
    product_code: str
    product_name: str
    package_type: str
    view: str
    image_path: str
    template_image_url: str | None
    source_workbook: str
    sheet: str
    row: int
    visual_score: float
    brand_score: float
    text_score: float
    package_score: float
    weights: dict[str, float]
    matched_keywords: list[str]


@dataclass(frozen=True)
class MatchPipeline:
    stage1_package_type: str | None
    stage1_count: int
    stage1_fallback: bool
    stage2_keywords: list[str]
    stage2_count: int
    stage2_fallback: bool
    stage3_count: int


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
    return [value / total for value in hist]


def image_features(path: Path) -> tuple[int, list[float]]:
    return average_hash(path), color_histogram(path)


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def euclidean_distance(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def load_feature_index(index_path: Path) -> list[dict[str, Any]]:
    return json.loads(index_path.read_text(encoding="utf-8"))


def template_image_url(image_path: str, template_images_dir: Path) -> str | None:
    path = Path(image_path)
    if path.is_absolute():
        try:
            path.relative_to(template_images_dir)
        except ValueError:
            return None
        return f"/template-images/{path.name}"
    if path.parent.name == "images":
        return f"/template-images/{path.name}"
    return None


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def expand_keywords(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for value in values:
        text = value.strip()
        if not text:
            continue
        expanded.append(text)
        expanded.extend(re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?度?|\d+ml|[\u4e00-\u9fff]{2,}", text, flags=re.I))
    seen: set[str] = set()
    result: list[str] = []
    for item in expanded:
        key = normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def discriminative_keywords(keywords: list[str]) -> list[str]:
    generic = {
        "瓶",
        "听",
        "箱",
        "纸箱",
        "产品",
        "图片",
        "正面",
        "背面",
        "侧面",
        "顶图",
        "底图",
    }
    result: list[str] = []
    for keyword in keywords:
        normalized = normalize_text(keyword)
        if not normalized or normalized in generic:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", normalized):
            continue
        if re.fullmatch(r"[a-z]", normalized):
            continue
        if re.fullmatch(r"[a-z]?\d+[a-z]?", normalized):
            continue
        result.append(keyword)
    return result


def keyword_score(template: dict[str, Any], keywords: list[str]) -> tuple[float, list[str]]:
    if not keywords:
        return 0.0, []
    tags = template_tags(template)
    haystack = normalize_text(
        " ".join(
            [
                str(template.get("product_name", "")),
                str(template.get("product_code", "")),
                str(template.get("package_type", "")),
                str(template.get("view", "")),
                " ".join(tags["keywords"]),
                " ".join(tags["capacities"]),
                " ".join(tags["degrees"]),
                " ".join(tags["specs"]),
                " ".join(tags["packages"]),
            ]
        )
    )
    matched: list[str] = []
    weighted = 0.0
    for keyword in expand_keywords(keywords):
        needle = normalize_text(keyword)
        if not needle or needle not in haystack:
            continue
        matched.append(keyword)
        if any(char.isdigit() for char in needle):
            weighted += 1.25
        elif len(needle) >= 3:
            weighted += 1.0
        else:
            weighted += 0.7
    return min(1.0, weighted / 4.0), matched[:8]


def brand_score(template: dict[str, Any], brands: list[str]) -> tuple[float, list[str]]:
    if not brands:
        return 0.0, []
    tags = template_tags(template)
    haystack = normalize_text(
        " ".join(
            [
                str(template.get("product_name", "")),
                str(template.get("product_code", "")),
                " ".join(tags["brands"]),
                " ".join(tags["keywords"]),
            ]
        )
    )
    matched: list[str] = []
    weighted = 0.0
    for brand in expand_keywords(brands):
        needle = normalize_text(brand)
        if not needle or needle not in haystack:
            continue
        matched.append(brand)
        weighted += 1.4 if len(needle) >= 4 else 1.0
    return min(1.0, weighted / 2.0), matched[:5]


def package_match_score(template_package: str, target_package: str | None) -> float:
    if not target_package:
        return 0.0
    normalized = str(template_package)
    normalized = normalized.replace("Ïä", "箱").replace("Æ¿", "瓶").replace("Ìı", "听")
    return 1.0 if target_package in normalized else -0.35


def visual_similarity(upload_hash: int, upload_hist: list[float], template: dict[str, Any]) -> float:
    template_hash = int(template["hash"])
    template_hist = template["histogram"]
    hash_distance = hamming_distance(upload_hash, template_hash) / 256
    color_distance = euclidean_distance(upload_hist, template_hist)
    return max(0.0, 1.0 - (0.75 * hash_distance + 1.8 * color_distance))


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(value, 0.0) for value in weights.values())
    if total <= 0:
        return weights
    return {key: round(max(value, 0.0) / total, 6) for key, value in weights.items()}


def ranking_weights(
    has_brand_input: bool,
    has_brand_match: bool,
    configured_weights: dict[str, float] | None = None,
    generic_brand_only: bool = False,
) -> dict[str, float]:
    configured_weights = configured_weights or {}
    if has_brand_input and has_brand_match and generic_brand_only:
        return normalize_weights(
            {
                "visual": configured_weights.get("weight_generic_brand_visual", 0.72),
                "brand": configured_weights.get("weight_generic_brand_brand", 0.08),
                "text": configured_weights.get("weight_generic_brand_text", 0.20),
            }
        )
    if has_brand_input and has_brand_match:
        return normalize_weights(
            {
                "visual": configured_weights.get("weight_brand_match_visual", 0.2),
                "brand": configured_weights.get("weight_brand_match_brand", 0.55),
                "text": configured_weights.get("weight_brand_match_text", 0.25),
            }
        )
    if has_brand_input:
        return normalize_weights(
            {
                "visual": configured_weights.get("weight_brand_miss_visual", 0.8),
                "brand": 0.0,
                "text": configured_weights.get("weight_brand_miss_text", 0.2),
            }
        )
    return normalize_weights(
        {
            "visual": configured_weights.get("weight_no_brand_visual", 0.85),
            "brand": 0.0,
            "text": configured_weights.get("weight_no_brand_text", 0.15),
        }
    )


def match_uploaded_image(
    upload_path: Path,
    index_path: Path,
    template_images_dir: Path,
    top_k: int = 5,
    package_type: str | None = None,
    keywords: list[str] | None = None,
    brands: list[str] | None = None,
    weights: dict[str, float] | None = None,
    strict_brand_filter: bool = False,
) -> tuple[list[MatchResult], MatchPipeline]:
    upload_hash, upload_hist = image_features(upload_path)
    search_keywords = keywords or []
    search_brands = brands or []
    extracted_tags = extract_product_tags(*search_brands, *search_keywords)
    search_brands = search_brands if strict_brand_filter and search_brands else [*search_brands, *extracted_tags["brands"]]
    search_keywords = [*search_keywords, *extracted_tags["keywords"]]
    if not package_type:
        package_type = infer_package_type(*search_keywords)
    templates = load_feature_index(index_path)

    stage1_templates = templates
    stage1_fallback = False
    if package_type:
        filtered = [
            template
            for template in templates
            if package_match_score(str(template.get("package_type", "")), package_type) > 0
        ]
        if filtered:
            stage1_templates = filtered
        else:
            stage1_fallback = True

    stage2_templates = stage1_templates
    stage2_fallback = False
    expanded_keywords = expand_keywords(search_keywords)
    stage2_keywords = discriminative_keywords(expanded_keywords)
    stage2_brands = discriminative_keywords(expand_keywords(search_brands))
    if stage2_keywords or stage2_brands:
        scored = []
        for template in stage1_templates:
            text_score, matched_keywords = keyword_score(template, stage2_keywords)
            template_brand_score, matched_brands = brand_score(template, stage2_brands)
            if strict_brand_filter and stage2_brands and template_brand_score <= 0:
                continue
            combined_score = (template_brand_score * 0.65) + (text_score * 0.35) if stage2_brands else text_score
            if combined_score > 0:
                scored.append((template, combined_score, [*matched_brands, *matched_keywords]))
        if scored:
            max_score = max(score for _, score, _ in scored)
            threshold = max(0.35, max_score * 0.75)
            stage2_templates = [template for template, score, _ in scored if score >= threshold]
        else:
            stage2_fallback = True
            if strict_brand_filter and stage2_brands:
                stage2_templates = []
                stage2_fallback = False

    matches: list[MatchResult] = []
    has_brand_input = bool(stage2_brands)
    generic_brand_only = has_brand_input and all(is_generic_snow_brand(brand) for brand in stage2_brands)
    for template in stage2_templates:
        visual_score = visual_similarity(upload_hash, upload_hist, template)
        template_brand_score, matched_brands = brand_score(template, stage2_brands)
        text_score, matched_keywords = keyword_score(template, stage2_keywords)
        package_score = package_match_score(str(template.get("package_type", "")), package_type)
        active_weights = ranking_weights(
            has_brand_input,
            template_brand_score > 0,
            weights,
            generic_brand_only=generic_brand_only,
        )
        score = (
            (visual_score * active_weights["visual"])
            + (template_brand_score * active_weights["brand"])
            + (text_score * active_weights["text"])
        )
        score = max(0.0, min(1.0, score))
        matches.append(
            MatchResult(
                score=round(score, 6),
                product_code=template["product_code"],
                product_name=template["product_name"],
                package_type=template["package_type"],
                view=template["view"],
                image_path=template["image_path"],
                template_image_url=template_image_url(template["image_path"], template_images_dir),
                source_workbook=template["source_workbook"],
                sheet=template["sheet"],
                row=int(template["row"]),
                visual_score=round(visual_score, 6),
                brand_score=round(template_brand_score, 6),
                text_score=round(text_score, 6),
                package_score=round(package_score, 6),
                weights=active_weights,
                matched_keywords=[*matched_brands, *matched_keywords],
            )
        )

    sorted_matches = sorted(matches, key=lambda item: item.score, reverse=True)[:top_k]
    pipeline = MatchPipeline(
        stage1_package_type=package_type,
        stage1_count=len(stage1_templates),
        stage1_fallback=stage1_fallback,
        stage2_keywords=[*stage2_brands, *stage2_keywords],
        stage2_count=len(stage2_templates),
        stage2_fallback=stage2_fallback,
        stage3_count=len(sorted_matches),
    )
    return sorted_matches, pipeline
