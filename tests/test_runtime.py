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
PUBLISH_METHOD = "rename" if os.name == "nt" else "replace"


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

    monkeypatch.setattr(Path, PUBLISH_METHOD, blocked_replace)
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


@pytest.mark.skipif(os.name != "nt", reason="Windows no-overwrite rename and sharing semantics")
@pytest.mark.parametrize("hold_read_handle", [False, True])
def test_windows_late_publisher_preserves_complete_winner(tmp_path, monkeypatch, hold_read_handle):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handles, writers, winner = [], [], {}
    original_open = Path.open
    original_rename, original_replace = Path.rename, Path.replace

    def tracked_open(path, *args, **kwargs):
        stream = original_open(path, *args, **kwargs)
        if path.name.endswith(".tmp.png") and args and args[0] == "xb":
            writers.append(stream)
        return stream

    def publish(path, target, operation):
        # Another process wins after this caller's cache check, before publication.
        assert writers and all(stream.closed for stream in writers)
        data = path.read_bytes()
        assert data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82")
        assert pymupdf.Pixmap(data).width > 0
        target.write_bytes(data)
        winner.update(path=target, data=data, inode=target.stat().st_ino)
        if hold_read_handle:
            # Shared readers are allowed, DELETE sharing is deliberately absent.
            handle = kernel.CreateFileW(str(target), 0x80000000, 1, None, 3, 0x80, None)
            assert handle != wintypes.HANDLE(-1).value, ctypes.get_last_error()
            handles.append(handle)
        return operation(path, target)

    monkeypatch.setattr(Path, "open", tracked_open)
    monkeypatch.setattr(Path, "rename", lambda path, target: publish(path, target, original_rename))
    monkeypatch.setattr(Path, "replace", lambda path, target: publish(path, target, original_replace))
    try:
        result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
        assert result.cache_hit
        assert winner["path"].stat().st_ino == winner["inode"]
        assert winner["path"].read_bytes() == winner["data"]
        assert not list(tmp_path.glob("*.tmp.png"))
        assert len(list(tmp_path.glob("*.png"))) == 1
    finally:
        for handle in handles:
            assert kernel.CloseHandle(handle)


@pytest.mark.parametrize("corruption", ["garbage", "truncated"])
def test_corrupt_png_cache_hit_is_not_accepted(tmp_path, corruption):
    result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    image = Path(result.image_path)
    image.write_bytes(b"not a PNG" if corruption == "garbage" else image.read_bytes()[:32])
    with pytest.raises(OSError, match="缓存的页面图片无法访问"):
        render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert not list(tmp_path.glob("*.tmp.png"))


def test_cache_hit_access_denial_remains_an_error(tmp_path, monkeypatch):
    result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    def blocked_read(path):
        assert path == Path(result.image_path)
        raise PermissionError("persistent access denial")
    monkeypatch.setattr("pdf_reader.render._read_png", blocked_read)
    with pytest.raises(OSError, match="缓存的页面图片无法访问"):
        render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert not list(tmp_path.glob("*.tmp.png"))


@pytest.mark.skipif(os.name != "nt", reason="Windows file-handle sharing semantics")
@pytest.mark.parametrize("exclusive", [False, True])
def test_windows_cache_read_with_real_delete_or_exclusive_handle(tmp_path, exclusive):
    import ctypes
    from ctypes import wintypes

    result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    image = Path(result.image_path)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # A rename-capable handle has DELETE access; it can still share ordinary reads.
    access, sharing = (0x80000000, 0) if exclusive else (0x10000, 3)
    handle = kernel.CreateFileW(str(image), access, sharing, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value, ctypes.get_last_error()
    try:
        with pytest.raises(PermissionError):
            image.read_bytes()  # CRT open lacks FILE_SHARE_DELETE even in the non-exclusive case.
        if exclusive:
            with pytest.raises(OSError, match="缓存的页面图片无法访问"):
                render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
        else:
            cached = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
            assert cached.cache_hit and cached.pixel_width == result.pixel_width
        assert not list(tmp_path.glob("*.tmp.png"))
    finally:
        assert kernel.CloseHandle(handle)


def test_render_reuses_concurrent_winner_on_locked_replace(tmp_path, monkeypatch):
    def concurrent_winner(path, target):
        target.write_bytes(path.read_bytes())
        raise PermissionError("another reader holds the completed target")

    monkeypatch.setattr(Path, PUBLISH_METHOD, concurrent_winner)
    result = render_pdf_page(PAPER, tmp_path, "a" * 64, 5, 1.0, None)
    assert result.cache_hit
    assert pymupdf.Pixmap(result.image_path).width > 0
    assert not list(tmp_path.glob("*.tmp.png"))


def test_render_does_not_accept_corrupt_concurrent_target(tmp_path, monkeypatch):
    def corrupt_target(path, target):
        target.write_bytes(b"not a PNG")
        raise PermissionError("target is locked")

    monkeypatch.setattr(Path, PUBLISH_METHOD, corrupt_target)
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
