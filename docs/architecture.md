# 第一阶段接口设计

依赖方向为 `CLI → ReaderService → parser / chunker / cache / search`。第二阶段的 MCP Adapter 和 Skill 只需调用 `ReaderService`，不再实现 PDF 解析逻辑。

## 数据模型

- `ParseConfig`：分块上限、是否提取图片。它和转换器版本一起进入缓存键。
- `Page`：从 PDF 解析的单页 Markdown，保存 PDF 的 **1 起始原始页码**。
- `Heading`：标题层级、文字和所在页，用于 `outline`。
- `Chunk`：文档 ID、章节路径、原始页码、Markdown 正文和块 ID。块不跨页，避免页码含糊。
- `Document`：页面、目录和块的合集。全文仅在 `export` 时拼接输出。

## Core API

```python
service = ReaderService(cache_dir)
ingest = service.ingest(pdf_path, ParseConfig())
outline = service.outline(ingest.document_id)
results = service.search(ingest.document_id, "关键词", top_k=5, max_chars=2000)
chunk = service.read(ingest.document_id, "c000001")
path = service.export(ingest.document_id, output_path)
```

`ingest` 的文档 ID 是 PDF 内容 SHA-256、解析配置和转换器版本组成的 SHA-256。缓存保存页、目录、块和图片。相同内容与配置直接读取缓存；改动文件或配置会生成新 ID。

`search` 只返回命中的片段，`max_chars` 限制所有片段正文的合计长度；元数据和 JSON 标点不计入该上限。Token 数是启发式估算，比较完整 Markdown 与此次检索所需的查询、元数据和片段输入量，不能替代具体模型的 tokenizer。
