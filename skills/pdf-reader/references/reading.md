# Reading modes and evidence coverage

Use the installed launcher from SKILL.md for every command below. Replace DOC_ID and RECORD_PATH with actual outputs. Do not concatenate the whole cached Markdown to plan a summary.

## Focused evidence loop

Specific questions stay on `search`/`read`; do not start Quick, Standard or Deep to answer a local question. Codex judges evidence sufficiency; Core provides locations, full chunks and historical delivery tracking, without semantic scoring.

1. Identify what the answer needs: definitions, premises, formula explanation, numbered figure/table caption, comparison or limitation. Check **current-context evidence** first: retain document ID, chunk ID, original page and the actual available text. Use it for a new question only if the relevant original text is still accessible and sufficient.
2. Search missing concepts with the paper's terms, initially `search DOC_ID 'terms' --top-k 5 --max-chars 600`. This is a preview budget, not a correctness threshold; enlarge it if candidate distinctions are unclear. **Do not read all Top-5 hits** automatically. Select the needed complete chunks from their previews, pages and sections, then `read DOC_ID CHUNK_ID`. A useful untruncated preview can supply evidence, but a search event records location only, not a full-read event.
3. Check the actual evidence against the question before answering. A relevant first hit may omit a definition, hypothesis, formula dimensions or the figure caption. Search only the missing concept with distinctive terms from the question or retrieved text. Split a compound query when its components occur in different blocks. For an absent numbered figure/formula/table, search the number plus caption/technical terms; verify identity rather than choosing a similar object.
4. For a broken sentence, missing caption, list or table header, inspect same-section and adjacent-block metadata with paged `chunks DOC_ID --offset OFFSET --limit LIMIT`. Reuse metadata already available; page further only as needed. Use the returned order, original page and exact section path to choose neighbors; do not assume IDs are consecutive or that every adjacent block is relevant. The `search has no section filter` constraint means section narrowing is a Codex candidate-selection step, not an invented `search --section` flag. Read only the relevant missing neighbors, not an entire section or all nearby pages. If section metadata is misleading, return to distinctive terms/captions.
5. Repeat only while a concrete needed fact remains missing. Before answering, check that the necessary premises, explanation and source locations are present and that required visuals have actually been viewed. Text delivery alone does not verify formula images, table columns or figure relationships. Use the existing original-page visual rules below; if retrieval or viewing fails, disclose the specific gap and limit the answer to verified evidence. Do not stop merely because Top-5 was exhausted, or infer that a missing search hit is absent from the PDF.

### Reuse and recovery

Keep these three states separate:

|State|What it establishes|What it cannot establish|
|---|---|---|
|PDF parse cache|Unchanged PDF need not be reparsed|That Codex has read or remembers any block|
|Reading record|**historical delivery** from successful CLI outputs; gaps revoke coverage|That the original text remains in the current model context|
|Current-context evidence|The relevant text and source are presently accessible to Codex|Permanent availability after a session or context change|

For consecutive questions, reuse currently available evidence and request only missing relevant material. Do not resubmit a search preview or full read merely to repeat text already available. Reassess sufficiency for the new question; a reused chunk can be relevant yet incomplete.

After a new session, **context compaction**, unavailable originals or an external output truncation, recover needed text with explicit `read` even when the disk record says it was read. A saved stdout path or a short summary is a locator, not a substitute for inaccessible exact original evidence. Core does not enforce permanent read suppression. When actual delivery was truncated, record `reading-gap` in an existing record, then reread; loss of model context alone does not erase valid historical delivery.

**Do not fabricate delivery events** for locally skipped/reused chunks. If an existing reading task is being supplemented, attach its `--reading-record` to actual search/read/render calls; a reread records another actual output and unique coverage remains a set. No new `reading-start` is needed for Focused. Without an existing record, use normal untracked calls and keep question-specific source references in the conversation. Never claim document-wide coverage from this local evidence loop.

Example: a retrieved method paragraph refers to a separate architecture figure and an internal-time subsection. Read that paragraph, search the figure's caption and internal-time terms separately, then read the missing matches. For a subsequent question, reuse those exact paragraphs if still available; retrieve only the missing formula explanation or neighboring premise. After context loss, explicitly recover the originals instead of trusting read-history IDs.

## Choose a scope

- Focused: specific PDF questions use `search` and full relevant `read` snippets, including necessary adjacent context. A request for a detailed derivation stays Focused; no `reading-start` is needed. Reuse evidence already delivered; refine retrieval only for missing evidence. Without a specific PDF requirement, ordinary knowledge questions need no PDF Reader.
- Quick: select a substantive representative from relevant problem/motivation/contribution, method subsections, results/evidence and conclusion/limitations headings. Manuals without paper headings use major-chapter representatives. Repeated heading-only fragments are skipped. Check actual content for all required roles and supplement missing evidence; this is a lightweight overview, not complete coverage. The plan grows with relevant structure rather than cutting off at ten blocks.
- Standard: cover main method/result sections fully, retain body image/table/formula candidates and substantive longest/end representatives elsewhere. Includes the Quick selection. Repeated heading-only fragments are skipped; sampled sections can remain partial. Verify necessary formula/table/image evidence and disclose gaps rather than equating candidate selection with verification.
- Deep: for explicit whole-document analysis, comprehensive comparison or full coverage of a specified range. Default keeps the existing body/frontmatter/appendix plan, excluding bibliography and contents. For body only use `--scope body`; for every extracted chunk including references and contents use `--scope all`. For a complete original PDF page range use `--pages FIRST LAST` (inclusive); for a complete section subtree use `--section 'exact / section / path'` from `chunks` metadata. These three scope options are mutually exclusive and Deep-only. Page/section scopes include every matching chunk regardless of heuristic role, including any references there. A page range cannot split a chunk; a section subtree may include supplementary material classified under the same heading, so inspect the scope when needed. Explicit all/range plans never apply the summary filters. Empty extracted pages remain unknown gaps even when the plan is complete.

