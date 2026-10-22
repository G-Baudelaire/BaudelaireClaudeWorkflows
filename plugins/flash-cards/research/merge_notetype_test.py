# /// script
# requires-python = ">=3.10"
# dependencies = ["anki==26.8.1"]
# ///
import os, sys, tempfile, shutil
from anki.collection import (Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions,
                             ExportAnkiPackageOptions, DeckIdLimit)
from anki.import_export_pb2 import ImportAnkiPackageUpdateCondition as UC
SRC = sys.argv[1]; W = sys.argv[2]
REV_ID = 1747648970786

def fresh(name):
    p = os.path.join(W, name); shutil.rmtree(p, ignore_errors=True); os.makedirs(p)
    return Collection(os.path.join(p, "c.anki2"))

def collaborator():
    col = fresh("collab")
    col.import_anki_package(ImportAnkiPackageRequest(package_path=SRC,
        options=ImportAnkiPackageOptions(with_scheduling=True)))
    # give history to first 5 reversed notes (both cards)
    m = [m for m in col.models.all() if m["name"].startswith("Basic (and reversed card)+")][0]
    other = col.new_note(m); other.fields[0] = "Bonjour"; other.fields[1] = "Hello (French)"
    col.add_note(other, col.decks.id("French"))
    print("  added unrelated note on", m["name"])
    nids = col.find_notes(f"mid:{REV_ID}")[:5]
    cards = [col.db.all("select id from cards where nid=? order by ord", n) for n in nids]
    col.sched.set_due_date([c[0][0] for c in cards], "30")   # old Card 1 = KO→EN
    col.sched.set_due_date([c[1][0] for c in cards], "60")   # old Card 2 = EN→KO
    return col, nids

def snapshot(col, guids):
    out = {}
    for g in guids:
        r = col.db.first("select id, mid from notes where guid=?", g)
        if not r: out[g] = None; continue
        cards = col.db.all("select ord, ivl, id from cards where nid=? order by ord", r[0])
        out[g] = (col.models.get(r[1])["name"], col.get_note(r[0]).fields[:2], cards)
    return out

def package(kind):
    """Build a package carrying the same notes (same GUIDs) on a changed note type."""
    src = Collection(os.path.join(tempfile.mkdtemp(), "s.anki2"))
    src.import_anki_package(ImportAnkiPackageRequest(package_path=SRC,
        options=ImportAnkiPackageOptions(with_scheduling=False)))
    mm = src.models
    if kind == "new_type":
        nt = mm.new("Korean vocab (skill)")
        for f in ["English", "Korean", "Audio", "Extra"]: nt["flds"].append(mm.new_field(f))
        t1 = mm.new_template("EN→KO"); t1["qfmt"] = "{{English}}"; t1["afmt"] = "{{FrontSide}}<hr id=answer>{{Korean}}{{Audio}}"
        t2 = mm.new_template("KO→EN"); t2["qfmt"] = "{{Korean}}{{Audio}}"; t2["afmt"] = "{{FrontSide}}<hr id=answer>{{English}}"
        old = mm.get(REV_ID)
        # reuse the old ids: English<-Back, Korean<-Front; EN→KO<-Card 2, KO→EN<-Card 1
        nt["flds"][0]["id"] = old["flds"][1]["id"]; nt["flds"][1]["id"] = old["flds"][0]["id"]
        t1["id"] = old["tmpls"][1]["id"]; t2["id"] = old["tmpls"][0]["id"]
        print("  old ids", [f.get("id") for f in old["flds"]], [t.get("id") for t in old["tmpls"]])
        nt["tmpls"] = [t1, t2]; mm.add_dict(nt)
        new = mm.by_name("Korean vocab (skill)")
        old = mm.get(REV_ID)
        nids = src.find_notes(f"mid:{REV_ID}")
        # old Card1 (KO→EN, ord0) -> new ord1; old Card2 (EN→KO, ord1) -> new ord0
        info = mm.change_notetype_info(old_notetype_id=REV_ID, new_notetype_id=new["id"])
        req = info.input; req.note_ids.extend(nids)
        req.new_fields[:] = [1, 0, -1, -1]       # English<-Back, Korean<-Front
        req.new_templates[:] = [1, 0]
        mm.change_notetype_of_notes(req)
        for n in nids:
            note = src.get_note(n); note["Audio"] = "[sound:x.mp3]"; src.update_note(note)
    elif kind == "same_id_changed":
        nt = mm.get(REV_ID); nt["flds"].append(mm.new_field("Audio")); mm.update_dict(nt)
    p = os.path.join(W, f"{kind}.apkg")
    src.export_anki_package(out_path=p, options=ExportAnkiPackageOptions(with_scheduling=False,
        with_media=False, legacy=False, with_deck_configs=False), limit=None)
    src.close(); return p

for kind in ["new_type"]:
    pkg = package(kind)
    for merge in [True]:
        col, nids = collaborator()
        guids = [col.get_note(n).guid for n in nids[:2]]
        before = snapshot(col, guids)
        res = col.import_anki_package(ImportAnkiPackageRequest(package_path=pkg,
            options=ImportAnkiPackageOptions(merge_notetypes=merge, with_scheduling=False,
                update_notes=UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS,
                update_notetypes=UC.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_ALWAYS)))
        log = res.log
        print(f"\n### {kind} merge_notetypes={merge}")
        print("  log: new=%d updated=%d dup=%d conflicting=%d first_field=%d missing_nt=%d" % (
            len(log.new), len(log.updated), len(log.duplicate), len(log.conflicting),
            len(log.first_field_match), len(log.missing_notetype)))
        nt = col.models.by_name("Korean vocab (skill)")
        print("  templates:", [t["name"] for t in nt["tmpls"]], "fields:", [f["name"] for f in nt["flds"]])
        print("  collab old ids", [[f.get("id") for f in m["flds"]] + [t.get("id") for t in m["tmpls"]] for m in col.models.all() if m["name"].startswith("Basic (and")])
        r = col.db.first("select mid, flds from notes where flds like 'Bonjour%' or flds like '%Bonjour'")
        print("  unrelated note now on:", col.models.get(r[0])["name"], r[1].split(chr(31))[:2], "cards:", col.db.scalar("select count() from cards c join notes n on n.id=c.nid where n.flds like '%Bonjour%'"))
        print("  notes total:", col.note_count(), " notetypes:", sorted(m.name for m in col.models.all_names_and_ids()))
        after = snapshot(col, guids)
        for g in guids: print("  before", before[g], "\n  after ", after[g])
        col.close()
