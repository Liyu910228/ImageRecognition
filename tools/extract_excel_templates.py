#!/usr/bin/env python3
"""Extract WPS/Excel DISPIMG product templates from workbook files.

The source workbooks store cell images as formulas such as:
    =DISPIMG("ID_...", 1)

This script resolves those IDs through xl/cellimages.xml and writes:
  - one image file per product/view template
  - manifest.json with product code, name, package type and image paths
  - manifest.csv for quick inspection
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_ETC = "http://www.wps.cn/officeDocument/2017/etCustomData"
NS_XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

DISPIMG_RE = re.compile(r'DISPIMG\(&quot;([^&]+)&quot;|DISPIMG\("([^"]+)"')
CELL_REF_RE = re.compile(r"([A-Z]+)([0-9]+)")


@dataclass(frozen=True)
class CellImage:
    image_id: str
    rel_id: str
    target: str
    description: str | None


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
        rel.attrib["Id"]: "xl/" + rel.attrib["Target"].lstrip("/")
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


def parse_sheet_rows(zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> list[dict[str, str]]:
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
        return []

    header_row = rows[min(rows)]
    max_col = max(header_row) if header_row else 0
    headers = [header_row.get(col, f"Column{col}") for col in range(1, max_col + 1)]

    records: list[dict[str, str]] = []
    for row_num in sorted(k for k in rows if k != min(rows)):
        record = {"__row__": str(row_num)}
        row_data = rows[row_num]
        for idx, header in enumerate(headers, start=1):
            record[header or f"Column{idx}"] = row_data.get(idx, "")
        if any(value for key, value in record.items() if key != "__row__"):
            records.append(record)
    return records


def find_image_id(value: str) -> str | None:
    match = DISPIMG_RE.search(value or "")
    if not match:
        return None
    return match.group(1) or match.group(2)


def iter_workbooks(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(p for p in path.glob("*.xlsx") if not p.name.startswith("~$"))
        elif path.suffix.lower() == ".xlsx" and not path.name.startswith("~$"):
            yield path


def extract_workbook(workbook_path: Path, output_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    workbook_slug = safe_name(workbook_path.stem, 60)

    with zipfile.ZipFile(workbook_path) as zf:
        shared_strings = read_shared_strings(zf)
        cell_images = read_cell_images(zf)
        sheet_names = read_sheet_names(zf)

        for sheet_name, sheet_path in sheet_names:
            if sheet_path not in zf.namelist():
                continue
            rows = parse_sheet_rows(zf, sheet_path, shared_strings)
            for row in rows:
                product_code = row.get("产品编码", "")
                product_name = row.get("产品名称", "")
                package_type = row.get("瓶、听、箱", row.get("瓶听箱", ""))

                images: dict[str, str] = {}
                for header, value in row.items():
                    image_id = find_image_id(value)
                    if not image_id or image_id not in cell_images:
                        continue
                    cell_image = cell_images[image_id]
                    source_name = cell_image.target
                    ext = Path(source_name).suffix.lower() or ".jpg"
                    filename = (
                        f"{workbook_slug}_row{row['__row__']}_"
                        f"{safe_name(product_code, 32)}_{safe_name(header, 20)}{ext}"
                    )
                    dest = output_dir / "images" / filename
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(source_name) as src, dest.open("wb") as out:
                        shutil.copyfileobj(src, out)
                    images[header] = str(dest.as_posix())

                if images:
                    records.append(
                        {
                            "source_workbook": str(workbook_path),
                            "sheet": sheet_name,
                            "row": int(row["__row__"]),
                            "product_code": product_code,
                            "product_name": product_name,
                            "package_type": package_type,
                            "images": images,
                        }
                    )
    return records


def write_outputs(records: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_json = output_dir / "manifest.json"
    manifest_csv = output_dir / "manifest.csv"

    manifest_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    with manifest_csv.open("w", encoding="utf-8-sig", newline="") as csv_file:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract product image templates from Excel files.")
    parser.add_argument("inputs", nargs="*", type=Path, default=[Path.cwd()])
    parser.add_argument("--output", type=Path, default=Path("outputs/product_templates"))
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    for workbook_path in iter_workbooks(args.inputs):
        print(f"Extracting {workbook_path}")
        records.extend(extract_workbook(workbook_path, args.output))

    write_outputs(records, args.output)
    image_count = sum(len(record["images"]) for record in records)
    print(f"Done. Products: {len(records)}, images: {image_count}")
    print(f"Manifest: {args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
