"""Tests for pdf_tool.py. Run with the plugin's own venv Python:

  tutor/.venv/Scripts/python.exe tutor/scripts/test_pdf_tool.py      (Windows)
  tutor/.venv/bin/python tutor/scripts/test_pdf_tool.py              (macOS / Linux)

Run any pdf_tool command once first (for example `info nonexistent.pdf`) to create the venv.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymupdf  # noqa: E402

import pdf_tool  # noqa: E402


def make_pdf(path):
    """Four pages: intro, definition, blank, more text. With a two-entry table of contents."""
    doc = pymupdf.open()
    texts = [
        "Chapter 1\nLimits\nA limit describes what a function approaches.",
        "The epsilon-delta definition\nFor every epsilon there is a delta.\nEpsilon comes first.",
        "",
        "Exercises\nFind a delta for each epsilon in the examples above.",
    ]
    for text in texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=11)
    doc.set_toc([[1, "Limits", 1], [2, "The definition", 2]])
    doc.save(path)
    doc.close()


class PdfToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = os.path.join(cls.tmp.name, "book.pdf")
        make_pdf(cls.pdf)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_parse_pages(self):
        self.assertEqual(pdf_tool.parse_pages("all", 4), [0, 1, 2, 3])
        self.assertEqual(pdf_tool.parse_pages("2", 4), [1])
        self.assertEqual(pdf_tool.parse_pages("1-2", 4), [0, 1])
        self.assertEqual(pdf_tool.parse_pages("1,3,9", 4), [0, 2])
        self.assertEqual(pdf_tool.parse_pages("3-99", 4), [2, 3])
        with self.assertRaises(SystemExit):
            pdf_tool.parse_pages("abc", 4)

    def test_info_reports_toc_and_pages_with_no_text(self):
        text = pdf_tool.info(self.pdf)
        self.assertIn("pages: 4", text)
        self.assertIn("Limits ... 1", text)
        self.assertIn("  The definition ... 2", text)  # indented one level
        self.assertIn("pages with almost no text (1; scans, images or blanks): 3", text)

    def test_info_is_compact_for_the_whole_book(self):
        # pi's version printed a table row per page; this must stay short
        self.assertLess(len(pdf_tool.info(self.pdf).splitlines()), 30)

    def test_search_finds_the_page_and_shows_context(self):
        text = pdf_tool.search(self.pdf, "epsilon comes first", literal=True)
        self.assertIn("=== Page 2", text)
        self.assertIn(">>> Epsilon comes first.", text)
        self.assertIn("1 match(es)", text)

    def test_search_is_case_insensitive_and_can_use_regex(self):
        self.assertIn("=== Page 1", pdf_tool.search(self.pdf, r"^LIM.TS$"))

    def test_search_limits_matches_and_pages(self):
        capped = pdf_tool.search(self.pdf, "e", literal=True, max_matches=2)
        self.assertIn("stopped after 2 matches", capped)
        only_page_one = pdf_tool.search(self.pdf, "epsilon", literal=True, pages="1")
        self.assertIn("No matches found", only_page_one)

    def test_search_reports_no_match_and_bad_regex(self):
        self.assertIn("No matches found", pdf_tool.search(self.pdf, "zebra", literal=True))
        with self.assertRaises(SystemExit):
            pdf_tool.search(self.pdf, "(")

    def test_extract_gives_the_requested_pages_only(self):
        text = pdf_tool.extract(self.pdf, "2")
        self.assertIn("--- Page 2 ---", text)
        self.assertIn("epsilon-delta definition", text)
        self.assertNotIn("Chapter 1", text)

    def test_extract_is_capped_and_says_so(self):
        text = pdf_tool.extract(self.pdf, "all", max_chars=60)
        self.assertIn("truncated at 60 characters", text)
        self.assertLess(len(text), 400)

    def test_render_writes_png_files_and_names_them(self):
        text = pdf_tool.render(self.pdf, "2")
        self.assertIn("PDF page 2 ->", text)
        path = text.splitlines()[0].split(" -> ", 1)[1]
        self.assertTrue(os.path.exists(path))
        with open(path, "rb") as f:
            self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n")

    def test_render_refuses_too_many_pages_and_empty_selections(self):
        with self.assertRaises(SystemExit):
            pdf_tool.render(self.pdf, "1-4", max_pages=2)
        with self.assertRaises(SystemExit):
            pdf_tool.render(self.pdf, "99")

    def test_the_private_venv_is_under_the_plugin_and_is_what_runs_these_tests(self):
        self.assertTrue(pdf_tool.venv_python().startswith(pdf_tool.VENV_DIR))
        self.assertTrue(pdf_tool.VENV_DIR.endswith(".venv"))
        self.assertTrue(pdf_tool.in_venv(), "run the tests with the plugin's venv Python (see the top of this file)")

    def test_missing_file(self):
        with self.assertRaises(SystemExit):
            pdf_tool.info(os.path.join(self.tmp.name, "nope.pdf"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
