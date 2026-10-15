#!/usr/bin/env python3
"""PDF tools for the tutor plugin: info, search, extract.

Usage:
  python pdf_tool.py info    PATH
  python pdf_tool.py search  PATH QUERY [--literal] [--context N] [--max-matches N] [--pages SPEC]
  python pdf_tool.py extract PATH --pages SPEC [--max-chars N]

Page numbers are PDF page numbers (1 = the first page of the file), which are
usually NOT the numbers printed on the pages. Printed labels are shown when the
PDF has them.

  python pdf_tool.py render  PATH --pages SPEC [--dpi N]
  python pdf_tool.py where

Whatever Python starts it, the tool always runs inside a private virtual
environment next to the plugin (tutor/.venv). The first run creates it and
installs PyMuPDF into it. Nothing is read from or installed into the system
Python. `where` shows which Python is actually in use.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import venv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_DIR = os.path.join(ROOT, ".venv")
REQUIREMENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
BOOTSTRAP_FLAG = "TUTOR_PDF_BOOTSTRAPPED"


def venv_python():
    sub = os.path.join("Scripts", "python.exe") if os.name == "nt" else os.path.join("bin", "python")
    return os.path.join(VENV_DIR, sub)


def in_venv():
    """True when this process is the plugin's private venv Python."""
    return os.path.normcase(os.path.abspath(sys.prefix)) == os.path.normcase(os.path.abspath(VENV_DIR))


def ensure_venv():
    """Always run inside the plugin's private venv, so the system Python is never used or changed.

    From any other Python: create the venv if it is missing, then hand the command over to it.
    Inside the venv: install PyMuPDF if it is missing, then carry on.
    """
    py = venv_python()
    if not os.path.exists(py):
        print("Setting up the PDF reader (first use only)...", file=sys.stderr)
        venv.create(VENV_DIR, with_pip=True)

    if not in_venv():
        sys.exit(subprocess.call([py, os.path.abspath(__file__)] + sys.argv[1:]))

    try:
        import pymupdf  # noqa: F401
        return
    except ImportError:
        pass

    if os.environ.get(BOOTSTRAP_FLAG):
        sys.exit("PyMuPDF is still missing after setup. Try deleting " + VENV_DIR + " and running again.")
    print("Installing PyMuPDF into the PDF reader's environment...", file=sys.stderr)
    subprocess.check_call([py, "-m", "pip", "install", "--quiet", "-r", REQUIREMENTS])
    env = dict(os.environ, **{BOOTSTRAP_FLAG: "1"})
    sys.exit(subprocess.call([py, os.path.abspath(__file__)] + sys.argv[1:], env=env))


def open_pdf(path):
    import pymupdf

    if not os.path.exists(path):
        raise SystemExit(f"File not found: {path}")
    return pymupdf.open(path)


def parse_pages(spec, total):
    """'all', '1-5', '1,3,7' or '3' -> sorted 0-indexed page numbers."""
    if spec.strip().lower() == "all":
        return list(range(total))
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                start, end = part.split("-", 1)
                pages.update(range(max(1, int(start)) - 1, min(total, int(end))))
            else:
                p = int(part) - 1
                if 0 <= p < total:
                    pages.add(p)
        except ValueError:
            raise SystemExit(f"Bad page spec '{part}'. Use 'all', '3', '1-5' or '1,3,7'.")
    return sorted(pages)


def label_of(page):
    """The printed page label if the PDF has one that differs from the page number."""
    try:
        label = page.get_label()
    except Exception:
        return ""
    return label if label and label != str(page.number + 1) else ""


def page_tag(page):
    label = label_of(page)
    return f"{page.number + 1} (printed {label})" if label else f"{page.number + 1}"


def info(path):
    """Metadata, table of contents and a short triage of what each page holds."""
    doc = open_pdf(path)
    meta = doc.metadata or {}
    out = [f"file: {path}", f"pages: {len(doc)}"]
    for key in ("title", "author", "subject"):
        if meta.get(key):
            out.append(f"{key}: {meta[key]}")

    labelled = [p for p in (doc[i] for i in range(min(len(doc), 40))) if label_of(p)]
    if labelled:
        sample = labelled[min(len(labelled) - 1, 10)]
        out.append(f"page labels: PDF page {sample.number + 1} is printed page '{label_of(sample)}' (numbers differ)")

    toc = doc.get_toc()
    if toc:
        out.append(f"\ntable of contents ({len(toc)} entries, PDF page on the right):")
        for level, title, page in toc[:300]:
            out.append(f"{'  ' * (level - 1)}{title} ... {page}")
        if len(toc) > 300:
            out.append(f"... {len(toc) - 300} more entries")
    else:
        out.append("\ntable of contents: none in this file")

    empty, total_chars = [], 0
    for page in doc:
        text = page.get_text()
        total_chars += len(text)
        if len(text.strip()) < 50:
            empty.append(page.number + 1)
    out.append(f"\naverage text per page: {total_chars // max(len(doc), 1)} characters")
    if empty:
        shown = ", ".join(map(str, empty[:20])) + (" ..." if len(empty) > 20 else "")
        out.append(f"pages with almost no text ({len(empty)}; scans, images or blanks): {shown}")
        out.append("  for these, read the page as an image instead of extracting text")
    doc.close()
    return "\n".join(out)


