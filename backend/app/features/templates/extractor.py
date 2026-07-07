from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from app.features.recognition.product_tags import extract_product_tags


NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_ETC = "http://www.wps.cn/officeDocument/2017/etCustomData"
NS_XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

DISPIMG_RE = re.compile(r'DISPIMG\(&quot;([^&]+)&quot;|DISPIMG\("([^"]+)"')
CELL_REF_RE = re.compile(r"([A-Z]+)([0-9]+)")

PRODUCT_CODE_HEADERS = ("产品编码", "ERP编码", "编码")
PRODUCT_NAME_HEADERS = ("产品名称", "特征码说明", "品名")
PACKAGE_HEADERS = ("瓶、听、箱", "瓶听箱", "包装形式", "包装类型", "包装")
IMAGE_HEADER_KEYWORDS = ("正面图", "背面图", "侧面一图", "侧面二图", "顶图", "底图", "立体图")


@dataclass(frozen=True)
class CellImage:
    image_id: str
    rel_id: str
    target: str
    description: str | None = None


def col_to_index(col: str) -> int:
    value = 0
    for char in col:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value


def safe_name(value: object, max_len: int = 80) -> str:
    text = str(value or "").strip()
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", text)
    text = re.sub(r"_+", "_", text).strip("._")
    return (text or "blank")[:max_len]


def normalize_header(value: object) -> str:
    return re.sub(r"[\s,，、/\\：:（）()]+", "", str(value or "").strip()).lower()


def normalize_package_type(value: object, product_name: object = "") -> str:
    text = str(value or "").strip()
    if "箱" in text:
        return "箱"
    if "听" in text or "罐" in text:
        return "听"
    if "瓶" in text:
        return "瓶"
    fallback = str(product_name or "")
    if "纸箱" in fallback or "箱" in fallback:
        return "箱"
    if "听" in fallback or "罐" in fallback:
        return "听"
    if "瓶" in fallback:
        return "瓶"
    return text


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall(f"{{{NS_MAIN}}}si"):
        texts = [node.text or "" for node in si.findall(f".//{{{NS_MAIN}}}t")]
        strings.append("".join(texts))
    return strings


