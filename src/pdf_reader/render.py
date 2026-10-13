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
                image = pymupdf.Pixmap(output.read_bytes())
            except (RuntimeError, OSError, pymupdf.mupdf.FzErrorBase) as exc:
                raise OSError(f"缓存的页面图片无法访问：{output}") from exc
            return RenderResult(doc_id, page_number, str(output), True, image.width, image.height, scale, clip)

        folder.mkdir(parents=True, exist_ok=True)
        image = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=area, alpha=False)
        temporary = folder / f"page-{page_number:04d}-{uuid.uuid4().hex}.tmp.png"
        try:
            # 由 Python 写文件，使权限/占用错误成为 CLI 能处理的 OSError。
            with temporary.open("xb") as destination:
                destination.write(image.tobytes("png"))
            try:
                temporary.replace(output)
            except (PermissionError, FileExistsError) as publish_error:
                # Windows 读者可阻止替换；另一个请求已完成时安全复用它。
                if not output.is_file():
                    raise
                try:
                    cached = pymupdf.Pixmap(output.read_bytes())
                except (RuntimeError, OSError, pymupdf.mupdf.FzErrorBase):
                    raise publish_error
                if (cached.width, cached.height) != (image.width, image.height):
                    raise publish_error
                return RenderResult(
                    doc_id, page_number, str(output), True,
                    cached.width, cached.height, scale, clip,
                )
        except OSError as exc:
            raise OSError(
                f"页面图片写入失败：{output}；请检查目录写权限或文件占用，"
                f"沙箱拒绝时申请写入授权。原始错误：{exc}"
            ) from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                # 临时文件清理失败不能覆盖真正的写入错误。
                pass
        return RenderResult(doc_id, page_number, str(output), False, image.width, image.height, scale, clip)
