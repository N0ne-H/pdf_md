"""无外部索引的关键词检索，适合第一阶段的小型本地文档。"""

import json
import re
from dataclasses import asdict

from .models import Document, SearchHit, SearchResult
from .tokens import estimate_tokens


def search_chunks(
    document: Document, query: str, top_k: int = 5, max_chars: int = 2000
) -> SearchResult:
    if top_k < 1 or max_chars < 1:
        raise ValueError("top_k 和 max_chars 必须大于 0")
    terms = list(dict.fromkeys(re.findall(r"[\w]+", query.casefold())))
    if not terms:
        raise ValueError("检索词不能为空")

    ranked = []
    for chunk in document.chunks:
        body = chunk.markdown.casefold()
        section = chunk.section.casefold()
        score = sum(body.count(term) + 2 * section.count(term) for term in terms)
        if score:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: (-item[0], item[1].page_number, item[1].id))

    hits: list[SearchHit] = []
    remaining = max_chars
    for score, chunk in ranked[:top_k]:
        if not remaining:
            break
        snippet = chunk.markdown[:remaining]
        hits.append(
            SearchHit(
                chunk_id=chunk.id,
                section=chunk.section,
                page_number=chunk.page_number,
                score=score,
                markdown=snippet,
                truncated=len(snippet) < len(chunk.markdown),
            )
        )
        remaining -= len(snippet)

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
