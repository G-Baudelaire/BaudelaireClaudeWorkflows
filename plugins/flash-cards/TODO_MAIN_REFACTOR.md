# TODO: refactor `main()` in `lint_cards.py`

Goal: split `main()` in `skills/create-flash-cards/scripts/anki_utilities/lint_cards.py`
into helper functions and classes. The report and JSON output must not change
unless a decision below says otherwise.

## Context

- `anki_utilities/` layout:
  - `protocols.py`: `Note` (frozen dataclass, `from_dict`, cached `front`/`back`/`words`/`front_raw`/`back_raw`).
  - `checks.py`: `Code` (StrEnum, each member carries its `.rule`), `Flag(code, detail)` with a
    `.rule` property, `Check = Callable[[Note], Flag | None]`, the per-note check functions and
    `field_count(expected)`, which builds a check for each deck.
  - `lint_cards.py`: `DEFAULT_CHECKS`, `lint(note, checks)`, `main()`.
  - `anki_io.py`: `read_deck(path)` for `.txt`/`.tsv`/`.csv` decks.
- Imports are absolute (`from checks import ...`), made possible by `sys.path.insert` of the script's own folder.
  Don't use relative imports: the script runs standalone via `uv run lint_cards.py`.
- `Code` needs Python 3.11+ (`StrEnum`), but the system `python3` is 3.10. Run with `uv run`.
- Formatting is black. Ruff config also enables `SIM`/`FURB`/`RUF` rules.

## The nine sections of `main()`

Line numbers are from when this was written (`main` starts at line 76) and will drift.

| # | Section | Lines | Takes in | Produces |
|---|---|---|---|---|
| 1 | Parse CLI arguments | 77–91 | `sys.argv` | `args` (path, report, json_out, max_examples) |
| 2 | Load the deck (`.json` vs `.txt`/`.tsv`) | 93–96 | `args.path` | `deck` dict |
| 3 | Prepare inputs: build `Note`s, work out the deck's usual field count, build the check list | 98–103 | `deck` | `notes`, `checks` |
| 4 | Run each check on every note, storing the flags in two ways | 105–120 | `notes`, `checks` | `results` (grouped by note), `by_code` (grouped by code) |
| 5 | Duplicate fronts: compares notes against each other | 122–134 | `notes` | more entries in `by_code` |
| 6 | Summary numbers | 136–137 | `notes`, `results` | `total`, `clean` |
| 7 | Build the markdown report: header, table of issues, one section per code | 138–162 | `by_code`, `total`, `clean`, `args.max_examples` | `lines` |
| 8 | Write or print the report | 164–169 | `lines`, `args.report` | file or stdout |
| 9 | Build and write the JSON summary | 171–184 | `total`, `results`, `by_code`, `args.json_out` | file |

### Three layers

- **Input (1–2):** reading the command line and files.
- **Analysis (3–6):** pure computation, with no I/O and no formatting. Its whole output is `notes`, `results` and `by_code`.
- **Output (7–9):** turning that output into markdown and JSON, then writing them.
  `max_examples` is only used here, so it's a presentation setting, not an analysis one.

The main dividing line is between analysis and output. If analysis returned one
object, the markdown and the JSON could each be built from it independently.

## Observations

1. **`results` and `by_code` hold the same flags, grouped two ways** (by note and by code),
   and they're filled in the same loop. One list of `(note, flag)` pairs could produce both,
   so whatever object analysis returns may only need to store that list.
2. **Duplicate fronts don't use `Flag`.** Section 5 adds tuples it builds by hand directly to
   `by_code`, and never adds anything to `results`. As a result:
   - duplicate notes don't count toward `flagged_notes` or the "no mechanical flags" percentage;
   - they're missing from the JSON `notes` list;
   - their "front" column shows the normalised key instead of `note.front`.
3. **The front is cut to two different lengths:** 100 characters in `results` and 80 in `by_code`.
4. **The sort by count is done twice** in section 7, once for the table and once for the per-code sections.
5. **Sections 2, 8 and 9 use bare `open()` calls** without a `with` block (ruff `SIM115`).
6. The duplicate check's normalisation (lowercase, drop trailing `\s?.!:` only) is deliberate.
   Stripping all symbols would make "What does % match?" and "What does _ match?" collide. Keep that comment.

## Decisions to make before slicing

- [ ] **Duplicate fronts (observation 2):** keep the current behaviour, or make duplicates
      produce real `Flag(Code.DUPLICATE_FRONT, ...)`s attached to notes? The second option
      changes the report counts and the JSON, so the baseline diff will show expected differences.
- [ ] **Front truncation (observation 3):** keep 100/80, or settle on one length?
- [ ] **Shape of the split**, e.g. `parse_args()`, `load_deck()`, an analysis function
      returning a result object, `render_markdown(result, max_examples)`,
      `build_summary(result)`, a small `write_or_print` helper.

## Verifying the refactor

Take a baseline **before** changing anything, then diff the output afterwards.

1. Save the test deck below as `lint_deck.json` somewhere outside the repo.
   It triggers 14 of the 16 issue types; `conjunction_front` and `empty_back` aren't exercised.
2. Baseline: `uv run lint_cards.py lint_deck.json --report base.md --json base.json`
3. After the refactor: the same command into `new.md` / `new.json`, then
   `diff base.md new.md && diff base.json new.json`. Both should be identical unless a decision above changed the output.

```json
{"header": {}, "header_lines": [], "tags_column": 3, "notes": [
 {"index": 0, "fields": ["사과", "apple"], "tags": ["korean::food"]},
 {"index": 1, "fields": ["", "something"], "tags": []},
 {"index": 2, "fields": ["What is a join? And what is a key?", "TBD"], "tags": ["sql"]},
 {"index": 3, "fields": ["What is the difference between a clustered and a non clustered index and how does the planner choose and use them in practice ok", "it depends"], "tags": ["leech"]},
 {"index": 4, "fields": ["Name three join types", "inner outer cross"], "tags": ["sql"]},
 {"index": 5, "fields": ["What is normalisation?", "removing redundancy"], "tags": ["sql"]},
 {"index": 6, "fields": ["Explain how an index speeds up lookups", "it keeps a sorted structure so the engine can binary search instead of scanning"], "tags": ["sql"]},
 {"index": 7, "fields": ["This is shown in figure 3", "yes indeed it is"], "tags": ["sql"]},
 {"index": 8, "fields": ["{{c1::물 means water", "", "extra"], "tags": ["korean"]},
 {"index": 9, "fields": ["{{ broken }} {{c", "x"], "tags": ["korean"]},
 {"index": 10, "fields": ["Part 1: what? Extra 2", "answer here"], "tags": ["x"]},
 {"index": 11, "fields": ["사과", "apple"], "tags": ["korean::food"]}
]}
```
