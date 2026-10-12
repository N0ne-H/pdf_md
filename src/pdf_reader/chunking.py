"""按 Markdown 标题和段落分块，每块严格属于一个 PDF 页面。"""

import re

from .models import Chunk, Heading, Page


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _split_long(text: str, limit: int):
    """长段落按空格优先切分；中文没有空格时按字符切分。"""
    while len(text) > limit:
        cut = text.rfind(" ", 0, limit + 1)
        if cut <= 0 or cut < limit // 2:
            cut = limit
        yield text[:cut].strip()
        text = text[cut:].strip()
    if text:
        yield text


def chunk_pages(
    document_id: str, pages: list[Page], limit: int
) -> tuple[list[Heading], list[Chunk]]:
    headings: list[Heading] = []
    chunks: list[Chunk] = []
    title_stack: list[tuple[int, str]] = []

    for page in pages:
        pending = ""

        def flush() -> None:
            nonlocal pending
            if pending:
                chunks.append(
                    Chunk(
                        id=f"c{len(chunks) + 1:06d}",
                        document_id=document_id,
                        section=" / ".join(title for _, title in title_stack) or "(无标题)",
                        page_number=page.number,
                        markdown=pending,
                    )
                )
                pending = ""

        def add_block(block: str) -> None:
            nonlocal pending
            for piece in _split_long(block, limit):
                candidate = f"{pending}\n\n{piece}" if pending else piece
                if len(candidate) > limit:
                    flush()
                pending = f"{pending}\n\n{piece}" if pending else piece

        for block in re.split(r"\n\s*\n+", page.markdown):
            lines: list[str] = []
            for line in block.strip().splitlines():
                match = HEADING.match(line)
                if not match:
                    lines.append(line)
                    continue
                if lines:
                    add_block("\n".join(lines))
                    lines = []
                flush()
                level = len(match.group(1))
                title = match.group(2).strip(" *`_")
                while title_stack and title_stack[-1][0] >= level:
                    title_stack.pop()
                title_stack.append((level, title))
                headings.append(Heading(level, title, page.number))
            if lines:
                add_block("\n".join(lines))
        flush()

    return headings, chunks
