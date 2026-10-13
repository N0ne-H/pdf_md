# PDF Evidence Verification Implementation Plan

> For agentic workers: implement the following tasks in order, verifying each before continuing.

**Goal:** Warn when retrieved Markdown may omit visual evidence and render only the needed original PDF page for verification.

**Architecture:** Keep search and cache formats compatible. Add rule-based flags to search hits, store an optional source PDF path with a cached document, and expose a PyMuPDF single-page renderer through `ReaderService` and CLI. The global Skill decides when to inspect the rendered image.

**Tech Stack:** Python 3.11, PyMuPDF 1.28.2, pymupdf4llm 1.28.2, pytest, PowerShell, local Codex Skill.

**Spec:** User's stage-four evidence reliability request; benchmark report at `output/基准测试1/Attention_Is_All_You_Need_基准测试报告.md`.

## Global Constraints

- Keep existing Core, CLI commands and schema-1 cache readable.
- No MCP, paid API, OCR, MinerU, vector database or full-document rendering.
- Reinstall the non-editable package and test its CLI after edits.

---

### Task 1: Retrieval evidence warnings

**Files:** `src/pdf_reader/evidence.py`, `src/pdf_reader/models.py`, `src/pdf_reader/search.py`, `tests/test_evidence.py`.

**Interface:** `assess_evidence(markdown: str, query: str) -> list[str]`; append `evidence_warnings` to `SearchHit`.

- [x] Write tests for Q2/Q3 formula-image links, Q5 suspicious table rows, visual-detail intent, and Q1/Q4 ordinary text.
- [x] Run `pytest tests/test_evidence.py -q` and observe the new tests fail.
- [x] Add only warning rules that the tests demonstrate; score/ranking and Markdown output remain unchanged.
- [x] Re-run those tests and the original search test.

### Task 2: On-demand page rendering

**Files:** `src/pdf_reader/models.py`, `src/pdf_reader/cache.py`, `src/pdf_reader/service.py`, `src/pdf_reader/cli.py`, `tests/test_evidence.py`.

**Interface:** `ReaderService.render_page(doc_id, page_number, *, scale=2.0, clip=None, pdf_path=None) -> RenderResult`; CLI `render-page DOC_ID PAGE [--scale N] [--clip X0 Y0 X1 Y1] [--pdf PATH]`.

- [x] Test page 4, page 6, page 8, repeat-render cache hit, local clip, old cache with explicit PDF, wrong/missing PDF, nonexistent page, and unwritable image output.
- [x] Run targeted tests and observe failure before implementing.
- [x] Save optional source path in schema-1 cache; verify its SHA-256 before rendering. Save deterministic PNGs only for requested pages/regions.
- [x] Re-run targeted tests and confirm no other pages are rendered.

### Task 3: Skill and installed-package integration

**Files:** `C:/Users/26214/.agents/skills/pdf-reader/SKILL.md` plus any test artifacts under `output/`.

- [x] Update the global Skill to inspect warning flags, render/actually view a relevant page for exact formulas, numbers, or visual details, and disclose failed visual inspection.
- [x] Validate the Skill, reinstall the package non-editably, and run CLI Q2/Q3/Q5 plus ordinary Q1/Q4 checks from the installed package.
- [x] Run all pytest tests; verify global Skill works from another cwd and report text/visual cost separately.

