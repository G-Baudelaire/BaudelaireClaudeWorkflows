#!/usr/bin/env python3
"""Flag mechanical violations of the 8 flashcard rules in a deck.

Input is the JSON produced by `anki_io.py to-json` (or the deck file itself,
which is converted internally). Output is a markdown report plus a JSON summary.

The checks look at *shape*, not meaning: they cannot tell whether a back
actually answers its front, whether a fact is correct, or whether a card is
worth having. Treat every flag as a prompt to read the card, not a verdict.

Usage:
    python3 lint_cards.py deck.json --report lint.md
    python3 lint_cards.py deck.txt  --report lint.md --json lint.json
"""

import argparse
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anki_io import read_deck  # noqa: E402

FRONT_CHAR_LIMIT = 120          # ~2 rendered lines
FRONT_WORD_LIMIT = 22
THIN_BACK_WORDS = 4

CONTEXT_PATTERNS = [
    r"\bfigure\s*\d", r"\bfig\.?\s*\d", r"\bdiagram above\b", r"\bimage above\b",
    r"\btable\s*\d+\.\d", r"\bslide\s*\d", r"\blecture\s*\d", r"\bchapter\s*\d",
    r"\bpage\s*\d+\b", r"\bas (?:seen|shown|discussed) (?:above|earlier|in class)\b",
    r"\bthe (?:above|previous|following)\b", r"\bmy notes\b", r"\bthis (?:course|module|unit)\b",
]

VAGUE_BACK_PATTERNS = [
    r"^\s*(?:it'?s )?complicated\.?\s*$", r"^\s*(?:it )?depends\.?\s*$",
    r"^\s*see (?:notes|slides|book|above)", r"^\s*tbd\.?\s*$", r"^\s*\?+\s*$",
    r"^\s*todo\b", r"^\s*n/?a\.?\s*$", r"^\s*\.\.\.\s*$",
]

EXAMPLE_MARKERS = [
    r"<div class=\"code\">", r"<pre", r"<code", r"\bexample\b", r"\be\.g\.", r"\bfor instance\b",
]

# Fronts that legitimately ask one thing while containing "and".
AND_EXEMPT = [
    r"\bstand for\b", r"\bstands for\b", r"\bmean\b", r"\bdifference between\b",
    r"\bvs\.?\b", r"\bcompared? (?:to|with)\b", r"\bbetween .+ and .+\?$",
]


def strip_html(text):
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def has_any(patterns, text):
    return any(re.search(p, text, flags=re.I) for p in patterns)


