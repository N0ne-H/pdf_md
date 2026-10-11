# PDF 转 Markdown（V1）

使用 `pymupdf4llm` 将单个 PDF 转成 Markdown。程序尽可能保留标题、段落、阅读顺序和表格，并将识别到的图片保存到 Markdown 旁边的 `images/` 文件夹。V1 面向可以直接提取文字的 PDF，不使用 OCR，也不单独识别数学公式。

## 项目结构

```text
pdf_to_md.py       命令行程序
requirements.txt   Python 依赖
input/             放入待转换的 PDF
output/            默认输出目录
```

## 安装与运行

建议使用 Python 3.10 或更新版本。在项目目录执行：

```powershell
python -m pip install -r requirements.txt
python pdf_to_md.py input/example.pdf
```

默认会生成 `output/example.md`；识别到图片时会保存到 `output/images/`。也可以指定输出文件：

```powershell
python pdf_to_md.py input/example.pdf -o output/notes.md
```

图片会保存在所指定 Markdown 文件同级的 `images/` 文件夹中，Markdown 引用使用相对路径。

## 检查转换效果

打开生成的 `.md`，检查标题、段落顺序、表格，以及图片链接。PDF 排版差异可能影响这些元素的识别。扫描件没有文字层时，V1 不会通过 OCR 提取其文字。

运行自带的简单测试：

```powershell
python -m unittest discover -s tests -v
```
