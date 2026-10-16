"""只规划元数据，以成功返回事件计算阅读覆盖；图片查看来自外部工具回执。"""

import json
import re
import uuid
from dataclasses import asdict
from pathlib import Path

from .cache import CacheStore
from .evidence import assess_evidence


MODES = ("quick", "standard", "deep")
IMAGE = re.compile(r"!\[[^]]*\]\(([^)]+)\)")
APPENDIX = re.compile(r"appendix|appendices|supplement|附录|补充材料", re.I)
REFERENCES = re.compile(r"(?:\*\*|^|\n)\s*(?:References|Bibliography|参考文献)\s*(?:\*\*|$|\n)", re.I)
OVERVIEW = re.compile(r"abstract|introduction|contribution|result|conclusion|摘要|引言|贡献|结果|结论|总结|关于本", re.I)
METHOD = re.compile(r"method|approach|architectur|model|attention|encoder|decoder|embedding|positional|feed.forward|方法|模型|架构|算法|机制", re.I)
EVIDENCE = re.compile(r"experiment|result|evaluation|limitation|discussion|实验|结果|评估|局限|讨论", re.I)
OVERVIEW_CUE = re.compile(r"(?:^|\n)\s*(?:\*\*|#+\s*)(abstract|introduction|conclusion|limitations?|摘要|引言|结论|局限性)(?=[ .。:：*]|$)", re.I)


def substantive(chunk):
    # 仅剔除能由本块章节名和页码完整解释的页眉/页脚，不按长度丢弃短公式或数值。
    text = re.sub(r"(?m)^\s*CHAPTER\s+[A-Z0-9 .]+\s*$", "", chunk.markdown)
    if not text.strip():
        return False
    normalize = lambda value: re.sub(r"[\W\d_]+", "", value).casefold()
    text = normalize(text)
    if not text:
        return True  # 纯数值/符号也可能是证据，不按字符类型过滤。
    for title in sorted(chunk.section.split(" / "), key=len, reverse=True):
        if normalize(title):
            text = text.replace(normalize(title), "", 1)
    return bool(text)


def inventory(document):
    chunks = []
    minimum_level = min((heading.level for heading in document.headings), default=0)
    roots = [heading for heading in document.headings if heading.level == minimum_level]
    title_root = roots[0].title if len(roots) == 1 and any(heading.level > minimum_level for heading in document.headings) else None
    reference_section = None
    after_references = False
    for chunk in document.chunks:
        role = "body"
        if APPENDIX.search(chunk.section):
            role = "appendix"
        elif REFERENCES.search(chunk.markdown) or re.search(r"references|bibliography|参考文献", chunk.section, re.I):
            reference_section = chunk.section
            after_references = True
            role = "references"
        elif reference_section == chunk.section:
            role = "references"
        elif chunk.section.split(" / ")[-1].strip(" *`_").lower() in ("contents", "table of contents", "目录"):
            role = "contents"
        elif after_references:
            role = "supplementary_after_references"
        elif document.headings and (chunk.section == "(无标题)" or chunk.section == title_root):
            role = "frontmatter"
        assets = []
        for index, match in enumerate(IMAGE.finditer(chunk.markdown), 1):
            assets.append({"asset_id": f"{chunk.id}:image:{index}", "kind": "image_candidate", "source": match.group(1)})
        rows = [line for line in chunk.markdown.splitlines() if line.startswith("|") and line.count("|") >= 4]
        if len(rows) >= 3:
            caption = re.search(r"(?:^|\n)\s*[*_]*(?:Table|表)\s*\d+", chunk.markdown, re.I)
            assets.append({"asset_id": f"{chunk.id}:table", "kind": "table_candidate", "source": None,
                           "numbered_caption": caption.group(0).strip(" * _\n") if caption else None})
        if re.search(r"\$\$|\\\[|\\\(", chunk.markdown):
            assets.append({"asset_id": f"{chunk.id}:math", "kind": "formula_text_candidate", "source": None})
        chunks.append({"chunk_id": chunk.id, "page_number": chunk.page_number, "section": chunk.section,
                       "characters": len(chunk.markdown), "role": role, "assets": assets,
                       "substantive": bool(assets) or substantive(chunk),
                       "evidence_warnings": assess_evidence(chunk.markdown, "")})
        prose = [line for line in chunk.markdown.splitlines()
                 if line.strip() and not line.startswith("|") and not IMAGE.fullmatch(line.strip())
                 and not line.strip().isdigit()]
        chunks[-1]["table_only"] = bool(rows) and not prose
        chunks[-1]["overview_cues"] = [match.group(1).lower() for match in OVERVIEW_CUE.finditer(chunk.markdown)]
        # 仅记录同节相邻页的明显英文断句；规划时只补一层，避免递归读完整节。
        previous = document.chunks[len(chunks) - 2] if len(chunks) > 1 else None
        tail = re.sub(r"\s+\d+\s*$", "", previous.markdown).rstrip(" *_\n") if previous else ""
        chunks[-1]["continues_previous"] = bool(previous and previous.section == chunk.section
            and chunk.page_number - previous.page_number == 1
            and re.search(r"(?:^|\n\n)(?:\*\*)?[a-z]", chunk.markdown.lstrip())
            and re.search(r"[a-zA-Z,]$", tail) and not tail.splitlines()[-1].startswith(("|", "!", "<")))
    return chunks


