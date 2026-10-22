# Anki file format reference

Everything needed to produce a file Anki imports cleanly, and to parse one the user exports.

## Contents

1. Plain-text import files (TSV/CSV)
2. Header directives
3. Quoting and escaping
4. HTML conventions inside fields
5. Note types and fields
6. Cloze syntax
7. Tags
8. Re-importing and preserving review history
9. Common import failures

---

## 1. Plain-text import files (TSV/CSV)

Anki imports plain text where each line is one **note** and fields are separated by a delimiter (tab by default). Tab-separated is the safer choice: commas appear constantly inside card text, tabs almost never do.

A minimal file:

```
#separator:tab
#html:true
What does CRUD stand for?	Create, Read, Update, Delete	sql::basics
```

Save as UTF-8 (no BOM). `.txt`, `.tsv`, and `.csv` all work.

## 2. Header directives

Lines at the top starting with `#` configure the import. Only these are meaningful:

| Directive | Effect |
|---|---|
| `#separator:tab` | Delimiter. Also `comma`, `semicolon`, `pipe`, or a literal character. |
| `#html:true` | Field content is HTML rather than literal text. Required if cards use `<br>`, `<code>`, `<b>`. |
| `#tags:foo bar` | Space-separated tags applied to **every** note in the file. |
| `#tags column:N` | Column N (1-based) holds that note's tags, space-separated. |
| `#notetype column:N` | Column N names the note type per note. |
| `#deck column:N` | Column N names the destination deck per note. |
| `#columns:Front	Back	Extra` | Column names, delimiter-separated. Useful documentation; Anki uses it for field mapping hints. |
| `#guid column:N` | Column N holds note GUIDs — the reliable way to update existing notes. |

Anything a directive doesn't cover (which note type, which deck) is chosen in the import dialog. When an export has directives, **preserve them exactly** on the way back out, including column positions — the user's file already matches their note type, and shifting a column silently corrupts every note.

## 3. Quoting and escaping

Anki follows the usual CSV quoting rules even in tab mode:

- A field containing the separator, a newline, or a double quote must be wrapped in `"`.
- A literal `"` inside a quoted field is doubled: `""`.
- Multi-line fields are legal *inside quotes* — an exported card whose back has newlines will span several physical lines.

This is why decks must be parsed with a real CSV reader (`csv.reader(f, delimiter='\t')`), not `line.split('\t')`. The `anki-io` command handles both directions; use it rather than hand-rolling.

Alternative to quoting: replace newlines inside fields with `<br>` and keep every note on one physical line. Cleaner to diff, and it's what most hand-maintained decks do.

## 4. HTML conventions inside fields

With `#html:true`, fields render as HTML. Useful and safe:

- `<br>` — line break (never a bare newline for layout)
- `<b>`, `<i>`, `<u>` — emphasis; `<b>Example</b><br>` as a section label is a common idiom
- `<code>` — inline identifiers, keywords, function names
- `<div class="code">…</div>` — code block. This is what this skill's note types style; their CSS sets `white-space: normal`, so line breaks inside it **must** be `<br>` and indentation **must** be `&nbsp;` pairs. `<pre>` is *not* styled by them — use `build_apkg.code_block()` and don't hand-roll it.
- `&nbsp;` — indentation inside code blocks, since HTML collapses runs of spaces (4 × `&nbsp;` per level is typical)
- `<ul>/<li>` — short lists
- `&lt;` `&gt;` `&amp;` — escape these when they're literal content, e.g. showing `SELECT * FROM t WHERE a &gt; 5`

Avoid inline `style=` attributes and `<script>`. Styling belongs in the note type's card template, so it stays consistent across the deck and can be changed once.

**Match the deck's existing idioms.** If their cards use `<div class="code">` with `&nbsp;` indentation, new cards use exactly that. A card that renders differently from its neighbours reads as broken even when the content is right.

## 4a. Note type identity — read before building any .apkg

A `.apkg` carries its note types with it, so the importer has to decide whether an
incoming note type *is* one the user already has. It decides by **id**, not by name.

If the id does not match, Anki creates a second note type called `Name+` and puts
the imported notes on that. The user ends up with `Basic` and `Basic+` side by
side — two copies of the same thing, styled independently, which is exactly what
they were trying to avoid.

Consequences:

- **Never let the id be freshly generated.** A note type created in a scratch
  collection gets a timestamp id, which will never match the user's. Always force
  the canonical ids from `notetypes.json`. `build-apkg` does this.
- **Same id → merges cleanly**, with no dialog options needed.
- **Different id → forks to `Name+`**, whatever the dialog says.
- **Same id but different fields or templates → also forks**, unless the user ticks
  **Merge notetypes**. That checkbox **defaults to off**, so forking is the normal
  outcome, and it happens silently — the import succeeds and the notes land on the
  `+` copy.

