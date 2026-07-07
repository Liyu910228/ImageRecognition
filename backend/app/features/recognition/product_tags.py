from __future__ import annotations

import re
from typing import Any


BRAND_ALIASES: tuple[tuple[str, str], ...] = (
    ("雪花勇闯天涯 SuperX", "雪花勇闯天涯 SuperX"),
    ("雪花匠心营造", "雪花匠心营造"),
    ("雪花勇闯天涯", "雪花勇闯天涯"),
    ("夺命大乌苏", "夺命大乌苏"),
    ("新疆乌苏", "新疆乌苏"),
    ("雪花啤酒", "雪花"),
    ("雪花纯生", "雪花纯生"),
    ("纯生", "雪花纯生"),
    ("雪花脸谱", "雪花脸谱"),
    ("雪花经典", "雪花经典"),
    ("经典", "雪花经典"),
    ("雪花清爽", "雪花清爽"),
    ("清爽", "雪花清爽"),
    ("雪花冰纯", "雪花冰纯"),
    ("雪花晶尊", "雪花晶尊"),
    ("雪花精酿", "雪花精酿"),
    ("雪花Vine", "雪花Vine"),
    ("Heineken", "喜力"),
    ("AMSTEL", "红爵"),
    ("SuperX", "雪花勇闯天涯 SuperX"),
    ("勇闯天涯", "雪花勇闯天涯"),
    ("Kilkenny", "苦丁"),
    ("Tiger", "虎牌"),
    ("喜力", "喜力"),
    ("虎牌", "虎牌"),
    ("苦丁", "苦丁"),
    ("蓝剑", "蓝剑"),
    ("雪津", "雪津"),
    ("黑狮", "黑狮"),
    ("大乌苏", "大乌苏"),
    ("乌苏", "乌苏"),
    ("红爵", "红爵"),
    ("新三星", "新三星"),
    ("海拉尔", "海拉尔"),
    ("雪花", "雪花"),
)

DEFAULT_SNOW_BRANDS = (
    "雪花",
    "纯生",
    "勇闯天涯",
    "SuperX",
    "匠心营造",
    "脸谱",
    "经典",
    "清爽",
    "冰纯",
    "晶尊",
    "精酿",
    "Vine",
    "红爵",
    "新三星",
    "海拉尔",
    "喜力",
    "Heineken",
    "虎牌",
    "Tiger",
    "苦丁",
    "Kilkenny",
    "蓝剑",
    "雪津",
    "黑狮",
    "乌苏",
    "大乌苏",
    "夺命大乌苏",
    "新疆乌苏",
    "AMSTEL",
)

COMPETITOR_BRANDS = (
    "燕京",
    "燕京U8",
    "青岛",
    "百威",
    "哈尔滨",
    "哈啤",
    "珠江",
    "金星",
    "金威",
    "重庆啤酒",
    "山城",
)

UNSAFE_GATE_BRANDS = {
    "u",
    "u8",
    "8",
    "1",
    "beer",
    "啤酒",
    "产品",
    "图片",
    "瓶",
    "听",
    "箱",
    "纸箱",
}

CONTEXT_REQUIRED_GATE_BRANDS = {
    "纯生",
    "经典",
    "清爽",
    "冰纯",
    "晶尊",
    "精酿",
    "vine",
}

GENERIC_SNOW_BRANDS = {
    "雪花",
    "雪花啤酒",
}

GENERIC_TAGS = {
    "产品",
    "图片",
    "啤酒",
    "瓶",
    "听",
    "箱",
    "纸箱",
    "正面",
    "背面",
    "侧面",
    "立体图",
    "顶图",
    "底图",
}


