from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


def crop_bottom_watermark(image_path: Path) -> Path:
    """Crop the white/red visit-info footer before visual recognition.

    CRM visit photos often append a white footer with red inspection text below the real
    image. The model must not use that text as product evidence.
    """
    with Image.open(image_path) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        width, height = image.size
        if width < 200 or height < 300:
            return image_path

        footer_top = _detect_footer_top(image)
        if footer_top is None or footer_top < int(height * 0.45):
            return image_path

        target = image_path.with_name(f"{image_path.stem}_cropped{image_path.suffix}")
        image.crop((0, 0, width, footer_top)).save(target)
        return target


def _detect_footer_top(image: Image.Image) -> int | None:
    width, height = image.size
    pixels = image.load()
    start_row = int(height * 0.62)
    row_step = max(1, height // 900)
    sample_step = max(1, width // 240)

    row_stats: list[tuple[int, float, float]] = []
    for y in range(start_row, height, row_step):
        total = 0
        red = 0
        light = 0
        for x in range(0, width, sample_step):
            r, g, b = pixels[x, y]
            total += 1
            if r > 135 and g < 145 and b < 145 and r > g * 1.18 and r > b * 1.18:
                red += 1
            if r > 198 and g > 198 and b > 198:
                light += 1
        if total:
            row_stats.append((y, light / total, red / total))

    if not row_stats:
        return None

    footer_top = height
    gap_rows = 0
    for y, light_ratio, _ in reversed(row_stats):
        if light_ratio >= 0.54:
            footer_top = y
            gap_rows = 0
            continue
        gap_rows += 1
        if gap_rows >= 3:
            break

    footer_height = height - footer_top
    if footer_height < max(int(height * 0.08), 80):
        return None

    footer_rows = [(y, light_ratio, red_ratio) for y, light_ratio, red_ratio in row_stats if y >= footer_top]
    if not footer_rows:
        return None
    red_rows = [y for y, light_ratio, red_ratio in footer_rows if light_ratio >= 0.45 and red_ratio >= 0.003]
    if len(red_rows) < 2:
        return None

    return max(0, footer_top - row_step * 2)
