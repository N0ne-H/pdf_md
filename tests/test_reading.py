"""阅读覆盖来源为返回事件；定位、截断、渲染与外部查看回执分开统计。"""

import json
from pathlib import Path

import pytest

from pdf_reader.cache import CacheStore
from pdf_reader.cli import main
from pdf_reader.models import Chunk, Document, Heading, Page, ParseConfig, RenderResult
from pdf_reader.reading import ReadingTracker, inventory, select_chunks


@pytest.fixture
def reading(tmp_path):
    doc_id = "a" * 64
    parts = [
        (1, "Abstract", "overview " * 30),
        (2, "Introduction", "contribution " * 25),
        (2, "Introduction", "context " * 20),
        (3, "Method", "method " * 40),
        (3, "Method", "equation ![](images/formula.png)"),
        (4, "Method", "Table 1\n|a|b|c|\n|---|---|---|\n|1|2|3|"),
        (4, "Method", "limitations " * 20),
        (5, "Conclusion", "conclusion " * 20),
        (6, "References", "**References** citation"),
        (6, "References", "more citations"),
        (7, "Appendix A", "derivation ![](images/appendix.png)"),
        (8, "Appendix A", "appendix detail " * 20),
    ]
    document = Document(doc_id, "b" * 64, "test.pdf", "test", ParseConfig(),
        pages=[Page(number, "text" if number < 9 else "") for number in range(1, 10)],
        headings=[Heading(1, "Paper", 1)] + [Heading(2, title, page) for page, title in
            [(1, "Abstract"), (2, "Introduction"), (3, "Method"), (5, "Conclusion"), (6, "References"), (7, "Appendix A")]],
        chunks=[Chunk(f"c{index:06d}", doc_id, "Paper / " + title, page, text)
                for index, (page, title, text) in enumerate(parts, 1)])
    cache = CacheStore(tmp_path / "cache")
    cache.save(document)
    images = cache.folder(doc_id) / "images"
    images.mkdir()
    (images / "formula.png").write_bytes(b"external image fixture")
    return ReadingTracker(cache), document, tmp_path


def invoke(tracker, capsys, *args):
    main(["--cache-dir", str(tracker.cache.root), *map(str, args)])
    return json.loads(capsys.readouterr().out)


def test_metadata_and_modes_do_not_return_markdown(reading):
    tracker, document, _ = reading
    catalog = tracker.catalog(document.id, limit=3)
    assert len(catalog["chunks"]) == 3 and catalog["next_offset"] == 3
    assert all("markdown" not in item for item in catalog["chunks"])
    metadata = inventory(document)
    scopes = [select_chunks(metadata, mode) for mode in ("quick", "standard", "deep")]
    assert len(scopes[0]) < len(scopes[1]) < len(scopes[2])
    assert "c000011" not in scopes[1] and "c000011" in scopes[2]
    assert "c000009" not in scopes[2]


def test_search_located_is_not_full_read_and_duplicate_read_is_unique(reading, capsys):
    tracker, document, root = reading
    record = root / "session.json"
    invoke(tracker, capsys, "reading-start", document.id, "--record", record)
    invoke(tracker, capsys, "search", document.id, "method", "--reading-record", record)
    status = tracker.status(record)
    assert status["located_chunk_ids"] and status["read_chunks"] == 0
    for _ in range(2):
        invoke(tracker, capsys, "read", document.id, "c000004", "--reading-record", record)
    status = tracker.status(record)
    assert status["read_chunks"] == 1 and status["covered_pages"] == [3]
    assert status["fully_covered_pages"] == []
    assert next(s for s in status["sections"] if s["title"] == "Method")["status"] == "partial"


