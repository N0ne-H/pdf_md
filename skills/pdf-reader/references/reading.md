# Reading modes and evidence coverage

Use the installed launcher from SKILL.md for every command below. Replace DOC_ID and RECORD_PATH with actual outputs. Do not concatenate the whole cached Markdown to plan a summary.

## Choose a scope

- Focused: specific PDF questions use `search` and full relevant `read` snippets, including necessary adjacent context. A request for a detailed derivation stays Focused; no `reading-start` is needed. Reuse evidence already delivered; refine retrieval only for missing evidence. Without a specific PDF requirement, ordinary knowledge questions need no PDF Reader.
- Quick: select a substantive representative from relevant problem/motivation/contribution, method subsections, results/evidence and conclusion/limitations headings. Manuals without paper headings use major-chapter representatives. Repeated heading-only fragments are skipped. Check actual content for all required roles and supplement missing evidence; this is a lightweight overview, not complete coverage. The plan grows with relevant structure rather than cutting off at ten blocks.
- Standard: cover main method/result sections fully, retain body image/table/formula candidates and substantive longest/end representatives elsewhere. Includes the Quick selection. Repeated heading-only fragments are skipped; sampled sections can remain partial. Verify necessary formula/table/image evidence and disclose gaps rather than equating candidate selection with verification.
- Deep: for explicit whole-document analysis, comprehensive comparison or full coverage of a specified range. Default keeps the existing body/frontmatter/appendix plan, excluding bibliography and contents. For body only use `--scope body`; for every extracted chunk including references and contents use `--scope all`. For a complete original PDF page range use `--pages FIRST LAST` (inclusive); for a complete section subtree use `--section 'exact / section / path'` from `chunks` metadata. These three scope options are mutually exclusive and Deep-only. Page/section scopes include every matching chunk regardless of heuristic role, including any references there. A page range cannot split a chunk; a section subtree may include supplementary material classified under the same heading, so inspect the scope when needed. Explicit all/range plans never apply the summary filters. Empty extracted pages remain unknown gaps even when the plan is complete.

Example: `reading-start DOC_ID --mode deep --pages 3 5 --compact` fully plans extracted chunks on original pages 3–5. `--scope all` is required for an unqualified request to cover every extracted part; do not silently exclude references/appendices. Use `--scope body` only when the user requests main-body coverage. Default Deep remains backward compatible; disclose excluded references/contents. New scope arguments never replan an existing record; resume it directly, or create a separate record for a different scope and disclose separate coverage.

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