def select_chunks(metadata, mode):
    if mode not in MODES:
        raise ValueError(f"阅读模式必须为 {MODES}")
    body = [item for item in metadata if item["role"] == "body" and item.get("substantive", True)]
    groups = {}
    for item in body:
        groups.setdefault(item["section"], []).append(item)
    selected = set()
    if mode == "deep":
        selected = {item["chunk_id"] for item in metadata if item["role"] not in ("references", "contents")}
    elif mode == "standard":
        for items in groups.values():
            label = " / ".join(items[0]["section"].split(" / ")[1:]) or items[0]["section"]
            if METHOD.search(label) or EVIDENCE.search(label):
                selected.update(item["chunk_id"] for item in items)
            else:
                selected.add(max(items, key=lambda item: item["characters"])["chunk_id"])
                selected.add(items[-1]["chunk_id"])
        selected.update(item["chunk_id"] for item in body if item["assets"])
        selected.update(select_chunks(metadata, "quick"))
    else:
        if not body:
            body = [item for item in metadata if item["role"] == "frontmatter" and item.get("substantive", True)]
        paths = [item["section"].split(" / ") for item in body]
        prefix = 0
        for titles in zip(*paths):
            if len(set(titles)) != 1:
                break
            prefix += 1

        def relative(item):
            return item["section"].split(" / ")[prefix:]

        def representative(items, method=False):
            candidates = [item for item in items if not item.get("table_only", False)] or items
            if method:
                explanations = [item for item in candidates if not any(a.get("numbered_caption") for a in item["assets"])]
                candidates = explanations or candidates
            return max(candidates, key=lambda item: item["characters"])["chunk_id"]

        scholarly = any(re.search(r"abstract|introduction|contribution|conclusion|摘要|引言|贡献|结论|总结", (relative(item) or [""])[0], re.I)
                        or item.get("overview_cues") for item in body)
        if scholarly:
            for section, items in groups.items():
                label = " / ".join(relative(items[0]))
                if OVERVIEW.search(label) or METHOD.search(label) or EVIDENCE.search(label):
                    selected.add(representative(items, bool(METHOD.search(label) and not EVIDENCE.search(label))))
        else:
            # 移除公共包装祖先后按真实分支取样，不依赖固定标题深度。
            major = {}
            for item in body:
                parts = relative(item)
                key = parts[0] if parts else ""
                major.setdefault(key, []).append(item)
            selected.update(representative(items) for items in major.values())
        cues = {}
        for item in body:
            for cue in item.get("overview_cues", []):
                cues.setdefault((item["section"], cue), []).append(item)
        selected.update(representative(items) for items in cues.values())
        if len(selected) < min(3, len(body)):
            candidates = [item for item in body if not item.get("table_only", False)] or body
            selected.update(candidates[index]["chunk_id"] for index in (0, len(candidates) // 2, len(candidates) - 1))
        initial = set(selected)
        for previous, current in zip(body, body[1:]):
            if current.get("continues_previous") and previous["section"] == current["section"]:
                if current["chunk_id"] in initial:
                    selected.add(previous["chunk_id"])
                if previous["chunk_id"] in initial:
                    selected.add(current["chunk_id"])
    if not selected and metadata:
        selected = {metadata[0]["chunk_id"]}
    return [item["chunk_id"] for item in metadata if item["chunk_id"] in selected]


class ReadingTracker:
    def __init__(self, cache: CacheStore):
        self.cache = cache

    def catalog(self, doc_id, offset=0, limit=50):
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("元数据 offset 必须非负，limit 必须为 1–100")
        document = self.cache.load(doc_id)
        metadata = inventory(document)
        return {"document_id": doc_id, "total_chunks": len(metadata), "total_pages": len(document.pages),
                "offset": offset, "next_offset": offset + limit if offset + limit < len(metadata) else None,
                "chunks": metadata[offset:offset + limit]}

    def _save(self, path, state):
        path = Path(path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def start(self, doc_id, mode="standard", record=None, *, pages=None, section=None, scope=None):
        document = self.cache.load(doc_id)
        metadata = inventory(document)
        explicit = pages is not None or section is not None or scope is not None
        if explicit and mode != "deep":
            raise ValueError("显式范围仅用于 Deep；具体问题优先 search/read")
        if sum(value is not None for value in (pages, section, scope)) > 1:
            raise ValueError("pages、section、scope 只能选择一种")
        selected = select_chunks(metadata, mode)
        requested = None
        if pages is not None:
            first, last = pages
            if not 1 <= first <= last <= len(document.pages):
                raise ValueError("页码范围必须在原 PDF 页数内且起点不大于终点")
            selected = [item["chunk_id"] for item in metadata if first <= item["page_number"] <= last]
            requested = {"pages": [first, last]}
        elif section is not None:
            selected = [item["chunk_id"] for item in metadata
                        if item["section"] == section or item["section"].startswith(section + " / ")]
            if not selected:
                raise ValueError("章节范围没有匹配片段；请从 outline/chunks 核对完整章节路径")
            requested = {"section": section}
        elif scope is not None:
            if scope not in ("body", "all"):
                raise ValueError("scope 必须为 body 或 all")
            selected = [item["chunk_id"] for item in metadata if scope == "all" or item["role"] == "body"]
            requested = {"scope": scope}
        path = Path(record or Path.cwd() / ".pdf_reader_readings" / f"{uuid.uuid4().hex}.json").resolve()
        if path.exists():
            raise ValueError(f"阅读记录已存在，不覆盖：{path}")
        state = {"schema": 1, "reading_id": uuid.uuid4().hex, "document_id": doc_id, "mode": mode,
                 "planned_chunk_ids": selected, "events": []}
        if requested is not None:
            state["scope"] = requested
        state["coverage"] = self._status(path, state)
        self._save(path, state)
        return {"record_path": str(path), "document_id": doc_id, "mode": mode,
                "total_chunks": len(metadata), "total_pages": len(document.pages),
                "planned_chunk_ids": selected, "planned_chunks": len(selected),
                **({"scope": requested} if requested is not None else {}),
                "policy": {"quick": "Section evidence representatives; supplement missing task evidence",
                           "standard": "Main methods/results, body assets and substantive section representatives",
                           "deep": "Explicit scope or all except bibliography/contents"}[mode]}

    def load(self, record, doc_id=None):
        state = json.loads(Path(record).read_text(encoding="utf-8"))
        if state.get("schema") != 1 or state.get("mode") not in MODES:
            raise ValueError("无效的阅读记录")
        if doc_id is not None and state["document_id"] != doc_id:
            raise ValueError("阅读记录与文档 ID 不匹配")
        self.cache.load(state["document_id"])
        return state

    def record(self, path, event):
        state = self.load(path)
        state["events"].append({"sequence": len(state["events"]) + 1, **event})
        state["coverage"] = self._status(path, state)
        self._save(path, state)

    @staticmethod
    def progress(state):
        located, full, previews, gaps, views, renders = set(), set(), set(), {}, {}, []
        for event in state["events"]:
            located.update(event.get("located", []))
            previews.update(event.get("truncated", []))
            for chunk_id in event.get("full", []):
                full.add(chunk_id)
                gaps.pop(chunk_id, None)
            if event["operation"] == "gap":
                gaps[event["chunk_id"]] = event["reason"]
                full.discard(event["chunk_id"])
            if event["operation"] == "visual":
                views[event["asset_id"]] = event
            if event["operation"] == "render":
                renders.append(event)
        return located, full, previews, gaps, views, renders

    def next_batch(self, record, max_chunks=5, max_chars=6000):
        if not 1 <= max_chunks <= 20 or not 1 <= max_chars <= 20000:
            raise ValueError("每批 max_chunks 必须为 1–20，max_chars 必须为 1–20000")
        state = self.load(record)
        document = self.cache.load(state["document_id"])
        full = self.progress(state)[1]
        remaining = [chunk for chunk in document.chunks if chunk.id in state["planned_chunk_ids"] and chunk.id not in full]
        returned, budget, complete, truncated = [], max_chars, [], []
        for chunk in remaining:
            if len(returned) >= max_chunks:
                break
            if len(chunk.markdown) > budget and returned:
                break
            snippet = chunk.markdown[:budget]
            cut = len(snippet) < len(chunk.markdown)
            returned.append({**asdict(chunk), "truncated": cut, "evidence_warnings": assess_evidence(chunk.markdown, "")})
            returned[-1]["markdown"] = snippet
            (truncated if cut else complete).append(chunk.id)
            budget -= len(snippet)
            if cut:
                break
        event = {"operation": "read_batch", "located": complete + truncated, "full": complete, "truncated": truncated,
                 "returned_characters": max_chars - budget}
        return {"record_path": str(Path(record).resolve()), "document_id": document.id, "mode": state["mode"],
                "chunks": returned, "remaining_planned_after_output": len(remaining) - len(complete),
                "needs_full_read": truncated}, event

    def gap(self, record, chunk_id, reason):
        state = self.load(record)
        if chunk_id not in {chunk.id for chunk in self.cache.load(state["document_id"]).chunks} or not reason.strip():
            raise ValueError("缺口需要有效的片段 ID 和原因")
        return {"operation": "gap", "chunk_id": chunk_id, "reason": reason}

    def visual(self, record, asset_id, image_path=None, evidence=None, reason=None):
        state = self.load(record)
        document = self.cache.load(state["document_id"])
        asset = next(((item, asset) for item in inventory(document) for asset in item["assets"]
                      if asset["asset_id"] == asset_id), None)
        if asset is None:
            raise ValueError("找不到图表候选 ID")
        if image_path is None:
            if not reason or not reason.strip():
                raise ValueError("未核验的图表必须说明原因")
            return {"operation": "visual", "asset_id": asset_id, "status": "not_viewed", "reason": reason}
        if not evidence or not evidence.strip():
            raise ValueError("查看回执需要实际图像工具结果的 evidence 引用")
        image = Path(image_path).resolve()
        item, info = asset
        expected = (self.cache.folder(document.id) / info["source"]).resolve() if info["source"] else None
        renders = self.progress(state)[5]
        allowed_render = any(Path(event["image_path"]).resolve() == image and event["page_number"] == item["page_number"] for event in renders)
        if not image.is_file() or (image != expected and not allowed_render):
            raise ValueError("图片来源不属于这个候选，或对应 render-page 尚未记录")
        return {"operation": "visual", "asset_id": asset_id, "status": "viewed_reported",
                "image_path": str(image), "evidence": evidence, "source": "external_tool_receipt_not_machine_authenticated"}

    def _status(self, record, state):
        document = self.cache.load(state["document_id"])
        metadata = inventory(document)
        located, full, previews, gaps, views, renders = self.progress(state)
        pages = sorted({item["page_number"] for item in metadata if item["chunk_id"] in full})
        empty_pages = [page.number for page in document.pages if not any(item["page_number"] == page.number for item in metadata)]
        full_pages = [page.number for page in document.pages if page.number not in empty_pages and
                      all(item["chunk_id"] in full for item in metadata if item["page_number"] == page.number)]
        sections, stack = [], []
        for heading in document.headings:
            while stack and stack[-1][0] >= heading.level:
                stack.pop()
            stack.append((heading.level, heading.title))
            path = " / ".join(title for _, title in stack)
            members = [item for item in metadata if item["section"] == path or item["section"].startswith(path + " / ")]
            count = sum(item["chunk_id"] in full for item in members)
            sections.append({**asdict(heading), "section": path, "total_chunks": len(members), "read_chunks": count,
                             "located_chunks": sum(item["chunk_id"] in located for item in members),
                             "status": "no_extracted_chunks" if not members else "complete_text_returned" if count == len(members) else "partial" if count else "unread"})
        assets = [{**asset, "chunk_id": item["chunk_id"], "page_number": item["page_number"],
                   "status": views.get(asset["asset_id"], {}).get("status", "not_viewed"),
                   "receipt": views.get(asset["asset_id"])} for item in metadata for asset in item["assets"]]
        unread = [item for item in metadata if item["chunk_id"] not in full]
        return {"record_path": str(Path(record).resolve()), "document_id": document.id, "mode": state["mode"],
                "total_chunks": len(metadata), "read_chunk_ids": sorted(full), "located_chunk_ids": sorted(located),
                **({"scope": state["scope"]} if "scope" in state else {}),
                "truncated_preview_chunk_ids": sorted(previews), "read_chunks": len(full),
                "text_chunk_coverage_percent": round(100 * len(full) / len(metadata), 2) if metadata else 0,
                "total_pages": len(document.pages), "covered_pages": pages, "fully_covered_pages": full_pages,
                "pages_without_extracted_chunks": empty_pages, "sections": sections, "assets": assets,
                "planned_chunks": len(state["planned_chunk_ids"]),
                "remaining_planned_chunk_ids": [chunk_id for chunk_id in state["planned_chunk_ids"] if chunk_id not in full],
                "plan_complete": set(state["planned_chunk_ids"]) <= full,
                "complete_text_delivery": bool(metadata) and not unread and not empty_pages,
                "unread_chunks": [{"chunk_id": item["chunk_id"], "page_number": item["page_number"], "section": item["section"],
                                   "role": item["role"], "reason": gaps.get(item["chunk_id"], "not_yet_read" if item["chunk_id"] in state["planned_chunk_ids"] else "outside_mode_plan")} for item in unread],
                "rendered_pages": renders, "event_count": len(state["events"]),
                "coverage_basis": "Successfully output full CLI chunks, not cognitive understanding; external tool truncation must be logged as a gap. Visual receipts are external declarations, not authenticated by Core."}

    def status(self, record, details=True):
        result = self._status(record, self.load(record))
        if details:
            return result
        groups = {}
        for chunk in result["unread_chunks"]:
            key = (chunk["role"], chunk["reason"])
            group = groups.setdefault(key, {"role": key[0], "reason": key[1], "chunk_ids": [], "pages": []})
            group["chunk_ids"].append(chunk["chunk_id"])
            if chunk["page_number"] not in group["pages"]:
                group["pages"].append(chunk["page_number"])
        compact = {key: value for key, value in result.items() if key not in ("unread_chunks", "assets", "rendered_pages", "sections")}
        compact["unread_groups"] = list(groups.values())
        compact["sections"] = [{key: value for key, value in section.items() if key != "section"} for section in result["sections"]]
        compact["visuals"] = {"candidate_count": len(result["assets"]),
                              "viewed_reported_asset_ids": [asset["asset_id"] for asset in result["assets"] if asset["status"] == "viewed_reported"],
                              "not_viewed_asset_ids": [asset["asset_id"] for asset in result["assets"] if asset["status"] != "viewed_reported"],
                              "receipt_trust": "external_tool_receipt_not_machine_authenticated"}
        compact["rendered_page_numbers"] = sorted({event["page_number"] for event in result["rendered_pages"]})
        return compact
