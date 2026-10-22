# /// script
# requires-python = ">=3.11"
# dependencies = ["anki==26.8.1", "piper-tts==1.8.0"]
# ///
"""Build the one-off migration package: the existing reversed Korean notes, same GUIDs,
moved onto `Korean vocab (skill)` with audio.

The new note type reuses the old type's field and template ids so that importing with
"Merge note types" maps each card's history onto the matching direction
(see merge_notetype_test.py).

Usage: uv run build_migration.py <export.apkg> <out.apkg>
"""

import json
import os
import sys
import tempfile

from anki.collection import (Collection, DeckIdLimit, ExportAnkiPackageOptions,
                             ImportAnkiPackageOptions, ImportAnkiPackageRequest)

from tts import Synthesizer

OLD_REVERSED_ID = 1747648970786
OLD_BASIC_ID = 1747648970785
NEW_ID = 1607392322
NEW_NAME = "Korean vocab (skill)"
EXTRA = '{{#Extra}}<br><br><div class="extra">{{Extra}}</div>{{/Extra}}'
SLOW_SPEED = 0.6
# AudioSlow holds a plain <audio> tag: Anki only auto-plays [sound:] tags, so the slow
# version stays silent until the button is pressed, but media check/export still see it
AUDIO = ('{{Audio}}{{#AudioSlow}}<span class="slow">{{AudioSlow}}<button type="button" '
         'onclick="this.parentElement.querySelector(\'audio\').play()">'
         f'{SLOW_SPEED:g}×</button>'
         '</span>{{/AudioSlow}}')


def add_korean_notetype(col):
    mm = col.models
    old = mm.get(OLD_REVERSED_ID)
    old_front, old_back = old["flds"][0]["id"], old["flds"][1]["id"]
    old_ko_en, old_en_ko = old["tmpls"][0]["id"], old["tmpls"][1]["id"]

    nt = mm.new(NEW_NAME)
    # keep the deck's existing look (stock centred style), not the skill's left-aligned CSS
    nt["css"] = old["css"]
    for name in ["English", "Korean", "Audio", "AudioSlow", "Extra"]:
        nt["flds"].append(mm.new_field(name))
    nt["flds"][0]["id"] = old_back
    nt["flds"][1]["id"] = old_front

    en_ko = mm.new_template("EN→KO")
    en_ko["qfmt"] = "{{English}}"
    en_ko["afmt"] = '{{FrontSide}}<hr id="answer">{{Korean}}<br>' + AUDIO + EXTRA
    en_ko["id"] = old_en_ko
    ko_en = mm.new_template("KO→EN")
    ko_en["qfmt"] = "{{Korean}}<br>" + AUDIO
    ko_en["afmt"] = '{{FrontSide}}<hr id="answer">{{English}}' + EXTRA
    ko_en["id"] = old_ko_en
    nt["tmpls"] = [en_ko, ko_en]
    mm.add_dict(nt)

    made = mm.by_name(NEW_NAME)
    db = col.db
    for table, column in (("notetypes", "id"), ("fields", "ntid"), ("templates", "ntid")):
        db.execute(f"update {table} set {column} = ? where {column} = ?", NEW_ID, made["id"])
    mm._clear_cache()
    return mm.get(NEW_ID)


def main(src, out):
    col = Collection(os.path.join(tempfile.mkdtemp(), "build.anki2"))
    col.import_anki_package(ImportAnkiPackageRequest(
        package_path=src, options=ImportAnkiPackageOptions(with_scheduling=False)))

    # particles/suffixes stay on Basic and are not part of this package
    col.remove_notes(col.find_notes(f"mid:{OLD_BASIC_ID}"))

    new = add_korean_notetype(col)
    nids = col.find_notes(f"mid:{OLD_REVERSED_ID}")
    req = col.models.change_notetype_info(old_notetype_id=OLD_REVERSED_ID,
                                          new_notetype_id=NEW_ID).input
    req.note_ids.extend(nids)
    req.new_fields[:] = [1, 0, -1, -1, -1]   # English <- Back, Korean <- Front
    req.new_templates[:] = [1, 0]        # EN→KO <- Card 2, KO→EN <- Card 1
    col.models.change_notetype_of_notes(req)

    synth = Synthesizer()
    for nid in nids:
        note = col.get_note(nid)
        name = col.media.add_file(synth.synthesize(note["Korean"]))
        note["Audio"] = f"[sound:{name}]"
        slow = col.media.add_file(synth.synthesize(note["Korean"], SLOW_SPEED))
        note["AudioSlow"] = f'<audio src="{slow}" preload="none"></audio>'
        col.update_note(note)

    if os.path.exists(out):
        os.remove(out)
    did = col.decks.id_for_name("Korean")
    col.export_anki_package(
        out_path=out,
        options=ExportAnkiPackageOptions(with_scheduling=False, with_media=True,
                                         legacy=False, with_deck_configs=False),
        limit=DeckIdLimit(deck_id=did))
    print(json.dumps({"notes": len(nids), "notetype": new["name"],
                      "cards": col.card_count(), "media": len(os.listdir(col.media.dir()))}))
    col.close()


if __name__ == "__main__":
    main(*sys.argv[1:3])
