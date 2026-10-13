"""轻量证据风险提示；没有命中规则不代表内容已经可靠。"""

import re


IMAGE_LINK = re.compile(r"!\[[^]]*\]\([^)]+\)")
FORMULA_QUERY = re.compile(
    r"formula|equation|sqrt|sine|cosine|positional encoding|scaled dot.product|公式|方程|位置编码|根号",
    re.IGNORECASE,
)
FORMULA_CONTEXT = re.compile(
    r"matrix of outputs as|sine and cosine functions|mathematical formula|equation\s*\(",
    re.IGNORECASE,
)
VISUAL_QUERY = re.compile(
    r"\b(?:figure|diagram|image|visuali[sz]ation|colou?rs?|arrows?|lines?|layout|spatial)\b|图片|图像|图示|结构图|连线|颜色|可视化|图\s*\d+",
    re.IGNORECASE,
)


def assess_evidence(markdown: str, query: str) -> list[str]:
    warnings: list[str] = []
    if IMAGE_LINK.search(markdown) and (FORMULA_QUERY.search(query) or FORMULA_CONTEXT.search(markdown)):
        warnings.append("formula_image")

    # 空单元格和拆开的列头常伴随复杂 PDF 表格的列错位；只提示复核。
    table_rows = [line for line in markdown.splitlines() if line.startswith("|") and line.count("|") >= 4]
    if len(table_rows) >= 3 and any("||" in line for line in table_rows):
        warnings.append("table_structure")

    if VISUAL_QUERY.search(query):
        warnings.append("visual_detail")
    return warnings
