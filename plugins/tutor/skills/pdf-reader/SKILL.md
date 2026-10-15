---
name: pdf-reader
description: Query a PDF, usually a book the learner is reading, quickly and without flooding the conversation. Use when the learner mentions a book, paper, lecture notes or any PDF and wants something found, explained, checked against it, or taught from it. Locates pages with the table of contents and search, then reads only those pages. Delegates to the pdf-reader agent so the book's text stays out of the main context.
---

# Reading a PDF

A book is too big to read into the conversation, and reading page ranges blind wastes effort. The approach here is **locate cheaply, then read only what you need**: the table of contents and a text search find the pages, and only those pages are read.

## Default: delegate to the agent

Call the Agent tool with `subagent_type: "tutor:pdf-reader"`. Give it:

- the PDF's full file path,
- one precise question (a concept, a definition, a theorem, "what does chapter 3 say about X", "where does the book prove Y"),
- anything that narrows it: the chapter, the notation the book uses, what the learner already knows.

It returns the answer, the pages it came from (PDF page and printed page), at most two short quotes, and caveats. The book's text never enters this conversation. Ask several focused questions rather than one sprawling one.

## Using what comes back

- **The book is a source, not an oracle.** If the answer matters for what you are about to teach, treat the page reference as the evidence and say where it comes from. If the agent reports a caveat (garbled text, a page it could not read, a term it could not find), treat that part as unverified and either ask it to look again or confirm with the researcher (`tutor:researcher`).
- **Match the learner's book.** When a book frames a topic differently from the usual treatment, teach with the book's framing and notation, and say when it differs from the standard one.
- **Give page references.** The learner can open the book at the page. Give the printed page number when there is one, and the PDF page number when it differs.
- **Teaching still follows the teach skill.** What the book says becomes material for the probe, plan and teach loop. Don't just read the book's explanation back to the learner.

## Doing it yourself (small jobs only)

For a quick look you can run the tool directly:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_tool.py" info "<pdf>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_tool.py" search "<pdf>" "<query>" --literal --max-matches 10
python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_tool.py" extract "<pdf>" --pages 12-13
```

If `python` is not found, use `python3` (macOS and Linux) or `py` (Windows). `info` shows the table of contents, the page-label difference, and pages with no text. `search` shows matches with context and page numbers. `extract` returns capped text for given pages. Page numbers are PDF page numbers (page 1 is the first page of the file), not the numbers printed on the pages. The first run installs its dependency into a private environment, which takes a few seconds.

When the text is not enough, because a page is a scan, the text is cut off or garbled, or the answer is in a figure, look at the page:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pdf_tool.py" render "<pdf>" --pages 8
```

That saves the page (up to 4 at a time) as a PNG and prints its path; view it with the Read tool. Use this rather than the Read tool on the PDF itself, which needs poppler installed and fails without it.

Anything bigger than a quick look goes to the agent.