def search(path, query, context=2, literal=False, max_matches=30, pages="all"):
    """Case-insensitive search by line, with a few lines of context around each match."""
    doc = open_pdf(path)
    try:
        pattern = re.compile(re.escape(query) if literal else query, re.IGNORECASE)
    except re.error as e:
        raise SystemExit(f"Invalid regex: {e}. Use --literal to search for the text as typed.")

    out, matches, stopped = [], 0, False
    for i in parse_pages(pages, len(doc)):
        page = doc[i]
        lines = page.get_text().split("\n")
        for n, line in enumerate(lines):
            if not pattern.search(line):
                continue
            if matches >= max_matches:
                stopped = True
                break
            matches += 1
            out.append(f"\n=== Page {page_tag(page)}, line {n + 1} ===")
            for j in range(max(0, n - context), min(len(lines), n + context + 1)):
                out.append(f"{'>>>' if j == n else '   '} {lines[j]}")
        if stopped:
            break
    doc.close()

    if matches == 0:
        return f"No matches found for: {query}"
    tail = f"stopped after {max_matches} matches; narrow the query or use --pages" if stopped else f"{matches} match(es)"
    return "\n".join(out) + f"\n\n--- {tail} ---"


def extract(path, pages, max_chars=20000):
    """Text of the given pages, capped so a careless request cannot flood the context."""
    doc = open_pdf(path)
    out, used, cut_at = [], 0, None
    for i in parse_pages(pages, len(doc)):
        page = doc[i]
        block = f"--- Page {page_tag(page)} ---\n{page.get_text()}"
        if used + len(block) > max_chars:
            cut_at = page.number + 1
            keep = max(0, max_chars - used)
            if keep:
                out.append(block[:keep])
            break
        out.append(block)
        used += len(block)
    doc.close()
    text = "\n".join(out)
    if cut_at:
        text += (f"\n\n[truncated at {max_chars} characters, part-way through page {cut_at}; "
                 f"ask for fewer pages or raise --max-chars]")
    return text


def render(path, pages, dpi=110, max_pages=4):
    """Render pages to PNG files so they can be looked at (scans, figures, garbled maths).

    Claude's Read tool views PNGs natively. Reading a PDF page directly needs poppler
    installed on the machine; this needs nothing beyond PyMuPDF.
    """
    import pymupdf

    doc = open_pdf(path)
    chosen = parse_pages(pages, len(doc))
    if not chosen:
        raise SystemExit("No pages matched that page spec.")
    if len(chosen) > max_pages:
        raise SystemExit(f"Render at most {max_pages} pages at a time (asked for {len(chosen)}). Narrow --pages.")

    stat = os.stat(path)
    key = f"{os.path.abspath(path)}|{stat.st_size}|{int(stat.st_mtime)}|{dpi}"
    out_dir = os.path.join(tempfile.gettempdir(), "tutor-pdf", hashlib.md5(key.encode()).hexdigest()[:12])
    os.makedirs(out_dir, exist_ok=True)

    zoom = dpi / 72.0
    lines = []
    for i in chosen:
        page = doc[i]
        out_path = os.path.join(out_dir, f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(out_path)
        lines.append(f"PDF page {page_tag(page)} -> {out_path}")
    doc.close()
    return "\n".join(lines) + "\n(view each image with the Read tool)"


def main(argv=None):
    parser = argparse.ArgumentParser(description="PDF tools for the tutor plugin")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("where", help="show which Python and PyMuPDF this tool runs with")

    p_info = sub.add_parser("info", help="metadata, table of contents, page triage")
    p_info.add_argument("path")

    p_search = sub.add_parser("search", help="search the text (regex by default)")
    p_search.add_argument("path")
    p_search.add_argument("query")
    p_search.add_argument("--literal", action="store_true", help="treat the query as plain text")
    p_search.add_argument("--context", type=int, default=2, help="lines of context around a match (default 2)")
    p_search.add_argument("--max-matches", type=int, default=30, help="stop after this many matches (default 30)")
    p_search.add_argument("--pages", default="all", help="limit the search: 'all', '1-5', '1,3,7' (default all)")

    p_extract = sub.add_parser("extract", help="text of given pages")
    p_extract.add_argument("path")
    p_extract.add_argument("--pages", required=True, help="'3', '1-5' or '1,3,7' ('all' is allowed but capped)")
    p_extract.add_argument("--max-chars", type=int, default=20000, help="cap on output size (default 20000)")

    p_render = sub.add_parser("render", help="render pages to PNG files to look at (view them with the Read tool)")
    p_render.add_argument("path")
    p_render.add_argument("--pages", required=True, help="'8', '8-9' or '1,5' (at most 4 pages)")
    p_render.add_argument("--dpi", type=int, default=110, help="resolution (default 110; raise for small print)")

    args = parser.parse_args(argv)
    if args.command == "render":
        print(render(args.path, args.pages, args.dpi))
    elif args.command == "where":
        import pymupdf

        print(f"python: {sys.executable}\nprivate venv: {in_venv()}\npymupdf: {pymupdf.__version__}")
    elif args.command == "info":
        print(info(args.path))
    elif args.command == "search":
        print(search(args.path, args.query, args.context, args.literal, args.max_matches, args.pages))
    else:
        print(extract(args.path, args.pages, args.max_chars))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ensure_venv()
    main()
