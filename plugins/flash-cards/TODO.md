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
| Dependencies | `uv run` with inline PEP 723 deps. Voice model downloaded on first use into a cache dir. Requires `uv` + `ffmpeg`. |
| Layering     | Note generation imports TTS. TTS never imports note/Anki code.                                                     |
| Skills       | One plugin, two skills: generic `create-flash-cards` + new `korean-vocab`, sharing scripts.                        |
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
| `assets/notetypes.json`     | `basic` (1607392319), `cloze` (…320), `basic_reversed` (…321), stock `Basic`. | `basic_reversed` never installed. No audio type.                                       |
| `scripts/anki_io.py`        | TSV/CSV ↔ JSON, preserves header lines + tags column.                         | `#guid`/`#notetype`/`#deck` columns treated as plain fields. Can't read `.apkg`.       |
| `scripts/build_apkg.py`     | JSON → `.apkg` with forced note-type ids, `--verify`.                         | Basic/cloze only. Fresh GUIDs every build. `with_media=False`.                         |
| `scripts/lint_cards.py`     | Shape checks.                                                                 | Fine as is.                                                                            |
| `main.py`                   | Piper TTS proof of concept.                                                   | Not wired in.                                                                          |

## 2. Plugin structure

```
.claude-plugin/plugin.json
skills/create-flash-cards/      SKILL.md, references/   (generic, existing)
skills/korean-vocab/            SKILL.md                (new)
scripts/                        shared, run as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/…`
  tts.py                        normalise → Piper → ffmpeg → mp3. No imports from the other scripts.
  anki_io.py  build_apkg.py  lint_cards.py   (build_apkg imports tts)
assets/notetypes.json
```

- [ ] Restructure the repo. Remove `venv/`, `install.sh`, `voices/` and
      `requirements.txt` in favour of the PEP 723 headers.
- [ ] Update `SKILL.md` paths to `${CLAUDE_PLUGIN_ROOT}` and send output to the
      user's cwd.
- [x] `tts.py`: voice + short-path espeak-ng data cached in
      `~/.cache/korean-flashcards/` on first use; clear error if `ffmpeg` is
      missing (done in `research/tts.py`, port as-is).
- [ ] Add the plugin to the marketplace repo and test a fresh install.

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
- [ ] `tts.py`: `speech_text(korean)` normalisation:
  - include optional `(요)`
  - take the first option of `A/B`
  - drop `___` and `[...]`
  - spell out digits (Sino-Korean for amounts and 번)
  - then `synthesize() -> ko_<sha1(speech_text)[:12]>.mp3`, reusing the cached
    file if it exists
- [ ] Update packages contain only new and changed notes, never the whole deck,
      to keep them small and only touch notes that were actually edited.
- [ ] Merge: dedupe incoming pairs against the deck (Korean or English match),
      then report new / duplicate / flagged pairs.
- [ ] `korean-vocab/SKILL.md`: inputs (pairs + `.apkg` export), pair-flagging
      rules, homonym sense in English (눈 → "eye (body)" vs "snow"), tag/subdeck
      behaviour, and import steps for you and your collaborators.

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
is no venv to manage:

```bash
cd research
uv run build_migration.py ../KoreanTest.apkg ../KoreanMigration.apkg
uv run dry_run.py <COPY of collection.anki2> ../KoreanMigration.apkg
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
- The `research/` prototypes become `scripts/tts.py` and `scripts/build_apkg.py` in §2/§3.
- `KoreanTest.apkg` and `KoreanMigration.apkg` are local build artefacts (gitignored).
- `venv/`, `voices/`, `install.sh`, `requirements.txt` and `main.py` are now unused.
  Delete them in the §2 restructure.

## Open questions

- ~~espeak-ng long-path failure~~: solved. `tts.py` copies the data to
  `~/.cache/korean-flashcards/espeak-ng-data-<ver>` and passes that path. Verified
  under `uv run`.

- Should the first collaborator import be automated as a version check? E.g. the
  instructions show the expected import log, and a mismatch means stop.
- Is the AnkiMobile import path needed? Not for now, since everyone imports on
  desktop.
