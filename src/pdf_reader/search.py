"""无外部索引的本地相关性检索。"""

import json
from dataclasses import asdict

from .evidence import assess_evidence
from .models import Document, SearchHit, SearchResult
from .retrieval import rank_chunks
from .tokens import estimate_tokens


def _snippet(markdown: str, budget: int) -> str:
    if len(markdown) <= budget:
        return markdown
    # 优先在段落或句子结束处截断，同时避免只返回很短的开头。
    start = max(1, int(budget * 0.6))
    for boundary in ("\n\n", "\n", ". ", "。", "; "):
        end = markdown.rfind(boundary, start, budget)
        if end >= start:
            return markdown[:end + len(boundary)].rstrip()
    for boundary in ("\n\n", "\n", ". ", "。", "; ", " "):
        end = markdown.rfind(boundary, 1, budget)
        if end >= max(1, budget // 4):
            return markdown[:end + len(boundary)].rstrip()
    return markdown[:budget].rstrip()


def _budgets(chunks: list, max_chars: int) -> list[int]:
    # 排名越高得到的空间越多，但首条不能独占 max_chars。
    if not chunks:
        return []
    weights = [1 / (index + 2) for index in range(len(chunks))]
    total = sum(weights)
    distributable = max_chars - len(chunks)
    budgets = [1 + int(distributable * weight / total) for weight in weights]
    for index in range(max_chars - sum(budgets)):
        budgets[index % len(budgets)] += 1
    return budgets


def search_chunks(
    document: Document, query: str, top_k: int = 5, max_chars: int = 2000
) -> SearchResult:
    if top_k < 1 or max_chars < 1:
        raise ValueError("top_k 和 max_chars 必须大于 0")
    ranked = rank_chunks(document.chunks, query)[:min(top_k, max_chars)]

    hits: list[SearchHit] = []
    unused = 0
    for (score, chunk), budget in zip(ranked, _budgets(ranked, max_chars)):
        snippet = _snippet(chunk.markdown, budget + unused)
        hits.append(
            SearchHit(
                chunk_id=chunk.id,
                section=chunk.section,
                page_number=chunk.page_number,
                score=score,
                markdown=snippet,
                truncated=len(snippet) < len(chunk.markdown),
                evidence_warnings=assess_evidence(chunk.markdown, query),
            )
        )
        unused += budget - len(snippet)

    full_tokens = estimate_tokens(document.full_markdown())
    # 比较实际会交给 AI 的查询、命中元数据和正文，而不只统计片段正文。
    returned_tokens = estimate_tokens(json.dumps(
        {"document_id": document.id, "query": query, "hits": [asdict(hit) for hit in hits]},
        ensure_ascii=False,
    ))
    return SearchResult(
        document_id=document.id,
        query=query,
        hits=hits,
        estimated_full_tokens=full_tokens,
        estimated_returned_tokens=returned_tokens,
        estimated_saved_tokens=max(0, full_tokens - returned_tokens),
        estimated_reduction_percent=round(
            max(0.0, 100 * (1 - returned_tokens / full_tokens)), 1
        ) if full_tokens else 0.0,
    )