def normalize_for_match(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def is_generic_snow_brand(value: object) -> bool:
    normalized = normalize_for_match(value)
    return normalized in {normalize_for_match(brand) for brand in GENERIC_SNOW_BRANDS}


def extract_product_tags(*values: object) -> dict[str, list[str]]:
    text = " ".join(str(value or "") for value in values if value is not None)
    normalized = normalize_for_match(text)
    brands = _unique(
        canonical
        for alias, canonical in BRAND_ALIASES
        if normalize_for_match(alias) in normalized
    )
    capacities = _unique(re.findall(r"\d+(?:\.\d+)?\s*(?:ml|ML|毫升)", text))
    degrees = _unique(re.findall(r"\d+(?:\.\d+)?\s*度", text))
    specs = _unique(
        item.replace("×", "*").replace("x", "*").replace("X", "*")
        for item in re.findall(r"\d+\s*[*×xX]\s*\d+", text)
    )
    packages = _unique(
        item
        for item in ["白瓶", "绿瓶", "棕瓶", "蓝瓶", "铝瓶", "塑料提手", "无纺布提手", "拉环盖", "纸箱", "塑膜", "卡纸"]
        if item in text
    )
    words = _unique(
        item
        for item in re.findall(r"[A-Za-z]+|[\u4e00-\u9fff]{2,}", text)
        if normalize_for_match(item) not in {normalize_for_match(tag) for tag in GENERIC_TAGS}
    )
    tags = _unique([*brands, *capacities, *degrees, *specs, *packages, *words])
    return {
        "brands": brands,
        "capacities": capacities,
        "degrees": degrees,
        "specs": specs,
        "packages": packages,
        "keywords": tags,
    }


def split_brand_config(value: object) -> list[str]:
    text = str(value or "")
    return _unique(item for item in re.split(r"[,，、\n\r\t ]+", text) if item.strip())


def sanitize_recognition_text(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"[\u4e00-\u9fffA-Za-z0-9]+[-—－]?\s*生动化检查[-—－]?[^\n\r,，;；]*", " ", text)
    text = re.sub(r"(手机时间|服务器时间)[:：]?.*", " ", text)
    text = re.sub(r"\d{8,}/[^\n\r]*", " ", text)
    text = re.sub(r"(黑龙江省|哈尔滨市|齐齐哈尔市|牡丹江市|佳木斯市|大庆市|鸡西市|双鸭山市|伊春市|七台河市|鹤岗市|黑河市|绥化市|大兴安岭|巴彦县)[^\n\r]*", " ", text)
    text = text.strip(" ,，;；/、\t\r\n")
    return text if re.search(r"[A-Za-z0-9\u4e00-\u9fff]", text) else ""


def has_competitor_brand(*values: object) -> bool:
    haystack = normalize_for_match(" ".join(str(value or "") for value in values))
    return any(normalize_for_match(brand) in haystack for brand in COMPETITOR_BRANDS)


def competitor_brand_matches(*values: object) -> list[str]:
    haystack = normalize_for_match(" ".join(str(value or "") for value in values))
    return _unique(brand for brand in COMPETITOR_BRANDS if normalize_for_match(brand) in haystack)


def is_weak_edge_product_evidence(*values: object) -> bool:
    text = normalize_for_match(" ".join(str(value or "") for value in values))
    if not text:
        return True
    weak_markers = ["小纸箱", "很小", "较小", "边缘", "角落", "左下角", "右下角", "远处", "模糊", "疑似", "无法识别", "未见"]
    vague_only = any(marker in text for marker in weak_markers)
    has_strong_product_signal = any(
        normalize_for_match(signal) in text
        for signal in [
            "雪花纯生",
            "勇闯天涯",
            "superx",
            "红爵",
            "amstel",
            "喜力",
            "heineken",
            "虎牌",
            "tiger",
            "乌苏",
            "瓶",
            "听",
            "500ml",
            "330ml",
            "8度",
            "10度",
            "1*12",
            "6*2",
        ]
    )
    return vague_only and not has_strong_product_signal


def snow_brand_matches(*values: object, snow_brands: list[str] | tuple[str, ...] | None = None) -> list[str]:
    configured_brands = list(snow_brands or DEFAULT_SNOW_BRANDS)
    haystack = normalize_for_match(" ".join(str(value or "") for value in values))
    competitor_matches = competitor_brand_matches(*values)
    matches: list[str] = []
    for brand in configured_brands:
        normalized = normalize_for_match(brand)
        if not _is_safe_gate_brand(brand):
            continue
        if normalized not in haystack:
            continue
        if competitor_matches and normalized in CONTEXT_REQUIRED_GATE_BRANDS and "雪花" not in haystack:
            continue
        matches.append(str(brand).strip())
    return _unique(matches)


def has_snow_brand(*values: object, snow_brands: list[str] | tuple[str, ...] | None = None) -> bool:
    return bool(snow_brand_matches(*values, snow_brands=snow_brands))


def infer_package_type(*values: object) -> str | None:
    text = "".join(str(value or "") for value in values)
    if any(item in text for item in ["纸箱", "整箱", "箱装", "箱"]):
        return "箱"
    if any(item in text for item in ["易拉罐", "罐", "听"]):
        return "听"
    if any(item in text for item in ["瓶", "白瓶", "绿瓶", "棕瓶", "蓝瓶", "铝瓶"]):
        return "瓶"
    return None


def template_tags(template: dict[str, Any]) -> dict[str, list[str]]:
    raw_tags = template.get("tags")
    if isinstance(raw_tags, dict):
        return {
            "brands": _as_list(raw_tags.get("brands")),
            "capacities": _as_list(raw_tags.get("capacities")),
            "degrees": _as_list(raw_tags.get("degrees")),
            "specs": _as_list(raw_tags.get("specs")),
            "packages": _as_list(raw_tags.get("packages")),
            "keywords": _as_list(raw_tags.get("keywords")),
        }
    return extract_product_tags(
        template.get("product_name", ""),
        template.get("product_code", ""),
        template.get("package_type", ""),
        template.get("view", ""),
    )


def _as_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        key = normalize_for_match(text)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _is_safe_gate_brand(value: object) -> bool:
    text = str(value or "").strip()
    normalized = normalize_for_match(text)
    if not normalized or normalized in UNSAFE_GATE_BRANDS:
        return False
    if normalized.isdigit():
        return False
    if re.fullmatch(r"[a-z]", normalized):
        return False
    if re.fullmatch(r"[a-z]?\d+[a-z]?", normalized):
        return False
    return True
