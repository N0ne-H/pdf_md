"""仅处理命令行参数和 JSON 输出，不包含 PDF 业务逻辑。"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .models import ParseConfig
from .reading import MODES, ReadingTracker
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

    for command in (search, read, render):
        command.add_argument("--reading-record", type=Path, help="成功输出后记录到该阅读任务")

    chunks = commands.add_parser("chunks", help="分页返回片段元数据，不返回 Markdown")
    chunks.add_argument("document_id")
    chunks.add_argument("--offset", type=int, default=0)
    chunks.add_argument("--limit", type=int, default=50)

    start = commands.add_parser("reading-start", help="创建独立阅读任务与模式计划")
    start.add_argument("document_id")
    start.add_argument("--mode", choices=MODES, default="standard")
    start.add_argument("--record", type=Path, help="阅读日志路径；默认存当前工作区 .pdf_reader_readings")
    batch = commands.add_parser("reading-next", help="返回下一批内容并记录成功输出")
    batch.add_argument("record", type=Path)
    batch.add_argument("--max-chunks", type=int, default=5)
    batch.add_argument("--max-chars", type=int, default=6000)
    status = commands.add_parser("reading-status", help="根据事件计算真实返回覆盖和未读内容")
    status.add_argument("record", type=Path)
    status.add_argument("--details", action="store_true", help="返回完整未读元数据与图像回执")
    gap = commands.add_parser("reading-gap", help="记录外部截断或其他未覆盖原因")
    gap.add_argument("record", type=Path)
    gap.add_argument("chunk_id")
    gap.add_argument("--reason", required=True)
    visual = commands.add_parser("reading-visual", help="提交外部图片查看回执或未查看原因")
    visual.add_argument("record", type=Path)
    visual.add_argument("asset_id")
    visual_source = visual.add_mutually_exclusive_group(required=True)
    visual_source.add_argument("--image", type=Path)
    visual_source.add_argument("--reason")
    visual.add_argument("--evidence", help="实际图像工具结果引用；Core 不认证外部调用")
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
    reading = ReadingTracker(service.cache)
    record = getattr(args, "reading_record", None)
    event = None
    try:
        if record is not None:
            reading.load(record, args.document_id)
        if args.command == "ingest":
            result = service.ingest(
                args.pdf,
                ParseConfig(chunk_size=args.chunk_size, extract_images=not args.no_images),
            )
        elif args.command == "outline":
            result = {"document_id": args.document_id, "headings": service.outline(args.document_id)}
        elif args.command == "search":
            result = service.search(args.document_id, args.query, args.top_k, args.max_chars)
            event = {"operation": "search", "located": [hit.chunk_id for hit in result.hits],
                     "truncated": [hit.chunk_id for hit in result.hits if hit.truncated]}
        elif args.command == "read":
            result = service.read(args.document_id, args.chunk_id)
            event = {"operation": "read", "located": [result.id], "full": [result.id],
                     "returned_characters": len(result.markdown)}
        elif args.command == "render-page":
            result = service.render_page(
                args.document_id, args.page_number, scale=args.scale,
                clip=tuple(args.clip) if args.clip else None, pdf_path=args.pdf,
            )
            event = {"operation": "render", "page_number": result.page_number,
                     "image_path": result.image_path, "clip": result.clip}
        elif args.command == "chunks":
            result = reading.catalog(args.document_id, args.offset, args.limit)
        elif args.command == "reading-start":
            result = reading.start(args.document_id, args.mode, args.record)
        elif args.command == "reading-next":
            record = args.record
            result, event = reading.next_batch(record, args.max_chunks, args.max_chars)
        elif args.command == "reading-status":
            result = reading.status(args.record, details=args.details)
        elif args.command == "reading-gap":
            record = args.record
            event = reading.gap(record, args.chunk_id, args.reason)
            result = event
        elif args.command == "reading-visual":
            record = args.record
            event = reading.visual(record, args.asset_id, args.image, args.evidence, args.reason)
            result = event
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
    # 先成功输出，再提交返回事件；输出失败不能虚增完整阅读计数。
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if record is not None and event is not None:
        try:
            reading.record(record, event)
        except (ValueError, FileNotFoundError, OSError) as exc:
            parser.exit(1, f"错误：内容已输出，但阅读记录未保存：{exc}\n")
