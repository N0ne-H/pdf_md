"""使用生成的 PDF 检查命令行转换流程。"""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf


SCRIPT = Path(__file__).resolve().parents[1] / "pdf_to_md.py"


class ConversionTest(unittest.TestCase):
    def test_default_output(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent / "output") as directory:
            pdf = Path(directory) / f"{Path(directory).name}.pdf"
            output = SCRIPT.parent / "output" / f"{pdf.stem}.md"
            document = pymupdf.open()
            document.new_page().insert_text((72, 72), "Default output")
            document.save(pdf)
            document.close()
            try:
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), str(pdf)],
                    text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Default output", output.read_text(encoding="utf-8"))
            finally:
                output.unlink(missing_ok=True)

    def test_table_and_image_paths(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent / "output") as directory:
            folder = Path(directory)
            pdf = folder / "sample.pdf"
            output = folder / "markdown output" / "result.md"

            document = pymupdf.open()
            page = document.new_page(width=600, height=800)
            page.insert_text((72, 72), "Example Title", fontsize=20)
            page.insert_text((72, 110), "Body paragraph", fontsize=11)

            # 画出带边框的两列表格，便于表格检测。
            for x in (72, 192, 312):
                page.draw_line((x, 150), (x, 210))
            for y in (150, 180, 210):
                page.draw_line((72, y), (312, y))
            for x, y, text in (
                (78, 170, "Name"), (198, 170, "Value"),
                (78, 200, "Alpha"), (198, 200, "42"),
            ):
                page.insert_text((x, y), text, fontsize=11)

            pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 80), False)
            pixmap.clear_with(0xFF0000)
            page.insert_image(pymupdf.Rect(72, 250, 272, 380), pixmap=pixmap)
            document.save(pdf)
            document.close()

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(pdf), "-o", str(output)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            markdown = output.read_text(encoding="utf-8")
            self.assertIn("Example Title", markdown)
            self.assertIn("Body paragraph", markdown)
            self.assertRegex(markdown, r"\|\s*Name\s*\|\s*Value\s*\|")
            image_links = re.findall(r"!\[[^]]*\]\(([^)]+)\)", markdown)
            self.assertTrue(image_links, markdown)
            for link in image_links:
                self.assertTrue(link.startswith("images/"), link)
                self.assertTrue((output.parent / link).is_file(), link)

    def test_invalid_pdf(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent / "output") as directory:
            pdf = Path(directory) / "invalid.pdf"
            pdf.write_text("not a PDF", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(pdf)],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("无法打开 PDF", result.stderr)


if __name__ == "__main__":
    unittest.main()
