# TODO — Korean audio flashcards

<!--toc:start-->

- [TODO — Korean audio flashcards](#todo--korean-audio-flashcards)
  - [Decisions](#decisions)
  - [Existing deck (`KoreanTest.apkg`)](#existing-deck-koreantestapkg)
  - [1. What the skill does today (`create-flash-cards/`)](#1-what-the-skill-does-today-create-flash-cards)
  - [2. Plugin structure](#2-plugin-structure)
  - [3. Extend: word pairs + current deck → updated deck with audio](#3-extend-word-pairs--current-deck--updated-deck-with-audio)
  - [4. One-off migration of the existing deck](#4-one-off-migration-of-the-existing-deck)
  - [Open questions](#open-questions)

<!--toc:end-->

## Decisions

| Topic        | Decision                                                                                                           |
| ------------ | ------------------------------------------------------------------------------------------------------------------ |
| Distribution | Claude Code plugin in the personal marketplace. Claude Code only.                                                  |
| Dependencies | The plugin is a uv project, run with `uv run --project`; in development it's a member of the repo's uv workspace. Voice model downloaded on first use into a cache dir. Requires `uv` + `ffmpeg`. |
| Layering     | Note generation imports TTS. TTS never imports note/Anki code.                                                     |
| Skills       | One plugin, one skill: `create-flash-cards`. TTS is one of its scripts, used when a note type has audio fields.    |
| Anki I/O     | Files only: `.apkg` (or GUID TSV) in, `.apkg` out. No AnkiConnect.                                                 |
| Sharing      | You're the only editor. Collaborators import your `.apkg` on desktop Anki ≥ 23.10, then sync to mobile.            |
| Input        | KO + EN pairs. Claude flags suspect pairs (typos, wrong meaning) but doesn't change them.                          |
| Politeness   | Match the deck (mostly 해요체, mixed by context). No register check.                                               |
| Fields       | `English`, `Korean`, `Audio`, `AudioSlow`, `Extra`. Extra is optional and empty by default.                        |
| Cards        | EN→KO (audio on back) and KO→EN (Korean text + audio on front).                                                    |
| Audio        | MP3 via ffmpeg, hash-named. Normal speed auto-plays (`[sound:]`); 0.6× (Piper `length_scale`, chosen by ear over 0.75×/0.5×) is a hidden `<audio>` played by a "0.6×" button. Text is normalised for speech; card text is unchanged. |
| Tags / deck  | Existing deck: extend its own subdecks and `korean::…` tags. New deck: Claude proposes topic tags.                 |
| History      | Must survive for everyone. Packages never carry scheduling.                                                        |
| Particles    | The 16 one-way `Basic` notes (Particles & Suffixes) stay as they are: no migration, no audio.                      |

## Existing deck (`KoreanTest.apkg`)

- 242 notes on `Basic (and reversed card)` (id 1747648970786) in
  `Korean::Numbers / Sentences / Vocabulary`. Fields are `Front`=Korean and
  `Back`=English. Card 1 = KO→EN, Card 2 = EN→KO.
- 16 notes on `Basic` (id 1747648970785) in `Korean::Particles & Suffixes`. One
  is untagged (은/는 vs 이/가).
- About 100 notes need speech normalisation, e.g. `잘 지냈어(요)?`, `(네/예)`,
  `이 / 가`, `저는 ___이에요/예요`, `4100원`, `A-58번`.
- The export has no scheduling. History lives in each person's own collection.

## 1. What the skill does today (`create-flash-cards/`)

| Piece                       | Behaviour                                                                     | Gaps                                                                                   |
| --------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `SKILL.md`                  | Generic generate/improve workflow → lint → tag → `.apkg` → report.            | Nothing Korean-specific. Hardcoded claude.ai paths (`/home/claude`, `/mnt/user-data`). |
| `references/card-rules.md`  | 8 card-design rules + rewrite patterns.                                       | No vocab guidance (homonyms, bare fields on reversible cards).                         |
| `references/anki-format.md` | TSV format, note-type id rules, GUID vs first-field matching.                 | Scripts don't implement the GUID path. Nothing on merging note types.                  |
| `notetypes.json`            | `basic` (1607392319), `cloze` (…320), `basic_reversed` (…321), stock `Basic`. | `basic_reversed` never installed. No audio type.                                       |
| `anki_io.py`                | TSV/CSV ↔ JSON, preserves header lines + tags column.                         | `#guid`/`#notetype`/`#deck` columns treated as plain fields. Can't read `.apkg`.       |
| `build_apkg.py`             | JSON → `.apkg` with forced note-type ids, `--verify`.                         | Basic/cloze only. Fresh GUIDs every build. `with_media=False`.                         |
| `lint_cards.py`             | Shape checks.                                                                 | Fine as is.                                                                            |
| `main.py`                   | Piper TTS proof of concept.                                                   | Not wired in.                                                                          |

## 2. Plugin structure

```
plugins/flash-cards/            (in the BaudelaireClaudeWorkflows marketplace repo)
  .claude-plugin/plugin.json
  pyproject.toml                deps + entry points; a member of the repo's uv workspace
  src/flash_cards/              run as `uv run --project "${CLAUDE_PLUGIN_ROOT}" <command>`
    anki_utilities/   anki_io.py (anki-io)  build_apkg.py (build-apkg)  lint_cards.py (lint-cards)
                      notetypes.json   (build_apkg imports text_to_speech)
    text_to_speech/   normalise → Piper → ffmpeg → mp3. No imports from anki_utilities.
      constants.py           CACHE_DIR, VOICE, LetterReadings, Digits, Small/BigUnits
      text_normalisation.py  TextNormalisation: card text → speech text, Sino-Korean numbers
      cache_paths.py         CachePaths: audio file names + cache check, voice model, espeak data
      synthesizer.py         Synthesizer: Piper WAV → ffmpeg MP3, via CachePaths
  skills/create-flash-cards/
    SKILL.md
    references/  card-rules.md  anki-format.md  korean-vocab.md (new)
  tests/        lint golden test, build + verify test (`uv run pytest` from the repo root)
  research/     PEP 723 migration prototypes
  docs/         this file, TODO_MAIN_REFACTOR.md
```

The plugin wrapper is only there for marketplace distribution. `SKILL.md` lists
TTS as an option: when a note type has `Audio`/`AudioSlow` fields,
`build_apkg.py` fills them. The Korean specifics (pair flagging, homonyms,
collaborator import steps) live in `references/korean-vocab.md`, which is read
only for Korean decks.

- [x] Restructure the repo into the layout above, with PEP 723 headers on the
      scripts (`requires-python = ">=3.11"`). `install.sh`, `requirements.txt`
      and `main.py` removed.
- [x] Move into BaudelaireClaudeWorkflows as `plugins/flash-cards` (history
      kept) and turn the scripts into the `flash_cards` package, a uv workspace
      member. This replaced the PEP 723 headers and the `sys.path` hack.
- [ ] Delete the old `~/Documents/Projects/KoreanFlashCardProducer` folder,
      untracked `venv/` and `voices/` included (the voice is already cached in
      `~/.cache/korean-flashcards/voices/`), once a fresh install works.
- [x] Point `SKILL.md` at the plugin's commands
      (`uv run --project "${CLAUDE_PLUGIN_ROOT}" …`) and send output to the
      user's cwd.
- [x] Port `research/tts.py` into the `text_to_speech/` package: voice +
      short-path espeak-ng data cached in `~/.cache/korean-flashcards/` on first
      use; clear error if `ffmpeg` is missing. Audio file names match the
      prototype, so the existing cache is reused. `research/tts.py` stays as the
      copy `build_migration.py` imports until §3 absorbs `research/`.
- [x] Add the plugin to the marketplace repo.
- [ ] Test a fresh install from the marketplace.
- [x] **Bug:** `anki_io.py`'s own CLI is broken since `read_deck` started
      returning a `Deck` dataclass (with `Note`s) instead of a dict. `to-json`
      crashes on `json.dumps(deck)` (a dataclass isn't serialisable; try
      `dataclasses.asdict`), and `stats` crashes on `deck["header_lines"]`.
      `deck_stats` and `write_deck` still index `deck["notes"]` / `n["fields"]`.
      `from-json` still works, since it hands plain JSON to `write_deck`.
      `lint_cards.py` is fine: its `load_deck` builds a `Deck` for both formats.

## 3. Extend: word pairs + current deck → updated deck with audio

**New note type** `Korean vocab (skill)`. Fix its note-type id, and **reuse the
old type's field and template ids** so merges map history correctly (see §4):

| New                                                       | Takes the id of    |
| --------------------------------------------------------- | ------------------ |
| field `English`                                           | old `Back`         |
| field `Korean`                                            | old `Front`        |
| template 1 _EN→KO_: `{{English}}` / `{{Korean}}{{Audio}}` | old Card 2 (EN→KO) |
| template 2 _KO→EN_: `{{Korean}}{{Audio}}` / `{{English}}` | old Card 1 (KO→EN) |

`Audio`, `AudioSlow` and `Extra` get new ids. `AudioSlow` holds
`<audio src="ko_<hash>_s060.mp3">`: Anki doesn't auto-play it, but export and
Check Media still count it (verified; a file referenced only from JS is not). `Extra` renders on the back of both cards only
when it's filled. CSS is the old type's stock style (centred, Arial 20px), not
the skill's left-aligned CSS. Confirmed in the app dry run.

Tasks:

- [ ] Read the old type's field/template ids from your collection export and
      store the full new type, ids included, in `notetypes.json`.
- [ ] `build_apkg.py`: install all types and pick one per note. Set `n.guid`
      when present. Generate missing audio, add it to media and export
      `with_media=True, with_scheduling=False`. `--verify` checks the media.
- [ ] `anki_io.py`: read an `.apkg` directly (notes, GUIDs, tags, deck per
      card), and lift `#guid column` from TSV.
- [x] `TextNormalisation.speech_text(card_text)` normalisation (same output as
      the prototype on all 258 deck fields):
  - include optional `(요)`
  - take the first option of `A/B`
  - drop `___` and `[...]`
  - spell out digits (Sino-Korean for amounts and 번)
  - read Latin letters the Korean way (`A-58번` → 에이 오십팔번)
  - then `Synthesizer.synthesize() -> ko_<sha1(speech_text)[:12]>.mp3`, reusing
    the cached file if it exists
- [ ] Update packages contain only new and changed notes, never the whole deck,
      to keep them small and only touch notes that were actually edited.
- [ ] Merge: dedupe incoming pairs against the deck (Korean or English match),
      then report new / duplicate / flagged pairs.
- [ ] `references/korean-vocab.md`: inputs (pairs + `.apkg` export), pair-flagging
      rules, homonym sense in English (눈 → "eye (body)" vs "snow"), tag/subdeck
      behaviour, and import steps for you and your collaborators. Add a pointer
      to it and the TTS option to `SKILL.md`, plus Korean triggers in its
      `description`.

**Workflow:** export the deck as `.apkg` (no scheduling) + pairs → Claude →
`.apkg` → everyone imports (update notes on, Merge note types on).

## 4. One-off migration of the existing deck

**Verified** with `anki` 26.09.3 (`research/merge_notetype_test.py`). Importing
a package with the same GUIDs on the new note type, with **Merge note types**
ticked:

- moves all 242 notes onto `Korean vocab (skill)`, with fields swapped correctly
- keeps the same card ids and history on the right direction (EN→KO stays
  EN→KO), with no extra cards
- leaves unrelated notes on the old note type untouched, and the old type still
  exists
- without the Merge tick, all 242 are "conflicting" and skipped. Nothing breaks,
  nothing changes.
- this only works when the template/field ids match the old ones. With fresh
  ids, history ended up on orphaned extra templates (4 cards per note).

So the migration is just the first build of the deck on the new note type.
There's no script per collection.

- [x] Build the migration `.apkg` (`research/build_migration.py`, prototype in
      `research/tts.py`): 242 notes, 484 cards, 484 MP3s (normal + 0.6×, 5.1 MB). Particles
      left out.
- [x] Programmatic dry run (`research/dry_run.py`, `anki` 26.8.1 = your desktop
      version) on a read-only snapshot of your real collection (488 reviewed
      cards, 27,676 revlog). **PASS:**
  - 242 updated, 0 conflicting
  - note, card and revlog counts unchanged
  - 0 scheduling changes, 0 wrong directions
  - other notes untouched, all audio present
- [x] **Leech tags:** accepted as lost. Imports strip `leech`/`marked`, and
      lapses/scheduling are unaffected. No restore step.
- [x] 0.6× button: assumed fine (only the speed constant changed since the
      in-app check).
- [ ] Check on iOS after the real migration, since a test profile can't sync.
- [ ] Write the collaborator instructions:
  - back up and update to Anki ≥ 23.10
  - File → Import, with **Merge note types** ✓ and update notes ✓
  - check that the import log shows 242 updated and 0 conflicting
  - sync, choosing **Upload to AnkiWeb** if asked (schema change)
- [ ] Afterwards: the old `Basic (and reversed card)` type stays, unused by the
      Korean notes. Leave it alone.

## Handoff: reproducing the prototype

Needs only `uv` and `ffmpeg`. Each script declares its dependencies (PEP 723), so there
is no venv to manage. They run in their own environments, apart from the workspace:

```bash
cd plugins/flash-cards/research
uv run build_migration.py ~/Documents/Anki/korean/KoreanTest.apkg ~/Documents/Anki/korean/KoreanMigration.apkg
uv run dry_run.py <COPY of collection.anki2> ~/Documents/Anki/korean/KoreanMigration.apkg
```

- The first run downloads the voice and copies espeak-ng data into
  `~/.cache/korean-flashcards/` (`voices/`, `espeak-ng-data-<piper version>/`,
  `audio/`). That takes ~1 min for 484 clips; cached re-runs take ~1s.
- Audio isn't byte-reproducible (Piper `noise_scale` 0.667 is random). The cache
  makes a card's audio stable once it's generated, so don't clear `audio/` between
  builds unless you want new takes.
- Pin `anki` to your desktop version (26.8.1).
- Snapshot the real collection read-only even while Anki is open:
  `sqlite3 "file:$HOME/Library/Application Support/Anki2/User 1/collection.anki2?mode=ro" ".backup '<dest>'"`.
  Never run `dry_run.py` on the live file.
- `research/merge_notetype_test.py` is the original proof that the merge preserves history.
- `research/tts.py` is now `src/flash_cards/text_to_speech/`.
  `research/build_migration.py` becomes `build_apkg.py` in §3.
- `KoreanTest.apkg` and `KoreanMigration.apkg` are local build artefacts, kept in
  `~/Documents/Anki/korean/` (`*.apkg` is gitignored).

## Open questions

- ~~espeak-ng long-path failure~~: solved. `CachePaths.espeak_data()` copies the data to
  `~/.cache/korean-flashcards/espeak-ng-data-<ver>` and passes that path. Verified
  under `uv run`.

- Should the first collaborator import be automated as a version check? E.g. the
  instructions show the expected import log, and a mismatch means stop.
- Is the AnkiMobile import path needed? Not for now, since everyone imports on
  desktop.
