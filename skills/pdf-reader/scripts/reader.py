"""全局 Skill 的固定缓存启动入口；业务逻辑仍由安装的 CLI 处理。"""

import sys

from pdf_reader.cli import main as cli_main


CACHE_DIR = r"C:\Users\26214\.cache\pdf-reader"


def main(arguments: list[str] | None = None) -> None:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    arguments = sys.argv[1:] if arguments is None else arguments
    # argparse 接受长选项缩写，也必须拒绝 --cache 等覆盖写法。
    if any(
        arg.startswith("--") and arg != "--" and "--cache-dir".startswith(arg.split("=", 1)[0])
        for arg in arguments
    ):
        raise SystemExit(f"PDF Reader 全局 Skill 使用固定缓存：{CACHE_DIR}，不能覆盖 --cache-dir")
    cli_main(["--cache-dir", CACHE_DIR, *arguments])


if __name__ == "__main__":
    main()
