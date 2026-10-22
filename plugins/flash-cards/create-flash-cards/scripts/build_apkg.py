#!/usr/bin/env python3
"""Build an Anki .apkg from deck JSON, using this skill's canonical note types.

Why this exists: a plain TSV import makes the user pick a note type by hand, and
cloze cards silently break if they land on a Basic type. An .apkg carries the note
type, its templates and its CSS with it, so the deck renders correctly on import.

The note types live in ../assets/notetypes.json and MUST be reused verbatim. Their
ids are load-bearing (see "Note type identity" in references/anki-format.md).

Usage:
    python3 build_apkg.py deck.json -o out.apkg
    python3 build_apkg.py deck.json -o out.apkg --deck "Technical Aspects::SQL"
    python3 build_apkg.py deck.json -o out.apkg --verify

Input JSON — either the shape anki_io.py emits, or:
    {"deck": "Technical Aspects::SQL",
     "notes": [{"fields": ["front", "back", "extra"], "tags": ["sql::joins"]},
               {"fields": ["Text with {{c1::blank}}", "back extra"],
                "tags": ["sql::ddl"], "cloze": true}]}

A note is treated as cloze when it sets "cloze": true, or when field 0 contains
"{{c<n>::". Basic notes take 2 or 3 fields (Extra may be omitted).

Requires the `anki` package: pip install anki --break-system-packages
"""

import argparse
import json
import os
import re
import sys
import tempfile

CLOZE_RE = re.compile(r"\{\{c\d+::")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets",
                      "notetypes.json")


# ---------------------------------------------------------------- HTML helpers

def code_block(text, indent_unit=2):
    """Render a code snippet as the <div class="code"> block these note types style.

    The .code CSS uses white-space:normal, so real newlines collapse — line breaks
    must be <br> and leading indentation must be &nbsp;. Do NOT use <pre>: it is
    not styled by these note types.
    """
    out = []
    for line in text.strip("\n").split("\n"):
        stripped = line.lstrip(" ")
        spaces = len(line) - len(stripped)
        pad = "&nbsp; " * (spaces // indent_unit)
        out.append(pad + escape(stripped))
    return '<div class="code">' + "<br>".join(out) + "</div>"


def escape(s):
    """Escape only what breaks HTML, leaving existing entities alone."""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("&amp;nbsp;", "&nbsp;").replace("&amp;lt;", "&lt;")
             .replace("&amp;gt;", "&gt;").replace("&amp;amp;", "&amp;"))


def inline(s):
    return "<code>" + escape(s) + "</code>"


# ---------------------------------------------------------------- note types

def load_notetypes():
    with open(ASSETS, encoding="utf-8") as fh:
        return json.load(fh)["notetypes"]


def install(col, spec):
    """Create the note type with its canonical id, or return it if already present."""
    from anki.models import NotetypeDict

    existing = col.models.get(spec["id"])
    if existing:
        return existing

    mm = col.models
    nt: NotetypeDict = mm.new(spec["name"])
    nt["id"] = 0  # add_dict requires 0; the canonical id is forced on afterwards
    nt["type"] = 1 if spec["kind"] == "cloze" else 0
    nt["css"] = spec["css"]
    nt["sortf"] = spec.get("sortf", 0)
    nt["flds"] = []
    for name in spec["fields"]:
        nt["flds"].append(mm.new_field(name))
    nt["tmpls"] = []
    for t in spec["templates"]:
        tmpl = mm.new_template(t["name"])
        tmpl["qfmt"] = t["qfmt"]
        tmpl["afmt"] = t["afmt"]
        nt["tmpls"].append(tmpl)
    mm.add_dict(nt)
    # add_dict may reassign the id; force the canonical one so imports merge
    made = col.models.by_name(spec["name"])
    if made["id"] != spec["id"]:
        _force_id(col, made["id"], spec["id"])
        made = col.models.get(spec["id"])
    return made


def _force_id(col, old_id, new_id):
    """Rewrite a note type's id in place.

    Anki assigns a timestamp id on creation, but the id is what the .apkg importer
    matches on — a fresh one guarantees a 'Name+' fork in the user's collection.
    Done through the db because there is no API for it.
    """
    db = col.db
    for table, column in (("notetypes", "id"), ("fields", "ntid"), ("templates", "ntid")):
        db.execute(f"update {table} set {column} = ? where {column} = ?", new_id, old_id)
    db.execute("update notes set mid = ? where mid = ?", new_id, old_id)
    col.models._clear_cache()


# ---------------------------------------------------------------- build

def build(deck_json, out_path, deck_name=None):
    from anki.collection import Collection, ExportAnkiPackageOptions, DeckIdLimit
    from anki.decks import DeckId

    data = deck_json if isinstance(deck_json, dict) else {"notes": deck_json}
    notes = data["notes"]
    deck_name = deck_name or data.get("deck") or "Imported"

    specs = load_notetypes()
    tmp = tempfile.mkdtemp()
    col = Collection(os.path.join(tmp, "build.anki2"))
    basic = install(col, specs["basic"])
    cloze = install(col, specs["cloze"])
    did = col.decks.id(deck_name)

    counts = {"basic": 0, "cloze": 0}
    for note in notes:
        fields = list(note.get("fields", []))
        is_cloze = note.get("cloze") or bool(CLOZE_RE.search(fields[0] if fields else ""))
        model = cloze if is_cloze else basic
        n = col.new_note(model)
        for i, value in enumerate(fields[: len(model["flds"])]):
            n.fields[i] = value
        n.tags = list(note.get("tags", []))
        col.add_note(n, DeckId(did))
        counts["cloze" if is_cloze else "basic"] += 1

    if os.path.exists(out_path):
        os.remove(out_path)
    col.export_anki_package(
        out_path=out_path,
        options=ExportAnkiPackageOptions(with_scheduling=False, with_media=False,
                                         legacy=False, with_deck_configs=False),
        limit=DeckIdLimit(deck_id=did))
    cards = col.decks.card_count([did], include_subdecks=False)
    col.close()
    return {"notes": len(notes), "cards": cards, "deck": deck_name, **counts}


def verify(path):
    """Re-import the package into a scratch collection and report what landed."""
    from anki.collection import Collection, ImportAnkiPackageRequest

    tmp = tempfile.mkdtemp()
    col = Collection(os.path.join(tmp, "verify.anki2"))
    col.import_anki_package(ImportAnkiPackageRequest(package_path=path))
    report = {
        "notes": col.note_count(),
        "cards": col.card_count(),
        "decks": {d.name: col.decks.card_count([d.id], include_subdecks=False)
                  for d in col.decks.all_names_and_ids()
                  if col.decks.card_count([d.id], include_subdecks=False)},
        "notetypes": sorted({col.get_note(n).note_type()["name"]
                             for n in col.find_notes("")}),
        "untagged": len(col.find_notes("-tag:*")),
        "cloze_render_ok": all(
            "[...]" in col.get_note(n).cards()[0].question()
            for n in col.find_notes("")
            if CLOZE_RE.search(col.get_note(n).fields[0])),
    }
    col.close()
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="deck JSON")
    ap.add_argument("-o", "--output", required=True, help="output .apkg")
    ap.add_argument("--deck", help="deck name (overrides the JSON's)")
    ap.add_argument("--verify", action="store_true",
                    help="re-import the result and print what landed")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)
    result = build(data, args.output, args.deck)
    print(json.dumps(result, indent=2))
    if args.verify:
        print(json.dumps(verify(args.output), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
