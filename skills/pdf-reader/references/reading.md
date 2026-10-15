# Reading modes and evidence coverage

Use the installed launcher from SKILL.md for every command below. Replace DOC_ID and RECORD_PATH with actual outputs. Do not concatenate the whole cached Markdown to plan a summary.

## Choose a scope

- Quick: a low-cost overview from abstract, contribution/introduction, main results/tables and conclusion. For manuals without these headings, sample substantive content across major chapters. State that this is an overview.
- Standard: default for an ordinary paper/document summary. Cover the main sections and important formula/table evidence. Sampled sections can remain partial; do not call this complete reading.
- Deep: for complete reading, detailed analysis or derivation. Read body and supplementary/appendix content in batches. Bibliography and explicit table-of-contents sections are excluded from the initial plan and must be disclosed; use explicit `read` if they matter to the request. The metadata outline is enough to plan chapters without reading a duplicated contents table as a key result.

The automatic plan is a lexical suggestion. For a routine summary, start the compact reading task and check section labels as batches arrive. If structure is unclear or exclusions look unexpected, inspect `outline DOC_ID` once. Use paged `chunks DOC_ID --offset 0 --limit 50` when you need missing-block IDs or image/table candidates; it returns metadata only. Repeated headings, unheaded bibliography, or after-reference material may be classified imperfectly. Do not treat a metadata role or a candidate image as a guaranteed semantic classification. Add targeted `search`/`read` calls with the same record when important content is missing.

## Start, read, and resume

1. Run `reading-start DOC_ID --mode quick|standard|deep --compact`. Standard is the CLI default. Optional `--record 'workspace\reading.json'` selects a task log; existing records are not overwritten. Retain the absolute `record_path`.
2. Run `reading-next RECORD_PATH --max-chunks 5 --max-chars 6000 --compact`. Read the returned batch before requesting the next one. Repeat until `remaining_planned_after_output` is zero, or consciously stop and disclose why. No single batch can request more than 20 chunks or 20,000 body characters. The character budget covers body text, not the full JSON; allocate enough tool output tokens to display it fully.
3. If `needs_full_read` is nonempty, use `read DOC_ID CHUNK_ID --reading-record RECORD_PATH` or increase the next batch budget within the allowed limit. A truncated preview remains unread.
4. At the end, run `reading-status RECORD_PATH --compact`. It reports counts, incomplete sections, omission groups and visual trust. For missing-block IDs, complete-section details or individual image receipts, use `reading-status RECORD_PATH --details`; `--details --compact` retains these fields with less JSON whitespace. The task file also stores the detailed computed coverage snapshot. Omit `--compact` for the legacy response layout. Reuse the same file to resume later, including from another cwd. Use one writer at a time per record; separate tasks get separate records.

Optional `--reading-record RECORD_PATH` on `search`, `read`, and `render-page` records their successful outputs. Search logs location/preview only; a full `read` or complete batch chunk logs text delivery. A successful render logs an available image and never marks it viewed. Ordinary untracked question retrieval remains supported.

If the surrounding tool truncates the CLI JSON, a full CLI return does not prove that Codex received all of it. Record `reading-gap RECORD_PATH CHUNK_ID --reason 'external tool output truncated'` for affected chunks, then reread in a smaller batch. If affected IDs are unclear, recover the last event's IDs from the task log and conservatively reread that batch. The gap removes that chunk from coverage until it is fully returned again. A saved stdout file or a loop printing only IDs/counts is not model-visible body delivery: display the full batch before advancing. Also record known omissions due to extraction failure, unreadable content or other blockers. Empty extracted pages are reported as such, not automatically called parsing failures or blank pages.

## Formula and image checks

Keep the visual rules from SKILL.md. Locate the relevant candidate asset in metadata/status; actually call the image viewer on the extracted image or a rendered original page. When rendering for a reading task, include `--reading-record RECORD_PATH`.

Only after an image tool has successfully displayed the relevant evidence, submit:

```text
reading-visual RECORD_PATH ASSET_ID --image ABSOLUTE_IMAGE_PATH --evidence 'actual image tool result reference and verification scope'
```

Use the actual tool result/call reference when the host exposes it; otherwise describe the completed view and exact path/scope, without inventing a call ID. A rendered page must have a matching recorded render on the candidate's page. Viewing a partial crop verifies only the content inside it. A single viewed page does not automatically verify every asset on that page; record only those actually checked.

For failed/unavailable viewing, use `reading-visual RECORD_PATH ASSET_ID --reason 'specific failure or intentionally not checked'`. Do not submit a view receipt merely because the path exists, rendering succeeded, or the expression is familiar.

The Core cannot observe or authenticate Codex image-tool calls. It labels successful receipts `viewed_reported` with `external_tool_receipt_not_machine_authenticated`. These declarations must match the real tool trace; they are not an independently certified verification score. All candidates without receipts remain `not_viewed`. For incomplete text-only formulas, record an omission rather than claiming a check that did not occur.

## Final disclosure

Base coverage statements on `reading-status`, not memory. Distinguish `plan_complete` from `complete_text_delivery`; completing Quick or Standard does not mean the entire document was read. `covered_pages` means at least one complete chunk returned, while `fully_covered_pages` means all extracted chunks on that page returned. Section status includes descendant sections, so overlapping hierarchical counts must not be added together.

Give a brief mode/read-count/page summary, relevant unread sections or appendix, and which important formulas/tables were actually viewed or left unverified. Candidate counts are heuristic, not a certified inventory of every mathematical object. Even 100% text delivery is not complete visual verification or proof that every claim was understood. Avoid an unqualified claim of complete PDF analysis when text, empty extraction pages, or relevant visual evidence remain uncovered.
