"""轻量检索评分；只使用现有 Markdown 和块元数据。"""

import math
import re
from collections import Counter

from .models import Chunk


WORD = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
TARGET = re.compile(r"\b(table|figure|fig\.?|section)\s*(\d+(?:\.\d+)*)|([表图])\s*(\d+)|第\s*(\d+(?:\.\d+)*)\s*节", re.I)
CAPTION = re.compile(r"^\s*(?:#+\s*)?(table|figure|fig\.?)\s*(\d+)\b", re.I | re.M)
TERMS = {
    "缩放点积注意力": "scaled dot product attention",
    "自注意力": "self attention",
    "位置编码": "positional encoding",
    "编码器": "encoder",
    "解码器": "decoder",
    "循环层": "recurrent layer",
    "循环": "recurrent",
    "顺序操作": "sequential operations",
    "路径长度": "path length",
    "训练成本": "training cost",
    "梯度": "gradients",
    "翻译": "translation",
    "公式": "formula",
}


def _words(text: str) -> list[str]:
    return WORD.findall(text.casefold())


def _plain(text: str) -> str:
    return " ".join(_words(text))


def _query_terms(query: str) -> list[str]:
    expanded = query.casefold()
    for chinese, english in TERMS.items():
        if chinese in query:
            expanded += " " + english
    return list(dict.fromkeys(_words(expanded)))


def _target(query: str) -> tuple[str, str] | None:
    match = TARGET.search(query)
    if not match:
        section = re.match(r"\s*(\d+\.\d+(?:\.\d+)*)\b", query)
        return ("section", section.group(1)) if section else None
    if match.group(1):
        kind = match.group(1).rstrip(".").casefold()
        kind = "figure" if kind == "fig" else kind
        return kind, match.group(2)
    if match.group(3):
        return ("table" if match.group(3) == "表" else "figure"), match.group(4)
    return "section", match.group(5)


def _phrase_bonus(query: str, chunk: Chunk) -> float:
    # 相邻词组属于补充分；不会像原始词频那样被反复出现的常用词支配。
    words = [word for word in _query_terms(query) if word.isascii() and len(word) > 1]
    phrases = {" ".join(words[i:i + size]) for size in (2, 3, 4)
               for i in range(len(words) - size + 1)}
    text = _plain(chunk.markdown)
    title = _plain(chunk.section.rsplit(" / ", 1)[-1])
    return sum(2.0 * (len(phrase.split()) - 1) if phrase in text else 0.8 for phrase in phrases
               if phrase in text or phrase in title)


def _target_bonus(query_target: tuple[str, str] | None, chunk: Chunk) -> float:
    if query_target is None:
        return 0.0
    kind, number = query_target
    if kind == "section":
        section = chunk.section.casefold()
        exact = re.search(rf"(?<![\d.]){re.escape(number)}(?![\d.])", section)
        child = re.search(rf"(?<![\d.]){re.escape(number)}\.\d+", section)
        return 90.0 if exact else 35.0 if child else 0.0
    captions = [("figure" if name.casefold().startswith("fig") else "table", n)
                for name, n in CAPTION.findall(chunk.markdown)]
    if (kind, number) in captions:
        return 100.0
    return -15.0 if any(name == kind for name, _ in captions) else 0.0


def rank_chunks(chunks: list[Chunk], query: str) -> list[tuple[int, Chunk]]:
    terms = _query_terms(query)
    if not terms:
        raise ValueError("检索词不能为空")
    if not chunks:
        return []

    bodies = [chunk.markdown.casefold() for chunk in chunks]
    counts = [Counter(_words(body)) for body in bodies]
    lengths = [sum(count.values()) for count in counts]
    average = sum(lengths) / len(lengths) or 1
    titles = [chunk.section.rsplit(" / ", 1)[-1].casefold() for chunk in chunks]
    document_frequency = {
        term: sum((term in body or term in title if not term.isascii()
                   else count[term] > 0 or term in title)
                  for body, title, count in zip(bodies, titles, counts))
        for term in terms
    }
    query_target = _target(query)
    first_in_section = {}
    for chunk in chunks:
        first_in_section.setdefault(chunk.section, chunk.id)
    ranked = []
    for chunk, body, title, count, length in zip(chunks, bodies, titles, counts, lengths):
        score = 0.0
        caption = chunk.markdown.split("\n", 1)[0].casefold()
        for term in terms:
            frequency = body.count(term) if not term.isascii() else count[term]
            if not frequency and term not in title:
                continue
            idf = math.log1p((len(chunks) - document_frequency[term] + 0.5)
                             / (document_frequency[term] + 0.5))
            if frequency:
                score += idf * frequency * 2.8 / (frequency + 1.8 * (0.5 + 0.5 * length / average))
            if term in title:
                score += 2.0 * idf
            if term in caption:
                score += 1.2 * idf
        score += _phrase_bonus(query, chunk)
        score += _target_bonus(query_target, chunk)
        if query_target and query_target[0] == "section" and chunk.id == first_in_section[chunk.section]:
            if re.search(rf"(?<![\d.]){re.escape(query_target[1])}(?![\d.])", title):
                score += 20.0
        if score > 0:
            ranked.append((round(score * 100), chunk))
    ranked.sort(key=lambda item: (-item[0], item[1].page_number, item[1].id))
    return ranked
