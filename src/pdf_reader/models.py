"""Core 的数据模型；不包含 CLI 或具体终端输出。"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParseConfig:
    chunk_size: int = 1200
    extract_images: bool = True

    def __post_init__(self) -> None:
        if self.chunk_size < 1:
            raise ValueError("chunk_size 必须大于 0")


@dataclass(frozen=True)
class Page:
    number: int
    markdown: str


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    page_number: int


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    section: str
    page_number: int
    markdown: str


@dataclass
class Document:
    id: str
    source_sha256: str
    source_name: str
    converter_version: str
    config: ParseConfig
    pages: list[Page] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    source_path: str | None = None

    def full_markdown(self) -> str:
        # 页码注释放在正文中，导出后仍能追溯 PDF 原页。
        return "\n\n".join(
            f"<!-- PDF page {page.number} -->\n\n{page.markdown.strip()}"
            for page in self.pages
        ) + "\n"


@dataclass(frozen=True)
class IngestResult:
    document_id: str
    cache_hit: bool
    page_count: int
    chunk_count: int
    estimated_full_tokens: int


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    section: str
    page_number: int
    score: int
    markdown: str
    truncated: bool
    evidence_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RenderResult:
    document_id: str
    page_number: int
    image_path: str
    cache_hit: bool
    pixel_width: int
    pixel_height: int
    scale: float
    clip: tuple[float, float, float, float] | None


@dataclass(frozen=True)
class SearchResult:
    document_id: str
    query: str
    hits: list[SearchHit]
    estimated_full_tokens: int
    estimated_returned_tokens: int
    estimated_saved_tokens: int
    estimated_reduction_percent: float
