"""运行可靠性：固定缓存启动、PNG 写入失败和并发发布。"""

import importlib.util
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf
import pytest

from pdf_reader.render import render_pdf_page


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "input" / "Attention Is All You Need.pdf"
LAUNCHER = ROOT / "skills" / "pdf-reader" / "scripts" / "reader.py"


def test_render_denied_write_reports_destination(tmp_path, monkeypatch):
    original_open = Path.open

    def denied_png(path, *args, **kwargs):
        if path.name.endswith(".tmp.png"):
            raise PermissionError("Permission denied: sandbox write")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", denied_png)
    with pytest.raises(OSError, match="页面图片写入失败.*权限"):
        render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert not list(tmp_path.glob("*.png"))


@pytest.mark.parametrize("cleanup_denied", [False, True])
def test_render_failed_publish_cleans_temp_and_preserves_error(tmp_path, monkeypatch, cleanup_denied):
    def blocked_replace(path, target):
        raise PermissionError("target is locked")

    monkeypatch.setattr(Path, "replace", blocked_replace)
    if cleanup_denied:
        def blocked_cleanup(path, *args, **kwargs):
            raise PermissionError("cleanup denied")

        monkeypatch.setattr(Path, "unlink", blocked_cleanup)
    with pytest.raises(OSError, match="页面图片写入失败.*target is locked"):
        render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert len(list(tmp_path.glob("*.tmp.png"))) == int(cleanup_denied)


def test_concurrent_render_publishes_valid_png_without_temp_files(tmp_path):
    def render(_):
        # PyMuPDF 不支持多线程渲染；并发消费者使用独立进程。
        result = subprocess.run(
            [sys.executable, "-c",
             "import json,sys; from pathlib import Path; from dataclasses import asdict; "
             "from pdf_reader.render import render_pdf_page; "
             "print(json.dumps(asdict(render_pdf_page(Path(sys.argv[1]),Path(sys.argv[2]),'a'*64,5,1.0,None))))",
             str(PAPER), str(tmp_path)],
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            text=True, encoding="utf-8", capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(render, range(4)))
    assert len({result["image_path"] for result in results}) == 1
    assert pymupdf.Pixmap(results[0]["image_path"]).width > 0
    assert len(list(tmp_path.glob("*.png"))) == 1


def test_render_reuses_concurrent_winner_on_locked_replace(tmp_path, monkeypatch):
    def concurrent_winner(path, target):
        target.write_bytes(path.read_bytes())
        raise PermissionError("another reader holds the completed target")

    monkeypatch.setattr(Path, "replace", concurrent_winner)
    result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert result.cache_hit
    assert pymupdf.Pixmap(result.image_path).width > 0
    assert not list(tmp_path.glob("*.tmp.png"))


def test_render_does_not_accept_corrupt_concurrent_target(tmp_path, monkeypatch):
    def corrupt_target(path, target):
        target.write_bytes(b"not a PNG")
        raise PermissionError("target is locked")

    monkeypatch.setattr(Path, "replace", corrupt_target)
    with pytest.raises(OSError, match="页面图片写入失败.*target is locked"):
        render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert not list(tmp_path.glob("*.tmp.png"))


def test_launcher_fixes_cache_and_rejects_override(monkeypatch):
    spec = importlib.util.spec_from_file_location("reader_launcher", LAUNCHER)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    calls = []
    monkeypatch.setattr(launcher, "cli_main", calls.append)
    launcher.main(["search", "doc", "formula"])
    assert calls == [["--cache-dir", r"C:\Users\26214\.cache\pdf-reader", "search", "doc", "formula"]]
    for flag in ("--cache-dir", "--cache-dir=elsewhere", "--cache", "--cache-d=elsewhere"):
        with pytest.raises(SystemExit, match="固定缓存"):
            launcher.main([flag, "elsewhere", "outline", "doc"])
    assert len(calls) == 1


def test_launcher_error_is_utf8_in_gbk_terminal():
    result = subprocess.run(
        [sys.executable, str(LAUNCHER), "--cache", "project-cache", "outline", "doc"],
        env={**os.environ, "PYTHONIOENCODING": "gbk"},
        text=True, encoding="utf-8", capture_output=True,
    )
    assert result.returncode != 0
    assert "固定缓存" in result.stderr
    assert "Traceback" not in result.stderr
