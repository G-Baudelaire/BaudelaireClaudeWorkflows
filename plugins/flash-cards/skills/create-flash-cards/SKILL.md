---
name: create-flash-cards
description: Turn source material (notes, docs, transcripts, code, textbook excerpts, an existing deck) into Anki flashcards, or audit and rewrite cards that already exist. Use this whenever the user mentions flashcards, Anki, spaced repetition, cloze deletions, .apkg/.txt/.tsv/.csv deck exports, "cards for X", "help me memorise X", "review my deck", or asks to improve, split, tag, or clean up cards they wrote by hand — even if they don't say the word "Anki". Also use when the user drops a set of notes and asks how to study or revise them.
---

# Create Flash Cards

Two jobs, one pipeline: **generate** cards from source material, and **improve** cards that already exist. Both end with a file the user can import into Anki without touching it, plus a short report of what changed and why.

The quality bar is the 8 rules in `references/card-rules.md`. Read that file before writing or editing any card — it is the substance of this skill, not background reading. `references/anki-format.md` covers the file format; read it before producing or parsing a deck file.

**Default output is `.apkg`, not TSV.** `notetypes.json` holds this skill's two canonical note types — `Basic (skill: front/back/extra)` and `Cloze (skill)` — with their templates and CSS. Build with `build-apkg`, which reuses them. Do not invent a note type, and do not restyle these: every deck built by this skill is meant to render identically, and the user already has decks on them. TSV remains available when the user asks for it, or when they are updating a deck in place and need first-field matching to preserve review history.

The scripts are this plugin's `flash_cards` Python package, run as commands with
`uv run --project "${CLAUDE_PLUGIN_ROOT}" <command>`. That runs them from the user's
current directory, so `deck.json`, `lint.md` and the finished deck all land there. The
first run sets up the plugin's environment, which can take a minute.

## Workflow

### 1. Read the input before deciding anything

If the user attached a deck export, parse it with the bundled script rather than eyeballing it — deck exports contain tabs, embedded newlines, and HTML that break naive parsing:

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" anki-io to-json <input.txt> -o deck.json
```

This gives a JSON array of notes plus the header directives, which is a safe format to edit. Convert back at the end with `from-json`.

Then work out three things:

- **Mode**: generating new cards, improving existing ones, or both (existing deck + new source material to extend it).
- **House style**: if a deck already exists, it defines the conventions — note type, field count, HTML idioms (`<code>`, `<div class="code">`, `<b>Example</b><br>`), whether tags are used. Match them. Inventing a new style for cards that will sit in the same deck is a worse outcome than a slightly imperfect card.
- **Scope**: how many cards the material actually justifies. Dense technical material is roughly one card per fact worth recalling. Don't pad, and don't compress three facts into one card to hit a number.

### 2. For generation: extract facts first, write cards second

List the atomic facts in the source before writing any card. This is what keeps cards atomic — if you write cards straight from prose you inherit the prose's sentence structure, and prose sentences routinely carry three facts each.

For each fact decide the format:

- **Q&A** for discrete facts, mechanisms, "why" questions, and anything where the question stands on its own.
- **Cloze** for dense material where surrounding context helps retrieval — parameter lists, sequences, numeric values, syntax skeletons. See `references/anki-format.md` for cloze syntax and the multi-blank pattern.
- **Recall-by-doing** for procedural/technical material: front states a task ("Add column `x` to table `Y`"), back gives the exact code. These beat definition cards for languages, APIs, and tools, because they test what the user will actually need to produce.

Then write both sides of every card in full (rule 5). If a back can't be written clearly, the concept isn't understood well enough yet — say so to the user and ask, rather than shipping a vague back.

### 3. For improvement: audit, then rewrite

Run the linter for the mechanical checks:

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" lint-cards deck.json --report lint.md
```

It flags compound fronts, over-long fronts, empty or thin backs, context-dependent references, missing examples, untagged notes, duplicates, and malformed cloze. It is deliberately noisy: it catches shape, not meaning. Read every flag and judge it — a flagged card that is fine stays as it is, and the report should say so.

The linter cannot see the failures that matter most, so read the cards yourself for:

- Backs that answer a different question than the front asks.
- Cards that are technically correct but untestable ("What is a database?").
- Wrong or outdated facts. Verify anything you're unsure about instead of preserving an error faithfully.
- Missing coverage — obvious neighbours of existing cards that were never made.

Then rewrite. Preferred fixes, in order: split a compound card into atomic ones; shorten the front and move the qualifiers to the back; add a concrete example to the back; add tags. Deleting a card is a last resort and always gets flagged to the user rather than done silently.