def test_batches_resume_truncation_and_gaps_are_not_full_coverage(reading, capsys):
    tracker, document, root = reading
    record = root / "session.json"
    invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record)
    result = invoke(tracker, capsys, "reading-next", record, "--max-chars", 20)
    assert result["chunks"][0]["truncated"] and tracker.status(record)["read_chunks"] == 0
    while not tracker.status(record)["plan_complete"]:
        batch = invoke(tracker, capsys, "reading-next", record, "--max-chunks", 2, "--max-chars", 1000)
        assert len(batch["chunks"]) <= 2 and sum(len(c["markdown"]) for c in batch["chunks"]) <= 1000
    status = tracker.status(record)
    assert status["read_chunks"] == 10 and not status["complete_text_delivery"]
    assert status["pages_without_extracted_chunks"] == [9]
    assert any(c["role"] == "references" for c in status["unread_chunks"])
    assert next(s for s in status["sections"] if s["title"] == "Appendix A")["status"] == "complete_text_returned"
    invoke(tracker, capsys, "reading-gap", record, "c000011", "--reason", "external tool output truncated")
    status = tracker.status(record)
    assert status["read_chunks"] == 9 and not status["plan_complete"]
    assert next(c for c in status["unread_chunks"] if c["chunk_id"] == "c000011")["reason"].startswith("external")
    invoke(tracker, capsys, "reading-next", record)
    assert tracker.status(record)["read_chunks"] == 10


def test_deep_pending_appendix_and_untouched_legacy_cache(reading, capsys):
    tracker, document, root = reading
    original = (tracker.cache.folder(document.id) / "document.json").read_bytes()
    record = root / "session.json"
    invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record)
    invoke(tracker, capsys, "reading-next", record, "--max-chunks", 2)
    status = tracker.status(record)
    assert not status["plan_complete"] and not status["complete_text_delivery"]
    assert next(s for s in status["sections"] if s["title"] == "Appendix A")["status"] == "unread"
    assert (tracker.cache.folder(document.id) / "document.json").read_bytes() == original


def test_render_does_not_mark_viewed_and_receipt_is_labeled_external(reading, capsys, monkeypatch):
    tracker, document, root = reading
    record = root / "session.json"
    invoke(tracker, capsys, "reading-start", document.id, "--record", record)
    image = tracker.cache.folder(document.id) / "images" / "formula.png"
    monkeypatch.setattr("pdf_reader.cli.ReaderService.render_page", lambda *args, **kw:
                        RenderResult(document.id, 3, str(image), True, 1, 1, 2, None))
    invoke(tracker, capsys, "render-page", document.id, 3, "--reading-record", record)
    asset_id = "c000005:image:1"
    assert all(asset["status"] == "not_viewed" for asset in tracker.status(record)["assets"])
    with pytest.raises(ValueError, match="evidence"):
        tracker.visual(record, asset_id, image)
    wrong_image = root / "other.png"
    wrong_image.write_bytes(b"image")
    with pytest.raises(ValueError, match="图片来源"):
        tracker.visual(record, asset_id, wrong_image, "view_image result")
    invoke(tracker, capsys, "reading-visual", record, asset_id, "--image", image, "--evidence", "test external receipt")
    asset = next(a for a in tracker.status(record)["assets"] if a["asset_id"] == asset_id)
    assert asset["status"] == "viewed_reported" and "not_machine_authenticated" in asset["receipt"]["source"]
    assert tracker.status(record)["read_chunks"] == 0


def test_failed_output_does_not_commit_read_event(reading, monkeypatch):
    tracker, document, root = reading
    record = root / "session.json"
    tracker.start(document.id, record=record)
    def failed_print(*args, **kwargs):
        raise BrokenPipeError("output unavailable")
    monkeypatch.setattr("builtins.print", failed_print)
    with pytest.raises(BrokenPipeError):
        main(["--cache-dir", str(tracker.cache.root), "reading-next", str(record)])
    assert tracker.status(record)["event_count"] == 0


def test_wrong_document_record_and_existing_record_are_rejected(reading):
    tracker, document, root = reading
    record = root / "session.json"
    tracker.start(document.id, record=record)
    with pytest.raises(ValueError, match="不覆盖"):
        tracker.start(document.id, record=record)
    with pytest.raises(ValueError, match="不匹配"):
        tracker.load(record, "b" * 64)


