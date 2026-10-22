# /// script
# requires-python = ">=3.10"
# dependencies = ["anki==26.8.1"]
# ///
"""Import the migration package into a COPY of a real collection, the way a user would
(Merge note types ticked, update notes if newer), and check nothing was lost.

Usage: uv run dry_run.py <collection copy.anki2> <migration.apkg>
"""

import sys
from collections import Counter

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from anki.import_export_pb2 import ImportAnkiPackageUpdateCondition as UC

OLD_REVERSED_ID = 1747648970786
NEW_ID = 1607392322
SCHED = "id, nid, ord, did, type, queue, due, ivl, factor, reps, lapses, left, data"


def snapshot(col):
    return {
        "cards": {r[0]: r for r in col.db.all(f"select {SCHED} from cards")},
        "notes": {r[0]: r for r in col.db.all("select id, guid, mid, flds, tags from notes")},
        "revlog": col.db.scalar("select count() from revlog"),
        "by_type": Counter(m for (m,) in col.db.all("select mid from notes")),
    }


def main(path, pkg):
    col = Collection(path)
    before = snapshot(col)
    res = col.import_anki_package(ImportAnkiPackageRequest(
        package_path=pkg,
        options=ImportAnkiPackageOptions(merge_notetypes=True, with_scheduling=False,
                                         update_notes=UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER,
                                         update_notetypes=UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER)))
    log = res.log
    after = snapshot(col)
    problems = []

    print("import log: new=%d updated=%d duplicate=%d conflicting=%d missing_notetype=%d" % (
        len(log.new), len(log.updated), len(log.duplicate), len(log.conflicting),
        len(log.missing_notetype)))
    if len(log.updated) != 242 or log.new or log.conflicting:
        problems.append("unexpected import log")

    moved = {nid for nid, n in before["notes"].items() if n[2] == OLD_REVERSED_ID}
    print("notes", len(before["notes"]), "->", len(after["notes"]),
          "| cards", len(before["cards"]), "->", len(after["cards"]),
          "| revlog", before["revlog"], "->", after["revlog"])
    if len(before["notes"]) != len(after["notes"]) or len(before["cards"]) != len(after["cards"]):
        problems.append("note/card count changed")
    if before["revlog"] != after["revlog"]:
        problems.append("revlog changed")

    # every card keeps its id and scheduling; moved cards swap ord 0<->1
    sched_changed = ord_wrong = 0
    for cid, old in before["cards"].items():
        new = after["cards"].get(cid)
        if new is None:
            problems.append(f"card {cid} missing")
            continue
        expected_ord = 1 - old[2] if old[1] in moved else old[2]
        if new[2] != expected_ord:
            ord_wrong += 1
        if old[3:] != new[3:] or old[1] != new[1]:
            sched_changed += 1
    print("cards with changed scheduling/deck:", sched_changed, "| wrong direction:", ord_wrong)
    if sched_changed or ord_wrong:
        problems.append("scheduling or direction mismatch")

    # moved notes: new type, same guid, fields swapped, audio present
    bad_fields = 0
    lost_tags = Counter()
    for nid in moved:
        o, n = before["notes"][nid], after["notes"][nid]
        of, nf = o[3].split("\x1f"), n[3].split("\x1f")
        if n[2] != NEW_ID or n[1] != o[1] or nf[0] != of[1] or nf[1] != of[0] \
                or not nf[2].startswith("[sound:ko_") or "_s060.mp3" not in nf[3]:
            bad_fields += 1
        # imports replace tags, so Anki-managed per-user tags (leech, marked) are dropped
        for tag in set(o[4].split()) - set(n[4].split()):
            lost_tags[tag] += 1
    print("moved notes with wrong type/guid/fields/audio:", bad_fields)
    print("tags dropped by import (expected for leech/marked):", dict(lost_tags))
    if set(lost_tags) - {"leech", "marked"}:
        problems.append("content tags dropped")
    if bad_fields:
        problems.append("moved note content mismatch")

    untouched = [nid for nid in before["notes"] if nid not in moved
                 and before["notes"][nid] != after["notes"][nid]]
    print("other notes changed:", len(untouched))
    if untouched:
        problems.append("unrelated notes changed")

    missing = []
    for (f,) in col.db.all(f"select flds from notes where mid={NEW_ID}"):
        fields = f.split("\x1f")
        for name in (fields[2][7:-1], fields[3].split('"')[1]):
            if not col.media.have(name):
                missing.append(name)
    print("audio files missing from media:", len(missing))
    if missing:
        problems.append("missing media")

    names = {m.id: m.name for m in col.models.all_names_and_ids()}
    print("notes by type:", {names.get(k, k): v for k, v in after["by_type"].items()})
    print("RESULT:", "PASS" if not problems else "FAIL " + "; ".join(problems))
    col.close()


if __name__ == "__main__":
    main(*sys.argv[1:3])
