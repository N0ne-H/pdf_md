"""第一阶段：真实 PDF 解析与 Core/CLI 行为测试。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pymupdf
import pytest

from pdf_reader import ParseConfig, ReaderService
from pdf_reader.cache import CacheStore
from pdf_reader.chunking import chunk_pages
from pdf_reader.models import Chunk, Document, Heading, Page
from pdf_reader.parser import parse_pdf
from pdf_reader.search import search_chunks


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "sample.pdf"
    document = pymupdf.open()
    first = document.new_page()
    first.insert_text((72, 72), "Sample Title", fontsize=20)
    first.insert_text((72, 110), "Alpha content on page one.", fontsize=11)

    # 真实图片和表格覆盖转换器的两种常见版面元素。
    for x in (72, 192, 312):
        first.draw_line((x, 150), (x, 210))
    for y in (150, 180, 210):
        first.draw_line((72, y), (312, y))
    for x, y, text in (
        (78, 170, "Name"), (198, 170, "Value"),
        (78, 200, "Alpha"), (198, 200, "42"),
    ):
        first.insert_text((x, y), text, fontsize=11)
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 80), False)
    pixmap.clear_with(0xFF0000)
    first.insert_image(pymupdf.Rect(72, 250, 272, 380), pixmap=pixmap)

    second = document.new_page()
    second.insert_text((72, 72), "Second Section", fontsize=18)
    second.insert_text((72, 110), "Beta content on page two.", fontsize=11)
    document.save(pdf)
    document.close()
    return pdf


def test_parser_preserves_pdf_page_numbers_and_images(sample_pdf: Path, tmp_path: Path):
    asset_dir = tmp_path / "cache assets"
    pages = parse_pdf(sample_pdf, asset_dir, ParseConfig())
    assert [page.number for page in pages] == [1, 2]
    assert "Alpha content" in pages[0].markdown
    assert "Beta content" in pages[1].markdown
    assert "|" in pages[0].markdown  # 表格由转换器输出为 Markdown。
    assert list((asset_dir / "images").glob("*.png"))


def test_chunking_keeps_section_and_page():
    pages = [
        Page(1, "# 第一章\n\n第一段。\n\n" + "长内容" * 70),
        Page(2, "第二页内容。\n\n## 小节\n\n关键词在这里。"),
    ]
    headings, chunks = chunk_pages("a" * 64, pages, limit=100)
    assert [(heading.title, heading.page_number) for heading in headings] == [
        ("第一章", 1), ("小节", 2)
    ]
    assert all(len(chunk.markdown) <= 100 for chunk in chunks)
    assert all(chunk.page_number == 1 for chunk in chunks if "长内容" in chunk.markdown)
    assert any(chunk.section == "第一章 / 小节" and chunk.page_number == 2 for chunk in chunks)

    # 标题从三级跳回二级时，应替换子章节，而不是继续嵌套。
    _, skipped = chunk_pages(
        "a" * 64,
        [Page(1, "# 主章\n\n### 三级\n\n内容一\n\n## 二级\n\n内容二")],
        limit=100,
    )
    assert skipped[-1].section == "主章 / 二级"


def test_cache_hit_and_config_change(sample_pdf: Path, tmp_path: Path, monkeypatch):
    service = ReaderService(tmp_path / "cache")
    first = service.ingest(sample_pdf)
    assert not first.cache_hit
    assert first.page_count == 2

    def no_reparse(*args, **kwargs):
        raise AssertionError("缓存命中时不应重新解析 PDF")

    monkeypatch.setattr("pdf_reader.service.parse_pdf", no_reparse)
    second = service.ingest(sample_pdf)
    assert second.cache_hit
    assert second.document_id == first.document_id
    assert service.read(first.document_id, "c000001").page_number == 1

    with pytest.raises(AssertionError, match="重新解析"):
        service.ingest(sample_pdf, ParseConfig(extract_images=False))

    # 即使文件名不变，只要内容变了，SHA-256 也会让旧缓存失效。
    sample_pdf.write_bytes(sample_pdf.read_bytes() + b"\n")
    with pytest.raises(AssertionError, match="重新解析"):
        service.ingest(sample_pdf)


def test_search_limits_and_token_comparison():
    doc_id = "b" * 64
    document = Document(
        id=doc_id,
        source_sha256="c" * 64,
        source_name="test.pdf",
        converter_version="test",
        config=ParseConfig(),
        pages=[Page(1, "Alpha " * 300), Page(2, "Beta " * 300)],
        chunks=[
            Chunk("c000001", doc_id, "Alpha", 1, "Alpha " * 100),
            Chunk("c000002", doc_id, "Beta", 2, "Beta " * 100),
        ],
    )
    result = search_chunks(document, "Alpha", top_k=1, max_chars=80)
    assert len(result.hits) == 1
    assert result.hits[0].page_number == 1
    assert result.hits[0].truncated
    assert len(result.hits[0].markdown) <= 80
    assert result.estimated_returned_tokens < result.estimated_full_tokens
    assert result.estimated_saved_tokens > 0
    assert search_chunks(document, "不存在").hits == []


def test_cli_outline_search_read_and_export(sample_pdf: Path, tmp_path: Path):
    cache = tmp_path / "cache"
    project = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(project / "src")}

    def command(*args: str) -> dict:
        result = subprocess.run(
            [sys.executable, "-m", "pdf_reader", "--cache-dir", str(cache), *args],
            cwd=project, env=env, text=True, encoding="utf-8", capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    ingested = command("ingest", str(sample_pdf))
    doc_id = ingested["document_id"]
    assert not ingested["cache_hit"]
    assert command("ingest", str(sample_pdf))["cache_hit"]
    outline = command("outline", doc_id)
    assert outline["document_id"] == doc_id
    assert outline["headings"]
    search = command("search", doc_id, "Beta", "--top-k", "1", "--max-chars", "50")
    assert len(search["hits"]) == 1
    assert len(search["hits"][0]["markdown"]) <= 50
    assert "Alpha content" not in json.dumps(search, ensure_ascii=False)
    chunk_id = search["hits"][0]["chunk_id"]
    assert command("read", doc_id, chunk_id)["page_number"] == 2
    output = tmp_path / "export.md"
    assert command("export", doc_id, "-o", str(output))["output"] == str(output)
    markdown = output.read_text(encoding="utf-8")
    assert "<!-- PDF page 1 -->" in markdown
    assert "<!-- PDF page 2 -->" in markdown
    assert "Alpha content" in markdown and "Beta content" in markdown
    image_folder = output.parent / "images" / doc_id[:12]
    assert list(image_folder.glob("*.png"))
    assert f"](images/{doc_id[:12]}/" in markdown


def test_invalid_pdf_reports_error(tmp_path: Path):
    pdf = tmp_path / "broken.pdf"
    pdf.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(ValueError, match="无法打开 PDF"):
        ReaderService(tmp_path / "cache").ingest(pdf)


def test_cli_outputs_utf8_even_when_terminal_uses_gbk(tmp_path: Path):
    doc_id = "d" * 64
    cache = tmp_path / "cache"
    CacheStore(cache).save(Document(
        id=doc_id,
        source_sha256="e" * 64,
        source_name="sample.pdf",
        converter_version="test",
        config=ParseConfig(),
        pages=[Page(1, "# 标题∙特殊字符")],
        headings=[Heading(1, "标题∙特殊字符", 1)],
    ))
    project = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(project / "src"), "PYTHONIOENCODING": "gbk"}
    result = subprocess.run(
        [sys.executable, "-m", "pdf_reader", "--cache-dir", str(cache), "outline", doc_id],
        cwd=project, env=env, text=True, encoding="utf-8", capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["headings"][0]["title"] == "标题∙特殊字符"