def test_compact_status_preserves_counts_and_durable_detailed_snapshot(reading, capsys):
    tracker, document, root = reading
    record = root / "session.json"
    invoke(tracker, capsys, "reading-start", document.id, "--record", record)
    invoke(tracker, capsys, "reading-next", record)
    compact = invoke(tracker, capsys, "reading-status", record)
    detailed = invoke(tracker, capsys, "reading-status", record, "--details")
    snapshot = json.loads(record.read_text(encoding="utf-8"))["coverage"]
    assert compact["read_chunk_ids"] == detailed["read_chunk_ids"] == snapshot["read_chunk_ids"]
    assert compact["covered_pages"] == detailed["covered_pages"]
    assert compact["unread_groups"] and "assets" not in compact
    assert len(json.dumps(compact)) < len(json.dumps(detailed))


def test_long_document_is_planned_as_metadata_and_read_in_bounded_batches(reading, capsys):
    tracker, document, root = reading
    document.headings = [Heading(1, "Long document", 1)]
    document.pages = [Page(page, "extracted text") for page in range(1, 9)]
    document.chunks = [Chunk(f"c{index:06d}", document.id, "Long document", (index - 1) // 10 + 1,
                             "paragraph " * 50) for index in range(1, 81)]
    tracker.cache.save(document)
    record = root / "long.json"
    started = invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record)
    assert started["planned_chunks"] == 80 and "markdown" not in json.dumps(started)
    catalog = invoke(tracker, capsys, "chunks", document.id, "--limit", 10)
    assert len(catalog["chunks"]) == 10 and catalog["next_offset"] == 10
    batch = invoke(tracker, capsys, "reading-next", record)
    assert len(batch["chunks"]) == 5 and batch["remaining_planned_after_output"] == 75
    assert tracker.status(record)["read_chunks"] == 5


def test_flat_top_level_chapters_are_body_not_frontmatter(reading):
    _, document, _ = reading
    titles = ["Introduction", "Method", "Conclusion"]
    document.headings = [Heading(1, title, index) for index, title in enumerate(titles, 1)]
    document.chunks = [Chunk(f"c{index:06d}", document.id, title, index, title + " substantive text")
                       for index, title in enumerate(titles, 1)]
    metadata = inventory(document)
    assert all(item["role"] == "body" for item in metadata)
    assert select_chunks(metadata, "standard") == ["c000001", "c000002", "c000003"]
    assert "c000003" in select_chunks(metadata, "quick")


def test_table_of_contents_is_not_read_as_key_results(reading):
    _, document, _ = reading
    document.chunks.append(Chunk("c000013", document.id, "Paper / Table of Contents", 1,
                                 "|Chapter|Page|Info|\n|---|---|---|\n|Method|3|Details|"))
    metadata = inventory(document)
    for mode in ("quick", "standard", "deep"):
        assert "c000013" not in select_chunks(metadata, mode)


def test_quick_manual_samples_chapters_despite_incidental_summary_heading(reading):
    _, document, _ = reading
    document.headings = [Heading(1, "Manual", 1), Heading(2, "1 Setup", 1), Heading(2, "2 Build", 2), Heading(2, "3 Publish", 3)]
    document.chunks = [
        Chunk("c1", document.id, "Manual / 1 Setup", 1, "setup details " * 30),
        Chunk("c2", document.id, "Manual / 1 Setup / 按钮总结", 1, "|a|b|c|\n|---|---|---|\n|1|2|3|"),
        Chunk("c3", document.id, "Manual / 2 Build", 2, "build details " * 30),
        Chunk("c4", document.id, "Manual / 3 Publish", 3, "publish details " * 30),
    ]
    assert select_chunks(inventory(document), "quick") == ["c1", "c3", "c4"]