That last one is the trap. **Never change the fields or templates of a note type the
user already has.** Not to add a field, not to add a template. If you need a
different card shape — a reverse card, an extra field — define a *new* note type
with a new id. A note type the collection has never seen has nothing to reconcile
against, so it installs cleanly on default settings, and the user's existing note
types are untouched.

CSS-only edits fork too, for the same reason. Change the CSS in `notetypes.json`
only when every deck is being rebuilt anyway, and tell the user to tick Merge notetypes.

If a deck must sit on one of the user's *stock* note types (Basic, Cloze, Basic
and reversed card) rather than this skill's, you need that collection's id for it.
Recover it from any `.apkg` they have exported that uses the type; there is no way
to guess it. `notetypes.json` records the ones already discovered under
`known_collection_notetype_ids`. Add to that list whenever you learn another.

Matching rules differ by format, which decides which one to ship:

| | matches on | preserves review history |
|---|---|---|
| `.apkg` | note **GUID** | only if you have the user's real GUIDs |
| TSV | **first field** | yes, for any card whose front is unchanged |

So: `.apkg` for a new deck or a wholesale replacement, TSV for updating a deck the
user already studies. If they want `.apkg` *and* history preserved, ask them to
export the existing deck in full so you have its GUIDs.

## 5. Note types and fields

Common built-ins:

| Note type | Fields | Cards generated |
|---|---|---|
| Basic | Front, Back | 1 |
| Basic (and reversed card) | Front, Back | 2 (both directions) |
| Basic (type in the answer) | Front, Back | 1, typed |
| Cloze | Text, Back Extra | one per distinct `c` number |

Custom note types are common in mature decks — a third "Extra"/"Notes" field for elaboration is the usual addition, letting the answer stay short while detail sits below it. That pattern satisfies rules 4 and 7 without bloating the back.

The import file's column count must match the note type's field count (plus any tags/deck/notetype columns declared in the header). Extra columns are dropped; missing ones import blank.

## 6. Cloze syntax

```
The Krebs cycle produces {{c1::2 ATP}} per glucose, while oxidative phosphorylation produces {{c2::32-34 ATP}}.
```

- `{{c1::text}}` — one card per distinct number. `c1` and `c2` here give two cards.
- Reusing a number blanks both occurrences on the same card — right for a term that appears twice, wrong when the blanks should be tested separately.
- `{{c1::text::hint}}` — the hint shows in place of the blank.
- Requires the **Cloze** note type; cloze markup on a Basic note renders as literal braces.
- Second field ("Back Extra") appears on every generated card — the place for a shared example or a link to related concepts.

Nesting cloze inside cloze is unsupported. Cloze inside `<code>` is fine.

## 7. Tags

Space-separated, so tags cannot contain spaces — use `-` or `_`. `::` creates hierarchy:

```
sql::joins sql::performance
```

Anki shows these as a tree and lets the user build filtered decks per branch. Two or three levels is the sweet spot; deeper hierarchies get tedious to type and browse.

`leech` and `marked` are Anki-managed — preserve them if present in an export, don't invent them.

## 8. Re-importing and preserving review history

On import Anki matches notes by **the first field** (or by GUID if `#guid column:` is present) and offers to update matched notes rather than duplicate them.

Consequences when improving an existing deck:

- **Back/tags changed, front identical** → note updates in place, review history intact. This is the cheap, safe edit.
- **Front changed** → treated as a new note; the old one stays behind with its history. The user must delete the old one manually.
- **Card split into three** → one keeps the original front (history preserved), two are new.

So: prefer fixing the back; when a front must change, say so explicitly in the report so the user knows what to clean up. If the export included a GUID column, keep it — it makes every edit non-destructive.

In the import dialog the user should check: correct note type, correct deck, and "Update existing notes when first field matches" (called *Update* / *Duplicate handling* depending on version).

## 9. Common import failures

| Symptom | Cause |
|---|---|
| Everything lands in one field | Wrong `#separator`, or file uses spaces not tabs |
| `<br>` shows literally on cards | Missing `#html:true` |
| Rows silently dropped | Unbalanced quotes — a stray `"` swallowed following lines |
| "Notes skipped" | First field empty, or duplicate first field within the file |
| Tags appear as a field | `#tags column:N` missing or pointing at the wrong column |
| Cloze cards show `{{c1::…}}` | Note type isn't Cloze |
| Mojibake (Ã©, â€™) | File not saved as UTF-8 |

Always re-parse a generated file before delivering it (`anki-io validate`). Round-tripping catches quoting bugs that eyeballing does not.