Preserve scheduling where you can: Anki matches notes on the first field, so a card whose front is unchanged keeps its review history on re-import. Prefer editing the back over rewriting the front when both would work, and say in the report which fronts changed (those import as new cards and lose their history).

### 4. Tag everything (this is rule 8, and it's the one most often skipped)

Every card gets at least one topical tag, using a hierarchy that mirrors how the subject is actually structured:

```
sql::joins        sql::aggregation        sql::ddl
```

Hierarchical tags let Anki filter subdecks and make related cards findable, which is the whole point of the anti-orphan rule. Where a card genuinely depends on another concept, also reference it in the card text ("...compare `WHERE` vs `HAVING`") rather than relying on tags alone.

Keep the tag vocabulary small — 6-12 tags for a hundred-card deck. A tag applied to one card is a label, not a category.

### 5. Deliver

Default path — build a `.apkg` on the canonical note types:

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" build-apkg deck.json \
    -o "<name>.apkg" \
    --deck "Technical Aspects::SQL" --verify
```

`--verify` re-imports the package into a scratch collection and reports notes, cards, decks, note types used, untagged count and whether cloze cards render. Run it every time — a deck that fails to import is worse than no deck.

The deck JSON is one object per note: `{"fields": [front, back, extra], "tags": [...]}`. Cloze notes are detected from `{{c1::` in field 0 and take `[text, back_extra]`. Field split:

- **Front** — the question, nothing else
- **Back** — the answer alone, kept short
- **Extra** — elaboration, contrasts, examples (rules 4 and 7); renders below a rule

Use `code_block(snippet)` from `flash_cards.anki_utilities.build_apkg` for code (run Python with `uv run --project "${CLAUDE_PLUGIN_ROOT}" python`). These note types style `<div class="code">`, **not** `<pre>` — the helper converts newlines to `<br>` and indentation to `&nbsp;`, which is what the CSS requires.

TSV path, when the user asks for it or is updating a deck in place:

```bash
uv run --project "${CLAUDE_PLUGIN_ROOT}" anki-io from-json deck.json -o <name>.txt
uv run --project "${CLAUDE_PLUGIN_ROOT}" anki-io validate <name>.txt
```

Then give the user a short report in chat:

- counts (cards in, cards out, split, rewritten, tagged, deleted)
- the specific problems found, grouped by rule, with one or two real examples from their own cards
- anything needing their decision: facts you couldn't verify, cards you'd delete, gaps in coverage
- how to import — for `.apkg`, `File → Import` and that is all; for TSV, check the note type and deck and tick "Update existing notes when first field matches" if they are re-importing a deck they already study

Keep the report proportional. For a 20-card job a paragraph is right; for a 200-card audit, group by problem type instead of listing every card.

## Judgement calls worth getting right

**Don't over-atomise.** Rule 1 splits distinct facts, but "front: term, back: definition + one-line why it matters + example" is a single fact with context, not three cards. Rules 4 and 7 explicitly want that material on the back. The test is whether the back contains one thing to *recall* — supporting context that makes it stick doesn't count against it.

**Don't turn everything into cloze.** Cloze suits material where context carries meaning. A cloze over a sentence with one obvious blank is just a Q&A card with extra steps.

**Match difficulty to purpose.** Cards for an exam next week and cards for a language being learnt over years want different phrasing. Ask if it's unclear.

**Say what you didn't do.** If the source contained material you deliberately skipped (too vague to test, already covered, needs a diagram), name it. Silent omissions read as sloppiness.

## Bundled files

- `${CLAUDE_PLUGIN_ROOT}/src/flash_cards/anki_utilities/notetypes.json` — the canonical note types: names, **ids**, fields, templates, CSS, and the HTML conventions that CSS expects. Reuse verbatim; never regenerate the ids.
- `references/card-rules.md` — the 8 rules with worked good/bad pairs and the rewrite patterns for each violation. Read before writing cards.
- `references/anki-format.md` — import file format, header directives, quoting, HTML conventions, cloze syntax, note type identity and re-import behaviour. Read before producing or parsing a file.

Commands, run with `uv run --project "${CLAUDE_PLUGIN_ROOT}" <command>` (source in `${CLAUDE_PLUGIN_ROOT}/src/flash_cards/anki_utilities/`):

- `build-apkg` (`build_apkg.py`) — build a `.apkg` on the canonical note types; `--verify` re-imports and checks it. The module also exports `code_block()` for `<div class="code">` snippets.
- `anki-io` (`anki_io.py`) — parse and write Anki TSV/CSV exports safely; `to-json`, `from-json`, `validate`, `stats`.
- `lint-cards` (`lint_cards.py`) — mechanical rule checks over a deck JSON; writes a markdown report.
