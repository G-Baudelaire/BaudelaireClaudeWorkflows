# tutor

A Claude Code plugin that teaches you a subject so it understands-not-memorises: it finds the edge of what you already know with graded questions, plans a route from facts you accept outright to what you want to learn, then teaches step by step with a quick check after each step.

This plugin is based on [amosblomqvist/learn](https://github.com/amosblomqvist/learn), adapted to Claude Code's tools.

## What you get

| Piece | What it is | How you use it |
|---|---|---|
| `teach` skill | The teaching method: probe, plan, teach | Ask to be taught anything, or run `/tutor:teach <topic>` |
| `quiz` tool | Graded multiple-choice questions, graded by the plugin | Claude calls it during a lesson |
| `researcher` agent | Web fact-checker and topic scoper, run apart from your conversation | Claude calls it when unsure of a fact, and before planning |
| `pdf-reader` skill and agent | Answers questions about a PDF (usually a book) without loading it into the conversation | Mention a book, or run `/tutor:pdf-reader <question about a PDF path>` |
| `/md-log`, `/md-unlog` | Mirrors the session into a markdown note (made for Obsidian) | `/md-log <path to an existing note>` |

## The workflow

A normal session looks like this.

1. **(Optional) Link a note.** Create an empty markdown note in your vault, then run `/md-log "<path to the note>"`. The session is written into it as you go, so maths and diagrams read rendered.
2. **Ask to learn something.** "Teach me the epsilon-delta definition of a limit."
3. **Probe.** Claude asks short graded questions, each adapted to your last answer, to find where your knowledge runs out: something you get right below it and something you miss above it. A run of right answers just means the questions were too easy, so it keeps going harder. A single miss is explored before it concludes anything. It then asks what you actually want from the topic.
4. **Plan.** Claude scopes the field with the researcher, then shows you a short plan and a small dependency map (facts you can accept outright at the roots, your goal at the end). **It waits for your go-ahead before teaching.**
5. **Teach.** One step at a time: why we need this step, the step itself (built so you could have discovered it), how it connects to what you already hold, then a quick quiz to confirm it landed. A step that doesn't land is fixed before anything is built on it.
6. **(Optional) Bring in a book.** Ask a question about a PDF and the pdf-reader finds the right pages and answers with page references, without putting the book's text in your conversation.

### Answering quiz questions

- Pick an option. You see a tick or cross with the correct answer and an explanation straight away.
- **Don't know?** Type `idk` under **Other** instead of guessing. It is recorded as a gap, not a wrong answer.
- Anything else you type under **Other** is read as a note about what you were thinking.
- Multi-select questions need exactly the right set. Options are shuffled for you.
- When a note is linked, each question is written to it **before** you answer, with the maths rendered, and the verdict after.

### The methods behind it

Two principles, both run through the `teach` skill:

- **Unconditional truths first.** Start from facts you can accept as they stand, with no caveats. They lock in instantly, and everything else is built on them.
- **"How could I have discovered this?"** Every step is motivated, so nothing appears from nowhere.

The skill is the full description; read `skills/teach/SKILL.md` for the details.

## Reading PDFs

`pdf-reader` runs the plugin's own tool, `scripts/pdf_tool.py`:

| Command | Does |
|---|---|
| `info` | Table of contents, page-label offset, pages that are scans |
| `search` | Find a term, with the pages it is on and a few lines of context |
| `extract` | Text of chosen pages (capped) |
| `render` | Saves up to 4 pages as PNG images, so symbol-heavy pages can be seen as they are |
| `where` | Shows which Python it is running with |

- It runs in a **private virtual environment** (`.venv`, inside the plugin folder), created on first use, with PyMuPDF installed into it. It never touches your system Python.
- **Page numbers are PDF page numbers**, not the numbers printed on the page. Printed numbers are shown alongside when the book has them.
- **Extracted text from maths is often garbled** (arrows, Greek letters, diagrams). The agent compares against a rendered page image for anything symbolic and says when the text was unreliable.

## Install and run

Requirements:

- A Claude Code version with function hooks (built and tested on **2.1.296**). This API is early access and may change between releases.
- **Python 3** on your PATH as `python`, `python3` or `py` (only for the PDF tool; it installs its own dependency).
- Web access for the researcher.

### Install it (stays loaded in every session)

The plugin is part of the `baudelaire-workflows` marketplace (see the repository root). In a terminal Claude Code session:

```
/plugin marketplace add G-Baudelaire/BaudelaireClaudeWorkflows
/plugin install tutor@baudelaire-workflows
```

Choose the **user** scope so it loads in every project. From a local clone you can use the folder instead:

```
claude plugin marketplace add <path to the repository root>
claude plugin install tutor@baudelaire-workflows
```

Anyone who can read the repository can install it, so a private repository limits it to the people who have access. **Installing runs the plugin's code on your machine** (its hooks and the Python PDF tool), so install it only from a source you trust.

A plugin installed from a local folder is read from that folder, so edits take effect after `/reload-plugins`. One installed from GitHub runs the copy made at install time: update it with `claude plugin update tutor`, then `/reload-plugins`.

### Try it without installing

From a clone of this repository, for one session only:

```
claude --plugin-dir ./plugins/tutor
```

Reload after editing the plugin with `/reload-plugins`.

### Permissions

The plugin quietly allows exactly two things: its own `quiz` tool (so the answer key is never shown in a permission prompt) and plain `python <plugin>/scripts/pdf_tool.py info|search|extract|render|where` commands (so the pdf-reader can run in the background). Anything else, including those commands with extra shell syntax, asks as usual.

## Known limits

- The question dialog is Claude Code's own, so its wording can't change. That is why "I don't know" goes under **Other**, and the skill tells you so the first time.
- Writing to a note rewrites the whole file (the file API cannot append), so a note over 4 MiB would stop being logged. A status message appears if a write fails.
- Quiz details (the options as you saw them, and your answer) are kept in memory only. A quiz asked before you linked a note is logged in full when you link, unless the plugin was reloaded in between; after a reload it is logged from its result text instead.
- The link to a note lasts for one session. Run `/md-log` again in the next.
- The researcher leans on encyclopedias. For anything a lesson is built on, the skill asks it for a primary or textbook source and treats "couldn't verify" as unverified.
- `/md-log` never creates a note, and it never overwrites what is already in one: backfill and live entries are appended.

## Repository layout

```
plugins/tutor/
  .claude-plugin/plugin.json    manifest
  skills/teach/                 the teaching method
  skills/pdf-reader/            how to query a book
  agents/researcher.md          fact-checking and scoping
  agents/pdf-reader.md          answers questions about a PDF
  hooks/                        quiz tool, md-log, and the PDF permission check (TypeScript)
  scripts/                      the PDF tool (Python) and its tests
  types/                        type contract for the plugin's session state
```

## Development

From the repository root:

```
claude plugin validate ./plugins/tutor
claude plugin test ./plugins/tutor                                  # TypeScript tests
plugins/tutor/.venv/Scripts/python.exe plugins/tutor/scripts/test_pdf_tool.py   # PDF tool tests (macOS/Linux: plugins/tutor/.venv/bin/python)
```

Run any `pdf_tool.py` command once first to create the virtual environment.

## Licence

MIT. See `LICENSE` at the repository root.