def check_note(note, fields_meta):
    """Return a list of (rule, code, detail) flags for one note."""
    flags = []
    fields = note["fields"]
    front_raw = fields[0] if fields else ""
    back_raw = " ".join(f for f in fields[1:] if f.strip())
    front, back = strip_html(front_raw), strip_html(back_raw)
    words = front.split()

    # Rule 5 / 6 — the front must exist and be short.
    if not front:
        flags.append(("5", "empty_front", "note has no first field"))
    if len(front) > FRONT_CHAR_LIMIT or len(words) > FRONT_WORD_LIMIT:
        flags.append(("6", "long_front", f"{len(front)} chars / {len(words)} words"))

    # Rule 1 — compound fronts.
    if front.count("?") > 1:
        flags.append(("1", "multi_question", f"{front.count('?')} question marks on the front"))
    if re.search(r"\bextra\s*\d", front, flags=re.I) or re.search(r"\bpart\s*\d\s*:", front, flags=re.I):
        flags.append(("1", "stapled_front", "front bundles numbered sub-questions"))
    if re.search(r"\b(?:and|as well as|plus)\b", front, flags=re.I) and not has_any(AND_EXEMPT, front):
        if len(words) > 10:
            flags.append(("1", "conjunction_front", "long front joined by 'and' — may be two questions"))
    if re.search(r"\bname\s+(\d+|two|three|four|five|six)\b", front, flags=re.I):
        flags.append(("1", "list_front", "asks for a list — consider cloze or one card per item"))

    # Rule 5 — back must exist and say something.
    if not back:
        flags.append(("5", "empty_back", "no answer content in any field after the first"))
    elif has_any(VAGUE_BACK_PATTERNS, back):
        flags.append(("5", "vague_back", f"back reads as a placeholder: {back[:60]!r}"))

    # Rule 4 — bare definition, no context.
    if back and len(back.split()) <= THIN_BACK_WORDS:
        conceptual = re.search(r"^(?:what is|what are|why|how|explain|describe)\b", front, flags=re.I)
        lookup = re.search(r"\b(?:stand for|stands for|mean|called|keyword|syntax|which (?:clause|keyword|constraint|operator|function))\b", front, flags=re.I)
        if conceptual and not lookup:
            flags.append(("4", "thin_back", f"{len(back.split())} words, conceptual question"))

    # Rule 7 — rule-shaped card with no example.
    if back and not has_any(EXAMPLE_MARKERS, back_raw):
        if re.search(r"^(?:explain|describe|how (?:do|can|does)|when (?:do|should)|why)\b", front, flags=re.I):
            if len(back.split()) > THIN_BACK_WORDS:
                flags.append(("7", "no_example", "explanatory card with no example on the back"))

    # Rule 3 — context dependence.
    if has_any(CONTEXT_PATTERNS, front) or has_any(CONTEXT_PATTERNS, back):
        flags.append(("3", "context_dependent", "refers to material outside the card"))
    if re.match(r"^(?:this|these|that|those|it)\b", front, flags=re.I):
        flags.append(("3", "dangling_pronoun", "front opens with an unanchored pronoun"))

    # Rule 8 — orphans.
    if not note["tags"] or set(note["tags"]) <= {"leech", "marked"}:
        flags.append(("8", "untagged", "no topical tag"))

    # Rule 2 — cloze sanity, only if cloze markup is present.
    if "{{c" in front_raw or "{{c" in back_raw:
        blob = front_raw + back_raw
        if blob.count("{{") != blob.count("}}"):
            flags.append(("2", "broken_cloze", "unbalanced cloze braces"))
        nums = set(re.findall(r"\{\{c(\d+)::", blob))
        if not nums:
            flags.append(("2", "broken_cloze", "cloze braces without a c-number"))

    # Field hygiene.
    if fields_meta["expected"] and len(fields) != fields_meta["expected"]:
        flags.append(("-", "field_count", f"{len(fields)} fields, deck uses {fields_meta['expected']}"))

    return flags


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="deck JSON (from anki_io.py to-json) or a deck .txt/.tsv/.csv")
    ap.add_argument("--report", help="write markdown report here")
    ap.add_argument("--json", dest="json_out", help="write JSON summary here")
    ap.add_argument("--max-examples", type=int, default=6, help="cards shown per issue in the report")
    args = ap.parse_args()

    if args.path.endswith(".json"):
        deck = json.load(open(args.path, encoding="utf-8"))
    else:
        deck = read_deck(args.path)

    widths = Counter(len(n["fields"]) for n in deck["notes"])
    fields_meta = {"expected": widths.most_common(1)[0][0] if widths else 0}

    results, by_code = [], defaultdict(list)
    for note in deck["notes"]:
        flags = check_note(note, fields_meta)
        if flags:
            results.append({"index": note["index"], "front": strip_html(note["fields"][0])[:100], "flags": flags})
            for rule, code, detail in flags:
                by_code[(rule, code)].append((note["index"], strip_html(note["fields"][0])[:80], detail))

    # Duplicate / near-duplicate fronts (normalised).
    norm = defaultdict(list)
    for note in deck["notes"]:
        # Lowercase and drop trailing punctuation only — stripping all symbols
        # would make "What does % match?" and "What does _ match?" collide.
        key = re.sub(r"[\s?.!:]+$", "", strip_html(note["fields"][0]).lower()).strip()
        if key:
            norm[key].append(note["index"])
    dupes = {k: v for k, v in norm.items() if len(v) > 1}
    for key, idxs in dupes.items():
        by_code[("1", "duplicate_front")].append((idxs[0], key[:80], f"also at note(s) {idxs[1:]}"))

    total = len(deck["notes"])
    clean = total - len(results)
    lines = [
        "# Flashcard lint report",
        "",
        f"- notes: **{total}**",
        f"- notes with no mechanical flags: **{clean}** ({clean * 100 // max(total, 1)}%)",
        f"- distinct issue types: **{len(by_code)}**",
        "",
        "Flags indicate shape, not correctness. Read each flagged card before changing it.",
        "",
        "## Issues by type",
        "",
        "| Rule | Issue | Cards |",
        "|---|---|---|",
    ]
    for (rule, code), items in sorted(by_code.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| {rule} | `{code}` | {len(items)} |")
    lines.append("")

    for (rule, code), items in sorted(by_code.items(), key=lambda kv: -len(kv[1])):
        lines += [f"### `{code}` (rule {rule}) — {len(items)} card(s)", ""]
        for idx, front, detail in items[: args.max_examples]:
            lines.append(f"- **#{idx}** {front} — _{detail}_")
        if len(items) > args.max_examples:
            lines.append(f"- …and {len(items) - args.max_examples} more")
        lines.append("")

    report = "\n".join(lines)
    if args.report:
        open(args.report, "w", encoding="utf-8").write(report)
        print(f"report -> {args.report}")
    else:
        print(report)

    summary = {
        "total_notes": total,
        "flagged_notes": len(results),
        "counts": {f"{code} (rule {rule})": len(v) for (rule, code), v in by_code.items()},
        "notes": results,
    }
    if args.json_out:
        json.dump(summary, open(args.json_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"json   -> {args.json_out}")


if __name__ == "__main__":
    main()
