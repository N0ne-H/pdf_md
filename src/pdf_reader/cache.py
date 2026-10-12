"""文件内容和解析配置决定缓存键；磁盘仅保存可重建的解析结果。"""

import hashlib
import json
import uuid
from dataclasses import asdict
from pathlib import Path

from .models import Chunk, Document, Heading, Page, ParseConfig


SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def document_id(source_sha256: str, config: ParseConfig, converter_version: str) -> str:
    # sort_keys 使相同配置总能得到相同的字节序列。
    payload = json.dumps(
        {
            "schema": SCHEMA_VERSION,
            "source_sha256": source_sha256,
            "config": asdict(config),
            "converter_version": converter_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CacheStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def folder(self, doc_id: str) -> Path:
        if len(doc_id) != 64 or any(c not in "0123456789abcdef" for c in doc_id):
            raise ValueError("无效的文档 ID")
        return self.root / doc_id

    def load(self, doc_id: str) -> Document:
        path = self.folder(doc_id) / "document.json"
        if not path.is_file():
            raise FileNotFoundError(f"缓存中找不到文档 {doc_id}，请先 ingest")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA_VERSION or data.get("id") != doc_id:
            raise ValueError(f"缓存版本或文档 ID 不匹配：{path}")
        return Document(
            id=data["id"],
            source_sha256=data["source_sha256"],
            source_name=data["source_name"],
            converter_version=data["converter_version"],
            config=ParseConfig(**data["config"]),
            pages=[Page(**item) for item in data["pages"]],
            headings=[Heading(**item) for item in data["headings"]],
            chunks=[Chunk(**item) for item in data["chunks"]],
        )

    def save(self, document: Document) -> None:
        folder = self.folder(document.id)
        folder.mkdir(parents=True, exist_ok=True)
        data = {"schema": SCHEMA_VERSION, **asdict(document)}
        path = folder / "document.json"
        temporary = folder / f"document-{uuid.uuid4().hex}.tmp"
        temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
