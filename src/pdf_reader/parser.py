"""只负责把 PDF 解析为带原始页码的 Markdown 页面。"""

import os
import threading
from pathlib import Path

import pymupdf
import pymupdf4llm

from .models import Page, ParseConfig


_CWD_LOCK = threading.Lock()


def parse_pdf(pdf: Path, asset_dir: Path, config: ParseConfig) -> list[Page]:
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise ValueError(f"找不到 PDF 文件或扩展名不是 .pdf：{pdf}")
    try:
        document = pymupdf.open(str(pdf))
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise ValueError(f"无法打开 PDF，文件可能已损坏：{pdf}") from exc

    with document:
        if not document.is_pdf:
            raise ValueError(f"文件内容不是 PDF：{pdf}")
        if document.needs_pass:
            raise ValueError(f"PDF 需要密码，暂不支持：{pdf}")

        options = {"page_chunks": True, "use_ocr": False}
        if config.extract_images:
            asset_dir.mkdir(parents=True, exist_ok=True)
            # 当前库将 image_path 同时用于落盘和 Markdown 链接。
            # 只在转换期间切换目录，并用锁避免并发转换相互影响。
            with _CWD_LOCK:
                previous_dir = Path.cwd()
                try:
                    os.chdir(asset_dir)
                    converted = pymupdf4llm.to_markdown(
                        document, write_images=True, image_path="images", **options
                    )
                finally:
                    os.chdir(previous_dir)
        else:
            converted = pymupdf4llm.to_markdown(document, **options)

    return [
        Page(number=int(item["metadata"]["page_number"]), markdown=item["text"])
        for item in converted
    ]
