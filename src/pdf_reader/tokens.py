"""轻量 Token 估算；不绑定任何模型的 tokenizer。"""

import math


def estimate_tokens(text: str) -> int:
    # 英文约四字符一 Token；中文等非 ASCII 字符粗略按一字符一 Token。
    ascii_count = sum(char.isascii() for char in text)
    return math.ceil(ascii_count / 4 + len(text) - ascii_count)