def read_sheet_names(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    root = ET.fromstring(zf.read("xl/workbook.xml"))
    sheets = []
    for idx, sheet in enumerate(root.findall(f".//{{{NS_MAIN}}}sheet"), start=1):
        sheets.append((sheet.attrib.get("name", f"Sheet{idx}"), f"xl/worksheets/sheet{idx}.xml"))
    return sheets


def read_cell_images(zf: zipfile.ZipFile) -> dict[str, CellImage]:
    names = set(zf.namelist())
    if "xl/cellimages.xml" not in names or "xl/_rels/cellimages.xml.rels" not in names:
        return {}

    rel_root = ET.fromstring(zf.read("xl/_rels/cellimages.xml.rels"))
    rel_targets = {
        rel.attrib["Id"]: _resolve_target("xl/cellimages.xml", rel.attrib["Target"])
        for rel in rel_root.findall(f"{{{NS_REL}}}Relationship")
    }

    root = ET.fromstring(zf.read("xl/cellimages.xml"))
    image_map: dict[str, CellImage] = {}
    for cell_image in root.findall(f"{{{NS_ETC}}}cellImage"):
        pic = cell_image.find(f"{{{NS_XDR}}}pic")
        if pic is None:
            continue
        c_nv_pr = pic.find(f".//{{{NS_XDR}}}cNvPr")
        blip = pic.find(f".//{{{NS_A}}}blip")
        if c_nv_pr is None or blip is None:
            continue
        image_id = c_nv_pr.attrib.get("name")
        rel_id = blip.attrib.get(f"{{{NS_OFFICE_REL}}}embed")
        if not image_id or not rel_id or rel_id not in rel_targets:
            continue
        image_map[image_id] = CellImage(
            image_id=image_id,
            rel_id=rel_id,
            target=rel_targets[rel_id],
            description=c_nv_pr.attrib.get("descr"),
        )
    return image_map


def read_sheet_drawing_images(zf: zipfile.ZipFile, sheet_path: str) -> dict[tuple[int, int], list[CellImage]]:
    rel_path = sheet_path.replace("xl/worksheets/", "xl/worksheets/_rels/") + ".rels"
    if rel_path not in zf.namelist():
        return {}
    rel_root = ET.fromstring(zf.read(rel_path))
    drawing_paths = [
        _resolve_target(sheet_path, rel.attrib.get("Target", ""))
        for rel in rel_root.findall(f"{{{NS_REL}}}Relationship")
        if rel.attrib.get("Type", "").endswith("/drawing")
    ]

    anchored: dict[tuple[int, int], list[CellImage]] = {}
    for drawing_path in drawing_paths:
        if drawing_path not in zf.namelist():
            continue
        drawing_rels = _read_relationship_targets(zf, drawing_path)
        root = ET.fromstring(zf.read(drawing_path))
        for anchor in root:
            marker = anchor.find(f"{{{NS_XDR}}}from")
            blip = anchor.find(f".//{{{NS_A}}}blip")
            if marker is None or blip is None:
                continue
            row_node = marker.find(f"{{{NS_XDR}}}row")
            col_node = marker.find(f"{{{NS_XDR}}}col")
            rel_id = blip.attrib.get(f"{{{NS_OFFICE_REL}}}embed")
            if row_node is None or col_node is None or not rel_id or rel_id not in drawing_rels:
                continue
            row = int(row_node.text or "0") + 1
            col = int(col_node.text or "0") + 1
            image = CellImage(image_id=f"{row}_{col}_{rel_id}", rel_id=rel_id, target=drawing_rels[rel_id])
            anchored.setdefault((row, col), []).append(image)
    return anchored


def _read_relationship_targets(zf: zipfile.ZipFile, part_path: str) -> dict[str, str]:
    folder, filename = part_path.rsplit("/", 1)
    rel_path = f"{folder}/_rels/{filename}.rels"
    if rel_path not in zf.namelist():
        return {}
    root = ET.fromstring(zf.read(rel_path))
    return {
        rel.attrib["Id"]: _resolve_target(part_path, rel.attrib.get("Target", ""))
        for rel in root.findall(f"{{{NS_REL}}}Relationship")
    }


def _resolve_target(base_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    base_dir = Path(base_part).parent
    parts: list[str] = []
    for part in (base_dir / target).as_posix().split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part and part != ".":
            parts.append(part)
    return "/".join(parts)


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    formula = cell.find(f"{{{NS_MAIN}}}f")
    if formula is not None and formula.text:
        return formula.text

    value = cell.find(f"{{{NS_MAIN}}}v")
    if value is None or value.text is None:
        inline = cell.find(f".//{{{NS_MAIN}}}t")
        return inline.text if inline is not None and inline.text else ""

    if cell_type == "s":
        index = int(value.text)
        return shared_strings[index] if 0 <= index < len(shared_strings) else value.text
    return value.text


def parse_sheet_rows(zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> tuple[list[dict[str, Any]], dict[int, str]]:
    root = ET.fromstring(zf.read(sheet_path))
    rows: dict[int, dict[int, str]] = {}
    for row in root.findall(f".//{{{NS_MAIN}}}row"):
        row_num = int(row.attrib["r"])
        row_data: dict[int, str] = {}
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            ref = cell.attrib.get("r", "")
            match = CELL_REF_RE.fullmatch(ref)
            if not match:
                continue
            row_data[col_to_index(match.group(1))] = cell_value(cell, shared_strings)
        rows[row_num] = row_data

    if not rows:
        return [], {}

    header_row = rows[min(rows)]
    max_col = max(header_row) if header_row else 0
    headers_by_col = {col: header_row.get(col, f"Column{col}") for col in range(1, max_col + 1)}
    records: list[dict[str, Any]] = []
    for row_num in sorted(k for k in rows if k != min(rows)):
        record: dict[str, Any] = {"__row__": str(row_num), "__cells__": rows[row_num]}
        row_data = rows[row_num]
        for col, header in headers_by_col.items():
            record[header or f"Column{col}"] = row_data.get(col, "")
        if any(value for key, value in record.items() if not key.startswith("__")):
            records.append(record)
    return records, headers_by_col


def find_image_id(value: str) -> str | None:
    match = DISPIMG_RE.search(value or "")
    if not match:
        return None
    return match.group(1) or match.group(2)


def extract_workbooks(workbook_paths: Iterable[Path], output_dir: Path) -> list[dict[str, Any]]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "images").mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for workbook_path in workbook_paths:
        records.extend(extract_workbook(workbook_path, output_dir))

    write_outputs(records, output_dir)
    return records


def extract_workbook(workbook_path: Path, output_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    workbook_slug = safe_name(workbook_path.stem, 60)

    with zipfile.ZipFile(workbook_path) as zf:
        shared_strings = read_shared_strings(zf)
        cell_images = read_cell_images(zf)
        for sheet_name, sheet_path in read_sheet_names(zf):
            if sheet_path not in zf.namelist():
                continue
            rows, headers_by_col = parse_sheet_rows(zf, sheet_path, shared_strings)
            drawing_images = read_sheet_drawing_images(zf, sheet_path)
            for row in rows:
                product_code = get_field(row, PRODUCT_CODE_HEADERS)
                product_name = get_field(row, PRODUCT_NAME_HEADERS)
                if not product_code and not product_name:
                    continue
                package_type = normalize_package_type(get_field(row, PACKAGE_HEADERS), product_name)
                images: dict[str, str] = {}

                for header, value in row.items():
                    if header.startswith("__"):
                        continue
                    if not is_image_header(header):
                        continue
                    image_id = find_image_id(str(value))
                    if not image_id or image_id not in cell_images:
                        continue
                    images[header] = copy_image(
                        zf,
                        cell_images[image_id],
                        output_dir,
                        workbook_slug,
                        row["__row__"],
                        product_code,
                        header,
                    )

                row_number = int(row["__row__"])
                for (image_row, image_col), anchored_images in drawing_images.items():
                    if image_row != row_number:
                        continue
                    header = headers_by_col.get(image_col, f"Column{image_col}")
                    if not is_image_header(header):
                        continue
                    for index, anchored_image in enumerate(anchored_images, start=1):
                        view_name = header if len(anchored_images) == 1 else f"{header}{index}"
                        images[view_name] = copy_image(
                            zf,
                            anchored_image,
                            output_dir,
                            workbook_slug,
                            row["__row__"],
                            product_code,
                            view_name,
                        )

                if images:
                    records.append(
                        {
                            "source_workbook": str(workbook_path),
                            "sheet": sheet_name,
                            "row": int(row["__row__"]),
                            "product_code": product_code,
                            "product_name": product_name,
                            "package_type": package_type,
                            "tags": extract_product_tags(product_name, product_code, package_type),
                            "images": images,
                        }
                    )
    return records


def get_field(row: dict[str, Any], candidates: tuple[str, ...]) -> str:
    normalized_candidates = {normalize_header(item) for item in candidates}
    for key, value in row.items():
        if key.startswith("__"):
            continue
        if normalize_header(key) in normalized_candidates:
            return str(value or "").strip()
    return ""


def is_image_header(value: object) -> bool:
    text = str(value or "").strip()
    if not text or "DISPIMG" in text.upper():
        return False
    normalized = normalize_header(text)
    return any(normalize_header(keyword) in normalized for keyword in IMAGE_HEADER_KEYWORDS)


def copy_image(
    zf: zipfile.ZipFile,
    cell_image: CellImage,
    output_dir: Path,
    workbook_slug: str,
    row_number: object,
    product_code: object,
    header: object,
) -> str:
    source_name = cell_image.target
    ext = Path(source_name).suffix.lower() or ".jpg"
    filename = f"{workbook_slug}_row{row_number}_{safe_name(product_code, 32)}_{safe_name(header, 20)}{ext}"
    dest = output_dir / "images" / filename
    with zf.open(source_name) as src, dest.open("wb") as out:
        shutil.copyfileobj(src, out)
    return str(dest)


def write_outputs(records: list[dict[str, Any]], output_dir: Path) -> None:
    (output_dir / "manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (output_dir / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "source_workbook",
                "sheet",
                "row",
                "product_code",
                "product_name",
                "package_type",
                "view",
                "image_path",
            ]
        )
        for record in records:
            for view, image_path in dict(record["images"]).items():
                writer.writerow(
                    [
                        record["source_workbook"],
                        record["sheet"],
                        record["row"],
                        record["product_code"],
                        record["product_name"],
                        record["package_type"],
                        view,
                        image_path,
                    ]
                )
