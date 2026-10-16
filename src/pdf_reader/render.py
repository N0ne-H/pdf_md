"""仅渲染请求的 PDF 原页或局部区域，并缓存生成的 PNG。"""

import hashlib
import json
import math
import os
import uuid
from pathlib import Path

import pymupdf

from .models import RenderResult


def _read_png(path):
    if os.name != "nt":
        return path.read_bytes()
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    # CRT open 不共享 DELETE，会与尚持有 DELETE 权限的发布句柄冲突。
    # 只请求读权限；共享读/写/删除不绕过 ACL，也不修改已发布的 PNG。
    handle = kernel.CreateFileW(str(path), 0x80000000, 7, None, 3, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except OSError:
        kernel.CloseHandle(handle)
        raise
    # open_osfhandle 接管句柄，stream 关闭时一起释放。
    with os.fdopen(descriptor, "rb") as stream:
        return stream.read()


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
                image = pymupdf.Pixmap(_read_png(output))
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
                # Windows 下首个完整 PNG 胜出；不替换已发布文件，避免与读者争抢删除共享权。
                if os.name == "nt":
                    temporary.rename(output)
                else:
                    temporary.replace(output)
            except (PermissionError, FileExistsError) as publish_error:
                # 另一个请求已完成同一目标时，校验并复用胜出文件。
                if not output.is_file():
                    raise
                try:
                    cached = pymupdf.Pixmap(_read_png(output))
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
