"""将单个可提取文字的 PDF 转换为 Markdown。"""

import argparse
import os
from pathlib import Path

import pymupdf
import pymupdf4llm


PROJECT_DIR = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="将 PDF 转换为 Markdown")
    parser.add_argument("pdf", type=Path, help="输入 PDF 文件路径")
    parser.add_argument("-o", "--output", type=Path, help="输出 Markdown 路径")
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    if not pdf.is_file():
        parser.error(f"找不到 PDF 文件：{args.pdf}")
    if pdf.suffix.lower() != ".pdf":
        parser.error(f"输入文件不是 .pdf：{args.pdf}")

    output = (args.output or PROJECT_DIR / "output" / f"{pdf.stem}.md").resolve()
    if output.suffix.lower() != ".md":
        parser.error(f"输出文件必须使用 .md 扩展名：{output}")

    try:
        document = pymupdf.open(pdf)
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        parser.exit(1, f"无法打开 PDF，文件可能已损坏或格式不正确：{exc}\n")

    with document:
        if not document.is_pdf:
            parser.exit(1, f"文件内容不是 PDF：{pdf}\n")
        if document.needs_pass:
            parser.exit(1, f"PDF 需要密码，暂不支持：{pdf}\n")

        # 图片放在 Markdown 文件旁边，方便移动整个输出文件夹。
        output.parent.mkdir(parents=True, exist_ok=True)
        previous_dir = Path.cwd()
        try:
            # 库把 image_path 同时当成保存路径和 Markdown 链接，
            # 在输出目录运行可直接得到 images/... 相对链接。
            os.chdir(output.parent)
            markdown = pymupdf4llm.to_markdown(
                document,
                write_images=True,
                image_path="images",
                use_ocr=False,
            )
        finally:
            os.chdir(previous_dir)

    output.write_text(markdown, encoding="utf-8")
    print(f"转换完成：{output}")


if __name__ == "__main__":
    main()
