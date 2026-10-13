"""Evidence warnings and on-demand verification against the benchmark paper."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pdf_reader import ReaderService
from pdf_reader.cache import CacheStore
from pdf_reader.evidence import assess_evidence


PAPER = Path(__file__).resolve().parents[1] / "input" / "Attention Is All You Need.pdf"


@pytest.fixture(scope="module")
def paper(tmp_path_factory):
    service = ReaderService(tmp_path_factory.mktemp("attention-evidence"))
    imported = service.ingest(PAPER)
    return service, imported.document_id


def test_benchmark_warnings_are_hints_not_certificates(paper):
    service, doc_id = paper
    q2 = service.search(doc_id, "Scaled Dot-Product Attention sqrt dk softmax gradients")
    assert any(h.page_number == 4 and "formula_image" in h.evidence_warnings for h in q2.hits)

    q3 = service.search(doc_id, "Positional Encoding sine cosine relative positions")
    assert any(h.page_number == 6 and "formula_image" in h.evidence_warnings for h in q3.hits)
    positional = next(c for c in service.cache.load(doc_id).chunks if c.id == "c000023")
    assert "formula_image" in assess_evidence(positional.markdown, "PE(pos,2i)")

    q5 = service.search(doc_id, "newstest2014 training cost FLOPs")
    assert any(h.page_number == 8 and "table_structure" in h.evidence_warnings for h in q5.hits)

    q1 = service.search(doc_id, "Encoder Decoder six identical layers masked")
    assert any(h.page_number == 3 and not h.evidence_warnings for h in q1.hits)
    q4 = service.search(doc_id, "Maximum path lengths per-layer complexity minimum sequential operations")
    assert any(h.page_number == 6 and not h.evidence_warnings for h in q4.hits)

    figure = service.search(doc_id, "long-distance dependencies verb making different colors heads")
    assert any(h.page_number == 13 and "visual_detail" in h.evidence_warnings for h in figure.hits)


def test_visual_detail_intent_is_flagged_even_without_image_link():
    assert "visual_detail" in assess_evidence("Figure 3 shows attention heads.", "Which colors and lines connect the words in Figure 3?")
    assert "visual_detail" in assess_evidence("图注", "图 3 的连线表示什么？")
    assert "visual_detail" in assess_evidence("Attention heads", "Which colors connect distant words?")
    assert assess_evidence("Ordinary narrative text.", "What does this paragraph mean?") == []


def test_render_only_requested_pages_and_reuse_cached_png(paper):
    service, doc_id = paper
    page4 = service.render_page(doc_id, 4)
    assert page4.page_number == 4 and not page4.cache_hit
    assert Path(page4.image_path).is_file()
    assert page4.pixel_width > 0 and page4.pixel_height > 0

    second = service.render_page(doc_id, 4)
    assert second.cache_hit and second.image_path == page4.image_path

    page6 = service.render_page(doc_id, 6)
    page8 = service.render_page(doc_id, 8)
    assert all(Path(item.image_path).is_file() for item in (page6, page8))
    images = list((service.cache.folder(doc_id) / "rendered_pages").glob("*.png"))
    assert len(images) == 3

    clip = service.render_page(doc_id, 4, scale=2, clip=(200, 350, 500, 600))
    assert Path(clip.image_path).is_file()
    assert clip.image_path != page4.image_path
    assert clip.pixel_width < page4.pixel_width
    assert service.render_page(doc_id, 4, scale=2, clip=(200, 350, 500, 600)).cache_hit


def test_render_validates_page_region_and_source(paper, tmp_path):
    service, doc_id = paper
    with pytest.raises(ValueError, match="页码"):
        service.render_page(doc_id, 0)
    with pytest.raises(ValueError, match="页码"):
        service.render_page(doc_id, 16)
    with pytest.raises(ValueError, match="区域"):
        service.render_page(doc_id, 4, clip=(100, 100, 50, 200))
    with pytest.raises(ValueError, match="区域"):
        service.render_page(doc_id, 4, clip=(0, 0, 9999, 9999))
    with pytest.raises(ValueError, match="缩放"):
        service.render_page(doc_id, 4, scale=0)
    with pytest.raises((ValueError, FileNotFoundError), match="PDF"):
        service.render_page(doc_id, 4, pdf_path=tmp_path / "missing.pdf")

    wrong_pdf = tmp_path / "wrong.pdf"
    wrong_pdf.write_bytes(b"%PDF-1.4\nwrong bytes")
    with pytest.raises(ValueError, match="哈希|匹配"):
        service.render_page(doc_id, 4, pdf_path=wrong_pdf)


def test_legacy_cache_can_use_explicit_pdf_and_missing_image_is_regenerated(paper):
    service, doc_id = paper
    document = service.cache.load(doc_id)
    document.source_path = None
    service.cache.save(document)
    with pytest.raises((ValueError, FileNotFoundError), match="PDF"):
        service.render_page(doc_id, 5)
    first = service.render_page(doc_id, 5, pdf_path=PAPER)
    image = Path(first.image_path)
    image.unlink()
    assert not image.exists()
    regenerated = service.render_page(doc_id, 5, pdf_path=PAPER)
    assert not regenerated.cache_hit and image.is_file()


def test_cli_render_page_returns_path_and_clear_errors(paper, tmp_path):
    service, doc_id = paper
    project = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(project / "src")}

    def command(*args: str):
        return subprocess.run(
            [sys.executable, "-m", "pdf_reader", "--cache-dir", str(service.cache.root), *args],
            cwd=project, env=env, text=True, encoding="utf-8", capture_output=True,
        )

    good = command("render-page", doc_id, "4", "--pdf", str(PAPER))
    assert good.returncode == 0, good.stderr
    assert Path(json.loads(good.stdout)["image_path"]).is_file()
    bad = command("render-page", doc_id, "99", "--pdf", str(PAPER))
    assert bad.returncode != 0 and "页码" in bad.stderr
    missing = command("render-page", doc_id, "4", "--pdf", str(tmp_path / "none.pdf"))
    assert missing.returncode != 0 and "PDF" in missing.stderr


def test_render_reports_unavailable_image_output(paper, monkeypatch):
    service, doc_id = paper
    original_mkdir = Path.mkdir

    def inaccessible_render_folder(path, *args, **kwargs):
        if path.name == "rendered_pages":
            raise PermissionError("页面图片目录无法访问")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", inaccessible_render_folder)
    with pytest.raises(PermissionError, match="页面图片目录无法访问"):
        service.render_page(doc_id, 11, pdf_path=PAPER)


def test_cli_reports_inaccessible_image_destination(paper, tmp_path):
    service, doc_id = paper
    blocked_cache = CacheStore(tmp_path / "blocked-cache")
    document = service.cache.load(doc_id)
    blocked_cache.save(document)
    (blocked_cache.folder(doc_id) / "rendered_pages").write_text("not a folder", encoding="utf-8")
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "pdf_reader", "--cache-dir", str(blocked_cache.root),
         "render-page", doc_id, "4", "--pdf", str(PAPER)],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        text=True, encoding="utf-8", capture_output=True,
    )
    assert result.returncode != 0 and "错误" in result.stderr
    assert "rendered_pages" in result.stderr
