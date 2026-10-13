"""仅处理命令行参数和 JSON 输出，不包含 PDF 业务逻辑。"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .models import ParseConfig
from .service import ReaderService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdf-reader", description="本地 PDF 智能阅读")
    parser.add_argument("--cache-dir", type=Path, default=Path(".pdf_reader_cache"))
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest", help="解析 PDF 并写入本地缓存")
    ingest.add_argument("pdf", type=Path)
    ingest.add_argument("--chunk-size", type=int, default=1200)
    ingest.add_argument("--no-images", action="store_true")

    outline = commands.add_parser("outline", help="查看标题及原始页码")
    outline.add_argument("document_id")

    search = commands.add_parser("search", help="只返回匹配片段")
    search.add_argument("document_id")
    search.add_argument("query")
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--max-chars", type=int, default=2000)

    read = commands.add_parser("read", help="按块 ID 读取单个片段")
    read.add_argument("document_id")
    read.add_argument("chunk_id")

    render = commands.add_parser("render-page", help="按原始页码渲染单页或局部 PNG")
    render.add_argument("document_id")
    render.add_argument("page_number", type=int)
    render.add_argument("--scale", type=float, default=2.0)
    render.add_argument("--clip", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    render.add_argument("--pdf", type=Path, help="旧缓存或原路径失效时提供原始 PDF")

    export = commands.add_parser("export", help="导出完整 Markdown")
    export.add_argument("document_id")
    export.add_argument("-o", "--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    # Windows 终端可能默认使用 GBK，而 PDF 内容包含 GBK 无法表示的字符。
    # 统一用 UTF-8 输出 JSON，避免检索成功后在打印阶段报错。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    service = ReaderService(args.cache_dir)
    try:
        if args.command == "ingest":
            result = service.ingest(
                args.pdf,
                ParseConfig(chunk_size=args.chunk_size, extract_images=not args.no_images),
            )
        elif args.command == "outline":
            result = {"document_id": args.document_id, "headings": service.outline(args.document_id)}
        elif args.command == "search":
            result = service.search(args.document_id, args.query, args.top_k, args.max_chars)
        elif args.command == "read":
            result = service.read(args.document_id, args.chunk_id)
        elif args.command == "render-page":
            result = service.render_page(
                args.document_id, args.page_number, scale=args.scale,
                clip=tuple(args.clip) if args.clip else None, pdf_path=args.pdf,
            )
        else:
            result = {"output": str(service.export(args.document_id, args.output))}
    except (ValueError, FileNotFoundError, KeyError, OSError) as exc:
        parser.exit(1, f"错误：{exc}\n")

    # dataclass 先转为普通字典，便于 CLI 和后续 Adapter 使用 JSON。
    if not isinstance(result, dict):
        result = asdict(result)
    else:
        result = {
            key: [asdict(item) for item in value] if key == "headings" else value
            for key, value in result.items()
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
