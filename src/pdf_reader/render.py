"""仅渲染请求的 PDF 原页或局部区域，并缓存生成的 PNG。"""

import hashlib
import json
import math
import uuid
from pathlib import Path

import pymupdf

from .models import RenderResult


def render_pdf_page(
    pdf: Path,
    folder: Path,
    doc_id: str,
    page_number: int,
    scale: float,
    clip: tuple[float, float, float, float] | None,
) -> RenderResult:
    if not math.isfinite(scale) or not 0 < scale <= 4:
        raise ValueError("缩放倍率必须大于 0 且不超过 4")
    if clip is not None and (len(clip) != 4 or not all(math.isfinite(v) for v in clip)):
        raise ValueError("区域必须是四个有限的 PDF 点坐标")

    with pymupdf.open(str(pdf)) as document:
        if not 1 <= page_number <= len(document):
            raise ValueError(f"页码超出 PDF 范围：{page_number}（共 {len(document)} 页）")
        page = document[page_number - 1]
        area = page.rect
        if clip is not None:
            area = pymupdf.Rect(*clip)
            if area.is_empty or not page.rect.contains(area):
                raise ValueError(f"区域超出原始 PDF 第 {page_number} 页的边界")

        key = json.dumps([page_number, scale, clip], separators=(",", ":"))
        suffix = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        output = folder / f"page-{page_number:04d}-{suffix}.png"
        if output.is_file():
            try:
                image = pymupdf.Pixmap(str(output))
            except (RuntimeError, OSError) as exc:
                raise OSError(f"缓存的页面图片无法访问：{output}") from exc
            return RenderResult(doc_id, page_number, str(output), True, image.width, image.height, scale, clip)

        folder.mkdir(parents=True, exist_ok=True)
        image = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=area, alpha=False)
        temporary = folder / f"page-{page_number:04d}-{uuid.uuid4().hex}.tmp.png"
        try:
            image.save(str(temporary))
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        return RenderResult(doc_id, page_number, str(output), False, image.width, image.height, scale, clip)
