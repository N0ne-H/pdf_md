# PDF Reader（第一阶段）

本地 PDF 智能阅读引擎：先把 PDF 转成带原始页码的 Markdown 并缓存，之后按标题查看目录、按关键词取少量片段。只有明确执行 `export` 时才输出全文。当前支持可提取文字的 PDF，不含 OCR、网页界面、远程服务和向量检索。

## 项目结构

```text
src/pdf_reader/
  models.py      页面、标题、文本块等数据模型
  parser.py      PyMuPDF4LLM 逐页解析
  chunking.py    按标题、段落和页码分块
  cache.py       SHA-256 缓存
  search.py      关键词排序和长度限制
  tokens.py      Token 粗估
  service.py     Core 公共接口
  cli.py         命令行适配器
docs/architecture.md  接口与依赖方向
tests/                pytest 测试
pdf_to_md.py           旧命令的兼容入口
input/、output/        输入和导出示例目录
```

CLI 只负责读取参数、输出 JSON；`ReaderService` 负责业务编排。未来的 MCP Adapter 可以直接调用相同的服务接口。[接口设计](docs/architecture.md)中列出数据模型与调用方式。

## 安装

建议使用已有的 `pdf-md-v1` Conda 环境和 Python 3.11：

```powershell
conda activate pdf-md-v1
python -m pip install -e ".[dev]"
```

仅使用程序、不运行测试时，也可以执行 `python -m pip install -r requirements.txt`。`-e` 是可编辑安装：修改 `src/` 中的 Python 文件后，无需反复安装本项目。

## 五个命令

先将待处理 PDF 放入 `input/`，再在项目根目录运行。示例中的 `DOC_ID` 是 `ingest` 输出的 `document_id`，请替换成实际的 64 位 ID。

```powershell
python -m pdf_reader ingest "input/南科大TRAE新手带练手册_吴伟豪.pdf"
python -m pdf_reader outline DOC_ID
python -m pdf_reader search DOC_ID "关键词" --top-k 3 --max-chars 1200
python -m pdf_reader read DOC_ID c000001
python -m pdf_reader export DOC_ID -o "output/手册.md"
```

安装后，也可把 `python -m pdf_reader` 换成 `pdf-reader`。使用其他缓存目录时，把 `--cache-dir 路径` 放在子命令前面。

`ingest` 返回 `cache_hit`、页数、块数及全文 Token 估算。同一 PDF 内容和解析配置再次导入时，`cache_hit` 为 `true`。可用 `--chunk-size 1200` 调整块上限，或用 `--no-images` 关闭图片提取；配置改变会生成不同文档 ID。缓存位于 `.pdf_reader_cache/`，不会提交到 Git。

`outline` 返回标题层级和 PDF 原始页码。`search` 只返回命中的片段、章节、页码和块 ID；`max_chars` 限制所有片段正文的总字符数，JSON 元数据不在限制内。`read` 用块 ID 读取单块。CLI 的 JSON 输出使用 UTF-8。`export` 才拼接所有页面，并把图片复制到 Markdown 旁边的 `images/文档ID前缀/` 目录；正文中插入 `<!-- PDF page N -->` 标记，便于核对原页。

旧命令仍可使用，内部也调用同一个 Core：

```powershell
python pdf_to_md.py "input/南科大TRAE新手带练手册_吴伟豪.pdf"
```

## Token 估算与测试

检索结果包含 `estimated_full_tokens`、`estimated_returned_tokens`、`estimated_saved_tokens` 和 `estimated_reduction_percent`。估算把 ASCII 字符约按四个字符一个 Token、中文等非 ASCII 字符约按一个字符一个 Token 计算，只适合比较输入量；实际模型的 tokenizer 可能给出不同数字。全文侧统计导出的 Markdown；检索侧统计查询、命中元数据和片段正文，不含外部提示词及估算字段本身。

```powershell
python -m pytest -q
```

测试覆盖逐页解析、表格和图片、分块页码、缓存命中、配置变化、检索上限、CLI、全文导出和损坏 PDF。PDF 的复杂版面仍可能影响标题、表格与阅读顺序的识别，建议用自己的文件抽查导出效果。

## 学习提示

- `@dataclass` 自动生成数据类的构造方法；`frozen=True` 防止解析配置和单个块被意外改写。
- `Path` 代替手工拼接路径，兼容 Windows 路径和中文文件名。
- `with pymupdf.open(...)` 在离开代码块时关闭 PDF。
- `sha256` 对文件内容计算摘要；再把配置序列化为排序稳定的 JSON，共同生成缓存 ID。
- Core 返回数据对象，CLI 最后才序列化为 JSON，因此第二阶段可以复用 Core 而不用解析终端输出。
