#!/usr/bin/env python3
"""Parse and write Anki plain-text deck exports without mangling them.

Deck exports contain tabs, quoted multi-line fields and HTML, so they need a
real CSV reader. This script converts a deck to JSON (safe to edit), converts
JSON back to a deck file, validates a written file by re-parsing it, and prints
quick stats.

Usage:
    python3 anki_io.py to-json   deck.txt  -o deck.json
    python3 anki_io.py from-json deck.json -o deck_out.txt
    python3 anki_io.py validate  deck_out.txt
    python3 anki_io.py stats     deck.txt

JSON shape:
    {
      "header": {"separator": "tab", "html": "true", "tags column": "4"},
      "header_lines": ["#separator:tab", ...],
      "tags_column": 4,          # 1-based, or null
      "notes": [
        {"index": 0, "fields": ["front", "back", "extra"], "tags": ["sql::basics"]},
        ...
      ]
    }
Editing rules: keep "fields" the same length for every note (it must match the
note type), put tags in "tags" not in the fields list, and use <br> rather than
newlines inside fields unless the original deck used real newlines.
"""

import argparse
import csv
import io
import json
import sys
from collections import Counter

SEPARATORS = {
    "tab": "\t",
    "comma": ",",
    "semicolon": ";",
    "colon": ":",
    "space": " ",
    "pipe": "|",
}


def parse_header(lines):
    """Return (header dict, raw header lines, number of lines consumed)."""
    header, raw, consumed = {}, [], 0
    for line in lines:
        if not line.startswith("#"):
            break
        raw.append(line.rstrip("\n"))
        consumed += 1
        body = line[1:].strip()
        if ":" in body:
            key, _, value = body.partition(":")
            header[key.strip().lower()] = value.strip()
    return header, raw, consumed


def separator_char(header):
    sep = header.get("separator", "tab").lower()
    return SEPARATORS.get(sep, sep if len(sep) == 1 else "\t")


def read_deck(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        lines = fh.readlines()

    header, raw_header, consumed = parse_header(lines)
    delim = separator_char(header)
    body = "".join(lines[consumed:])

    rows = [
        row
        for row in csv.reader(io.StringIO(body), delimiter=delim)
        if row and any(cell.strip() for cell in row)
    ]

    tags_col = header.get("tags column")
    tags_col = int(tags_col) if tags_col and tags_col.isdigit() else None

    notes = []
    for i, row in enumerate(rows):
        tags = []
        fields = list(row)
        if tags_col and len(row) >= tags_col:
            tags = row[tags_col - 1].split()
            fields = row[: tags_col - 1] + row[tags_col:]
        notes.append({"index": i, "fields": fields, "tags": tags})

    return {
        "header": header,
        "header_lines": raw_header,
        "tags_column": tags_col,
        "notes": notes,
    }


def write_deck(deck, path):
    delim = separator_char(deck.get("header", {}))
    tags_col = deck.get("tags_column")

    out = io.StringIO()
    writer = csv.writer(out, delimiter=delim, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    for note in deck["notes"]:
        fields = list(note.get("fields", []))
        tags = " ".join(note.get("tags", []))
        if tags_col:
            insert_at = min(tags_col - 1, len(fields))
            row = fields[:insert_at] + [tags] + fields[insert_at:]
        else:
            row = fields + ([tags] if tags else [])
        writer.writerow(row)

    header_lines = deck.get("header_lines") or []
    if not header_lines:
        header_lines = ["#separator:tab", "#html:true"]
        if tags_col:
            header_lines.append(f"#tags column:{tags_col}")

    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(header_lines) + "\n")
        fh.write(out.getvalue())


def deck_stats(deck):
    widths = Counter(len(n["fields"]) + (1 if deck.get("tags_column") else 0) for n in deck["notes"])
    tagged = sum(1 for n in deck["notes"] if n["tags"])
    tag_counts = Counter(t for n in deck["notes"] for t in n["tags"])
    fronts = [n["fields"][0].strip() for n in deck["notes"] if n["fields"]]
    dupes = [f for f, c in Counter(fronts).items() if c > 1]
    empty_backs = sum(
        1 for n in deck["notes"] if len(n["fields"]) < 2 or not n["fields"][1].strip()
    )
    return {
        "notes": len(deck["notes"]),
        "header": deck["header"],
        "column_counts": dict(widths),
        "tagged_notes": tagged,
        "untagged_notes": len(deck["notes"]) - tagged,
        "distinct_tags": dict(tag_counts),
        "duplicate_fronts": dupes,
        "empty_backs": empty_backs,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["to-json", "from-json", "validate", "stats"])
    ap.add_argument("path")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    if args.command == "to-json":
        deck = read_deck(args.path)
        text = json.dumps(deck, indent=2, ensure_ascii=False)
        if args.output:
            open(args.output, "w", encoding="utf-8").write(text)
            print(f"{len(deck['notes'])} notes -> {args.output}")
        else:
            print(text)

    elif args.command == "from-json":
        deck = json.load(open(args.path, encoding="utf-8"))
        if not args.output:
            sys.exit("from-json needs -o/--output")
        write_deck(deck, args.output)
        print(f"{len(deck['notes'])} notes -> {args.output}")

    elif args.command == "validate":
        deck = read_deck(args.path)
        stats = deck_stats(deck)
        problems = []
        if len(stats["column_counts"]) > 1:
            problems.append(f"inconsistent column counts: {stats['column_counts']}")
        if stats["empty_backs"]:
            problems.append(f"{stats['empty_backs']} note(s) with an empty second field")
        if stats["duplicate_fronts"]:
            problems.append(f"{len(stats['duplicate_fronts'])} duplicate first field(s)")
        if not deck["header_lines"]:
            problems.append("no header directives — Anki will guess the separator")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        if problems:
            print("\nPROBLEMS:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        print("\nOK: file re-parses cleanly.")

    else:  # stats
        print(json.dumps(deck_stats(read_deck(args.path)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