Example: `reading-start DOC_ID --mode deep --pages 3 5 --compact` fully plans extracted chunks on original pages 3–5. `--scope all` is required for an unqualified request to cover every extracted part; do not silently exclude references/appendices. Use `--scope body` only when the user requests main-body coverage. Default Deep remains backward compatible; disclose excluded references/contents. New scope arguments never replan an existing record; resume it directly, or create a separate record for a different scope and disclose separate coverage.

The automatic plan is a lexical suggestion. For a routine summary, start the compact reading task and check section labels as batches arrive. If structure is unclear or exclusions look unexpected, inspect `outline DOC_ID` once. Use paged `chunks DOC_ID --offset 0 --limit 50` when you need missing-block IDs or image/table candidates; it returns metadata only. Repeated headings, unheaded bibliography, or after-reference material may be classified imperfectly. Do not treat a metadata role or a candidate image as a guaranteed semantic classification. Add targeted `search`/`read` calls with the same record when important content is missing.

## Lean output for Standard and Deep

Use `--lean` on `reading-start`, `reading-next` and final `reading-status` for Standard/Deep. Quick may keep `--compact`. The default JSON and original Compact contract remain unchanged. `--lean` and `--compact` are mutually exclusive; an older installation without Lean must be updated or use the existing Compact workflow, not a different cache.

Lean start retains the record path, document identity, mode, explicit scope and plan counts. Retain that association: Lean batches omit repeated record/document/mode fields, but each chunk still contains its ID, original page, exact section, complete selected Markdown, `truncated` and `evidence_warnings`. The response still provides `remaining_planned_after_output` and `needs_full_read`. Read the full returned text before advancing, allocate adequate tool output budget, and handle truncation/gaps exactly as below. For resumption after context loss, query status first to recover identity/scope before consuming a Lean batch.

Lean final status separates `read_planned_chunks`/`remaining_planned_chunks` from document-wide `read_chunks`/`document_unread_chunks` and `unread_outside_plan_chunks`. `plan_complete` still does not mean `complete_text_delivery`. All active `gaps` retain chunk ID, original page and reason, including gaps outside the plan; `needs_full_read` lists unresolved truncated deliveries, not previews subsequently recovered in full. Empty extracted pages remain visible. `planned_visuals` counts only candidates in the current plan and retains the external-receipt trust label; a path/render is not a view, and receipt counts do not certify visual verification.

Use `reading-status RECORD_PATH --details --lean` when you need remaining IDs, document-wide omission/section detail, exact visual candidate paths/receipts, fully covered pages, historical previews or audit information. This returns the full existing detailed schema using compact JSON whitespace; it overrides the Lean projection. `--details --compact` is still supported. Persistent records retain all events and full coverage snapshots regardless of output format. Changing output flags never replans a record or marks hidden evidence delivered.

## Start, read, and resume

1. Run `reading-start DOC_ID --mode standard|deep --lean` (Quick uses `--mode quick --compact`). Standard is the CLI default. Optional `--record 'workspace\reading.json'` selects a task log; existing records are not overwritten. Retain the absolute `record_path`, document identity and scope.
2. Run `reading-next RECORD_PATH --max-chunks 5 --max-chars 6000 --lean` (Quick may use `--compact`). Read the returned batch before requesting the next one. Repeat until `remaining_planned_after_output` is zero, or consciously stop and disclose why. No single batch can request more than 20 chunks or 20,000 body characters. The character budget covers body text, not the full JSON; allocate enough tool output tokens to display it fully.
3. If `needs_full_read` is nonempty, use `read DOC_ID CHUNK_ID --reading-record RECORD_PATH` or increase the next batch budget within the allowed limit. A truncated preview remains unread.
4. At the end, run `reading-status RECORD_PATH --lean` (Quick may use `--compact`). Check remaining plan counts, active gaps/truncation, document-wide incompleteness and planned visual trust. For missing-block IDs, complete-section details or individual image receipts, use `reading-status RECORD_PATH --details --lean`. Original `--compact` still reports incomplete sections, omission groups and document-wide visual counts; `--details --compact` keeps full details. Omit both output flags for the legacy response layout. The task file also stores the detailed computed coverage snapshot. Reuse the same file to resume later, including from another cwd. Use one writer at a time per record; separate tasks get separate records.

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
