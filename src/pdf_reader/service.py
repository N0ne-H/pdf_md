"""供 CLI、未来 MCP Adapter 和 Skill 共用的业务入口。"""

import re
import shutil
from importlib.metadata import version
from pathlib import Path

from .cache import CacheStore, document_id, sha256_file
from .chunking import chunk_pages
from .models import Chunk, Document, Heading, IngestResult, ParseConfig, SearchResult
from .parser import parse_pdf
from .search import search_chunks
from .tokens import estimate_tokens


class ReaderService:
    def __init__(self, cache_dir: Path):
        self.cache = CacheStore(cache_dir)

    def ingest(self, pdf_path: Path, config: ParseConfig | None = None) -> IngestResult:
        pdf = Path(pdf_path).resolve()
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            raise ValueError(f"找不到 PDF 文件或扩展名不是 .pdf：{pdf_path}")
        config = config or ParseConfig()
        source_sha256 = sha256_file(pdf)
        converter_version = version("pymupdf4llm")
        doc_id = document_id(source_sha256, config, converter_version)

        try:
            document = self.cache.load(doc_id)
            cache_hit = True
        except FileNotFoundError:
            pages = parse_pdf(pdf, self.cache.folder(doc_id), config)
            headings, chunks = chunk_pages(doc_id, pages, config.chunk_size)
            document = Document(
                id=doc_id,
                source_sha256=source_sha256,
                source_name=pdf.name,
                converter_version=converter_version,
                config=config,
                pages=pages,
                headings=headings,
                chunks=chunks,
            )
            self.cache.save(document)
            cache_hit = False

        return IngestResult(
            document_id=doc_id,
            cache_hit=cache_hit,
            page_count=len(document.pages),
            chunk_count=len(document.chunks),
            estimated_full_tokens=estimate_tokens(document.full_markdown()),
        )

    def outline(self, doc_id: str) -> list[Heading]:
        return self.cache.load(doc_id).headings

    def search(
        self, doc_id: str, query: str, top_k: int = 5, max_chars: int = 2000
    ) -> SearchResult:
        return search_chunks(self.cache.load(doc_id), query, top_k, max_chars)

    def read(self, doc_id: str, chunk_id: str) -> Chunk:
        for chunk in self.cache.load(doc_id).chunks:
            if chunk.id == chunk_id:
                return chunk
        raise KeyError(f"文档 {doc_id} 中找不到块 {chunk_id}")

    def export(self, doc_id: str, output_path: Path) -> Path:
        document = self.cache.load(doc_id)
        output = Path(output_path).resolve()
        if output.suffix.lower() != ".md":
            raise ValueError(f"导出路径必须以 .md 结尾：{output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        markdown = document.full_markdown()

        images = self.cache.folder(doc_id) / "images"
        if images.is_dir():
            # 每个文档的图片使用独立子目录，避免同名 PDF 互相覆盖。
            relative_dir = f"images/{doc_id[:12]}"
            shutil.copytree(images, output.parent / relative_dir, dirs_exist_ok=True)
            markdown = re.sub(r"(?<=\]\()images/", relative_dir + "/", markdown)

        output.write_text(markdown, encoding="utf-8")
        return output
