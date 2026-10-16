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


def test_quick_retains_core_method_despite_many_overview_chunks(reading):
    _, document, _ = reading
    document.chunks = [Chunk(f"c{i:06d}", document.id, "Paper / Abstract", 1, "overview " * 30)
                       for i in range(1, 13)] + [
        Chunk("method", document.id, "Paper / Model Architecture / Encoder", 3, "encoder residual method"),
        Chunk("result", document.id, "Paper / Results", 8, "experimental results"),
        Chunk("limit", document.id, "Paper / Limitations", 9, "limited applicability"),
        Chunk("end", document.id, "Paper / Conclusion", 10, "main conclusion"),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert {"method", "result", "limit", "end"} <= set(quick)
    assert len(quick) < len(document.chunks)


def test_summary_skips_repeated_headers_but_keeps_short_evidence(reading):
    _, document, _ = reading
    document.chunks[7:7] = [Chunk("header", document.id, "Paper / Method", 4, "Method  Paper  4"),
                            Chunk("short", document.id, "Paper / Results", 5, "Accuracy: 93.0%.")]
    metadata = inventory(document)
    for mode in ("quick", "standard"):
        assert "header" not in select_chunks(metadata, mode)
        assert "short" in select_chunks(metadata, mode)
    assert "header" in select_chunks(metadata, "deep")


def test_standard_keeps_complete_method_and_results(reading):
    _, document, _ = reading
    document.chunks.insert(4, Chunk("middle", document.id, "Paper / Method", 3,
                                    "essential assumptions and formula explanation"))
    metadata = inventory(document)
    standard = set(select_chunks(metadata, "standard"))
    assert {item["chunk_id"] for item in metadata if item["section"] == "Paper / Method"} <= standard
    assert set(select_chunks(metadata, "quick")) <= standard


def test_quick_method_prefers_explanation_over_displaced_result_table(reading):
    _, document, _ = reading
    document.chunks[3:3] = [
        Chunk("explanation", document.id, "Paper / Model / Embeddings", 3, "learned embeddings and shared weights"),
        Chunk("displaced", document.id, "Paper / Model / Embeddings", 4,
              "Table 1: unrelated comparison\n|a|b|c|\n|---|---|---|\n" + "|1|2|3|\n" * 20),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert "explanation" in quick and "displaced" not in quick
    assert "displaced" in select_chunks(inventory(document), "standard")


@pytest.mark.parametrize("prefix", ["", "Report / ", "Report / Translated model subtitle / ",
                                    "Report / Wrapper / Translation / Subtitle / "])
def test_quick_uses_real_sections_below_shared_wrappers(reading, prefix):
    _, document, _ = reading
    document.chunks = [
        Chunk("problem", document.id, prefix + "Introduction", 1, "research problem and motivation"),
        Chunk("method", document.id, prefix + "Methods / Architecture", 2, "core design " * 20),
        Chunk("detail", document.id, prefix + "Methods / Architecture", 2, "additional detail"),
        Chunk("comparison", document.id, prefix + "Experiments", 4, "comparison evidence"),
        Chunk("conclusion", document.id, prefix + "Conclusion", 5, "main finding"),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert {"problem", "method", "comparison", "conclusion"} <= set(quick)
    assert "detail" not in quick


def test_quick_shared_subtitle_does_not_hide_chinese_sections(reading):
    _, document, _ = reading
    prefix = "调研 / Translated model survey / "
    document.chunks = [
        Chunk("background", document.id, prefix.rstrip(" /"), 1, "**Abstract**: research problem"),
        Chunk("method", document.id, prefix + "1 检测方法", 2, "方法分类及核心解释" * 20),
        Chunk("detail", document.id, prefix + "1 检测方法", 3, "补充说明"),
        Chunk("experiment", document.id, prefix + "2 对比实验", 4, "实验设置与比较结果"),
        Chunk("conclusion", document.id, prefix + "3 总结与展望", 5, "研究结论及局限"),
        Chunk("table", document.id, prefix + "3 总结与展望", 5,
              "|a|b|c|\n|---|---|---|\n" + "|1|2|3|\n" * 40),
    ]
    quick = set(select_chunks(inventory(document), "quick"))
    assert {"background", "method", "experiment", "conclusion"} <= quick
    assert "table" not in quick


def test_quick_unstructured_fallback_is_spread_and_not_only_largest_table(reading):
    _, document, _ = reading
    document.chunks = [Chunk(f"part{i}", document.id, "(无标题)", i + 1, "explanation " * 30)
                       for i in range(9)]
    document.chunks[4] = Chunk("part4", document.id, "(无标题)", 5,
                               "|a|b|c|\n|---|---|---|\n" + "|1|2|3|\n" * 100)
    quick = select_chunks(inventory(document), "quick")
    assert "part0" in quick and "part8" in quick
    assert 3 <= len(quick) < len(document.chunks)
    assert any(chunk_id in quick for chunk_id in ("part3", "part5"))


def test_quick_keeps_explicit_limitations_and_one_boundary_neighbor(reading):
    _, document, _ = reading
    document.chunks = [
        Chunk("intro", document.id, "Paper / Introduction", 1, "research question."),
        Chunk("opening", document.id, "Paper / Discussion and Conclusion", 2,
              "The result requires the\n\n2"),
        Chunk("representative", document.id, "Paper / Discussion and Conclusion", 3,
              "formation of an internal model. " + "Important evidence. " * 30),
        Chunk("limitations", document.id, "Paper / Discussion and Conclusion", 3,
              "**Limitations.** Training costs are high."),
        Chunk("extra", document.id, "Paper / Discussion and Conclusion", 3, "Additional detail."),
        Chunk("appendix", document.id, "Paper / Appendix", 4, "**Limitations.** Appendix only."),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert {"opening", "representative", "limitations"} <= set(quick)
    assert "extra" not in quick and "appendix" not in quick


def test_quick_continuation_can_follow_intervening_image_and_is_not_recursive(reading):
    _, document, _ = reading
    document.chunks = [
        Chunk("intro", document.id, "Paper / Introduction", 1, "Problem."),
        Chunk("before", document.id, "Paper / Results", 2, "The system **must craft the**\n\n2"),
        Chunk("selected", document.id, "Paper / Results", 3,
              "![](images/chart.png)\n\nFigure 1: comparison.\n\n**query** for planning. " + "Evidence. " * 40),
        Chunk("end", document.id, "Paper / Conclusion", 4, "Main conclusion."),
    ]
    assert {"before", "selected"} <= set(select_chunks(inventory(document), "quick"))
    document.chunks = [
        Chunk("intro", document.id, "Paper / Introduction", 1, "Problem."),
        Chunk("first", document.id, "Paper / Method", 2, "architecture " * 100),
        Chunk("next", document.id, "Paper / Method", 3, "continuation of the"),
        Chunk("last", document.id, "Paper / Method", 4, "remaining details."),
        Chunk("end", document.id, "Paper / Conclusion", 5, "Main conclusion."),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert "next" in quick and "last" not in quick


def test_quick_repeated_inline_overview_labels_do_not_select_every_chunk(reading):
    _, document, _ = reading
    document.chunks = [Chunk(f"abstract{i}", document.id, "Paper / Abstract", 1,
                             "**Abstract**: overview. " * 20) for i in range(12)] + [
        Chunk("method", document.id, "Paper / Method", 2, "Design."),
        Chunk("end", document.id, "Paper / Conclusion", 3, "Findings."),
    ]
    quick = select_chunks(inventory(document), "quick")
    assert len(quick) == 3


def test_short_numeric_and_symbol_evidence_is_not_formatting(reading):
    _, document, _ = reading
    document.chunks[3:3] = [Chunk("number", document.id, "Paper / Method", 3, "93.0"),
                            Chunk("symbol", document.id, "Paper / Method", 3, "√(64) = 8"),
                            Chunk("prose", document.id, "Paper / Method", 3, "Chapter 1 explains our new method")]
    standard = select_chunks(inventory(document), "standard")
    assert {"number", "symbol", "prose"} <= set(standard)


@pytest.mark.parametrize("flags, expected", [
    (["--pages", "3", "4"], ["c000004", "c000005", "c000006", "c000007"]),
    (["--section", "Paper / Method"], ["c000004", "c000005", "c000006", "c000007"]),
    (["--section", "Paper / Appendix A"], ["c000011", "c000012"]),
    (["--scope", "body"], [f"c{i:06d}" for i in range(1, 9)]),
    (["--scope", "all"], [f"c{i:06d}" for i in range(1, 13)]),
])
def test_explicit_deep_scope_plan_delivery_and_recovery(reading, capsys, flags, expected):
    tracker, document, root = reading
    record = root / "scope.json"
    invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record, *flags, "--compact")
    state = tracker.load(record)
    assert state["planned_chunk_ids"] == expected and state["scope"]
    # Already delivered evidence must not be repeated by subsequent batches.
    invoke(tracker, capsys, "read", document.id, expected[0], "--reading-record", record)
    delivered = [expected[0]]
    while not tracker.status(record)["plan_complete"]:
        batch = invoke(tracker, capsys, "reading-next", record, "--compact")
        delivered.extend(chunk["id"] for chunk in batch["chunks"])
    assert delivered == expected
    assert set(tracker.status(record)["read_chunk_ids"]) == set(expected)
    invoke(tracker, capsys, "reading-gap", record, expected[0], "--reason", "external truncation")
    batch = invoke(tracker, capsys, "reading-next", record, "--compact")
    assert [chunk["id"] for chunk in batch["chunks"]] == [expected[0]]
    assert tracker.status(record)["plan_complete"]
    assert not tracker.status(record)["complete_text_delivery"]  # page 9 has no extracted text


@pytest.mark.parametrize("flags", [
    ["--mode", "quick", "--scope", "all"],
    ["--mode", "deep", "--pages", "4", "3"],
    ["--mode", "deep", "--pages", "1", "10"],
    ["--mode", "deep", "--section", "Missing"],
    ["--mode", "deep", "--pages", "1", "2", "--scope", "all"],
])
def test_invalid_deep_scope_does_not_create_record(reading, capsys, flags):
    tracker, document, root = reading
    record = root / "invalid.json"
    with pytest.raises(SystemExit):
        invoke(tracker, capsys, "reading-start", document.id, "--record", record, *flags)
    assert not record.exists()


def test_deep_section_includes_descendants_and_explicit_pages_keep_references(reading):
    tracker, document, root = reading
    document.chunks.insert(7, Chunk("child", document.id, "Paper / Method / Assumptions", 4, "short assumptions"))
    tracker.cache.save(document)
    result = tracker.start(document.id, "deep", root / "subtree.json", section="Paper / Method")
    assert "child" in result["planned_chunk_ids"]
    assert "c000008" not in result["planned_chunk_ids"]
    reference = tracker.start(document.id, "deep", root / "references.json", pages=[6, 6])
    assert reference["planned_chunk_ids"] == ["c000009", "c000010"]


def test_legacy_record_resumes_without_scope_and_keeps_its_plan(reading):
    tracker, document, root = reading
    record = root / "old.json"
    tracker.start(document.id, "deep", record)
    state = tracker.load(record)
    state.pop("scope", None)
    state["planned_chunk_ids"] = ["c000004", "c000009"]
    tracker._save(record, state)
    batch, event = tracker.next_batch(record)
    assert [chunk["id"] for chunk in batch["chunks"]] == state["planned_chunk_ids"]
    tracker.record(record, event)
    assert tracker.status(record)["plan_complete"]


def test_skill_routes_local_detail_to_focused_and_documents_to_scoped_deep():
    root = Path(__file__).resolve().parents[1] / "skills/pdf-reader"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    reference = (root / "references/reading.md").read_text(encoding="utf-8")
    assert "Focused" in skill and "sqrt(d_k)" in skill
    assert "specific question stays Focused even when" in skill
    assert "Ordinary knowledge questions without a specific PDF" in skill
    assert "--scope all" in reference and "--pages" in reference and "--section" in reference
    assert "Deep for complete reading, detailed analysis, or derivation" not in skill


def test_focused_skill_has_context_and_gap_driven_reading_contract():
    root = Path(__file__).resolve().parents[1] / "skills/pdf-reader"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    reference = (root / "references/reading.md").read_text(encoding="utf-8")
    assert "Focused evidence loop" in skill and "Focused evidence loop" in reference
    for requirement in ("Do not read all Top-5 hits", "current-context evidence", "historical delivery",
                        "context compaction", "search has no section filter", "Do not fabricate delivery events"):
        assert requirement in reference


def test_focused_reuse_does_not_log_delivery_and_full_rereads_remain_allowed(reading, capsys):
    tracker, document, root = reading
    # An existing record can receive supplemental Focused calls without running its plan.
    record = root / "existing.json"
    tracker.start(document.id, record=record)
    invoke(tracker, capsys, "search", document.id, "method", "--reading-record", record)
    assert tracker.status(record)["read_chunks"] == 0
    invoke(tracker, capsys, "read", document.id, "c000004", "--reading-record", record)
    state = tracker.load(record)
    assert state["coverage"]["read_chunk_ids"] == ["c000004"]
    # Offline reuse decision: no CLI call, therefore no fabricated output event.
    assert tracker.load(record)["events"] == state["events"]
    invoke(tracker, capsys, "read", document.id, "c000004", "--reading-record", record)
    reread = tracker.load(record)
    assert reread["events"][-1]["full"] == ["c000004"]
    assert reread["coverage"]["read_chunks"] == 1
    invoke(tracker, capsys, "reading-gap", record, "c000004", "--reason", "external output unavailable")
    assert tracker.status(record)["read_chunks"] == 0
    data = invoke(tracker, capsys, "read", document.id, "c000004", "--reading-record", record)
    assert data["page_number"] == 3 and data["markdown"] == document.chunks[3].markdown
    assert tracker.status(record)["read_chunk_ids"] == ["c000004"]
    other = root / "other.json"
    tracker.start(document.id, record=other)
    assert tracker.status(other)["read_chunks"] == 0
    invoke(tracker, capsys, "read", document.id, "c000004", "--reading-record", other)
    assert tracker.status(other)["read_chunks"] == 1


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


def test_compact_batches_preserve_delivery_events_and_recovery(reading, capsys):
    tracker, document, root = reading
    records = [root / "legacy.json", root / "compact.json"]
    starts = [invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record,
                     *(["--compact"] if index else [])) for index, record in enumerate(records)]
    assert starts[1]["planned_chunks"] == starts[0]["planned_chunks"]
    assert "planned_chunk_ids" not in starts[1]
    for budget in (20, 1000):
        batches = [invoke(tracker, capsys, "reading-next", record, "--max-chars", budget,
                          *(["--compact"] if index else [])) for index, record in enumerate(records)]
        expected = [{key: value for key, value in chunk.items() if key != "document_id"}
                    for chunk in batches[0]["chunks"]]
        assert batches[1]["chunks"] == expected
        for key in ("remaining_planned_after_output", "needs_full_read"):
            assert batches[1][key] == batches[0][key]
        states = [tracker.load(record) for record in records]
        assert states[0]["events"] == states[1]["events"]
        assert len(json.dumps(batches[1])) < len(json.dumps(batches[0]))


def test_compact_status_keeps_gaps_sections_and_visual_disclosure(reading, capsys):
    tracker, document, root = reading
    record = root / "compact.json"
    invoke(tracker, capsys, "reading-start", document.id, "--mode", "deep", "--record", record)
    invoke(tracker, capsys, "reading-next", record)
    invoke(tracker, capsys, "reading-gap", record, "c000001", "--reason", "external truncation")
    compact = invoke(tracker, capsys, "reading-status", record, "--compact")
    detailed = invoke(tracker, capsys, "reading-status", record, "--details", "--compact")
    for key in ("read_chunks", "covered_pages", "fully_covered_pages", "plan_complete",
                "complete_text_delivery", "pages_without_extracted_chunks", "coverage_basis"):
        assert compact[key] == detailed[key]
    assert compact["remaining_planned_chunks"] == len(detailed["remaining_planned_chunk_ids"])
    assert any(group["reason"] == "external truncation" and group["chunks"] == 1 for group in compact["unread_groups"])
    assert sum(compact["section_states"].values()) == len(detailed["sections"])
    assert all(section["status"] != "complete_text_returned" for section in compact["sections"])
    assert compact["visuals"]["not_viewed_count"] == len(detailed["assets"])
    assert "not_machine_authenticated" in compact["visuals"]["receipt_trust"]
    assert detailed["read_chunk_ids"] and "read_chunk_ids" not in compact
    assert len(json.dumps(compact)) < len(json.dumps(detailed))


def test_batch_is_flushed_before_event_commit(reading, capsys, monkeypatch):
    tracker, document, root = reading
    record = root / "order.json"
    tracker.start(document.id, mode="deep", record=record)
    import builtins
    original_print = builtins.print
    observed = []
    def checked_print(*args, **kwargs):
        assert kwargs.get("flush") is True
        assert tracker.status(record)["event_count"] == 0
        observed.extend(chunk["id"] for chunk in json.loads(args[0])["chunks"])
        original_print(*args, **kwargs)
    monkeypatch.setattr("builtins.print", checked_print)
    invoke(tracker, capsys, "reading-next", record)
    assert tracker.load(record)["events"][0]["full"] == observed


def test_failed_flush_does_not_commit_batch(reading, monkeypatch):
    tracker, document, root = reading
    record = root / "flush-failure.json"
    tracker.start(document.id, record=record)
    class FailingFlush:
        def write(self, text):
            return len(text)
        def flush(self):
            raise BrokenPipeError("flush unavailable")
    monkeypatch.setattr("pdf_reader.cli.sys.stdout", FailingFlush())
    with pytest.raises(BrokenPipeError, match="flush unavailable"):
        main(["--cache-dir", str(tracker.cache.root), "reading-next", str(record)])
    assert tracker.status(record)["event_count"] == 0
