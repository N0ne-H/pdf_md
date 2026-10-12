"""保留原来的单文件转换命令，内部复用 PDF Reader Core。"""

import argparse
from pathlib import Path

from pdf_reader import ReaderService


def main() -> None:
    parser = argparse.ArgumentParser(description="将 PDF 转换为 Markdown")
    parser.add_argument("pdf", type=Path, help="输入 PDF 文件路径")
    parser.add_argument("-o", "--output", type=Path, help="输出 Markdown 路径")
    args = parser.parse_args()

    output = args.output or Path(__file__).resolve().parent / "output" / f"{args.pdf.stem}.md"
    service = ReaderService(Path(__file__).resolve().parent / ".pdf_reader_cache")
    try:
        result = service.ingest(args.pdf)
        saved = service.export(result.document_id, output)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(1, f"错误：{exc}\n")
    print(f"转换完成：{saved}")


if __name__ == "__main__":
    main()
