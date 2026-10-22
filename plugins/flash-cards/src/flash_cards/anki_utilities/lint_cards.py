"""Flag mechanical violations of the 8 flashcard rules in a deck.

Input is the JSON produced by `anki-io to-json` (or the deck file itself,
which is converted internally). Output is a markdown report plus a JSON summary.

The checks look at *shape*, not meaning: they cannot tell whether a back
actually answers its front, whether a fact is correct, or whether a card is
worth having. Treat every flag as a prompt to read the card, not a verdict.

Usage:
    uv run lint-cards deck.json --report lint.md
    uv run lint-cards deck.txt  --report lint.md --json lint.json
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable

from .anki_io import read_deck
from .checks import (
    Check,
    Code,
    Flag,
    cloze_without_number,
    conjunction_front,
    context_dependent,
    dangling_pronoun,
    empty_back,
    empty_front,
    field_count,
    list_front,
    long_front,
    multi_question,
    no_example,
    stapled_front,
    thin_back,
    unbalanced_cloze,
    untagged,
    vague_back,
)
from .protocols import Note

DEFAULT_CHECKS: tuple[Check, ...] = (
    empty_front,
    long_front,
    multi_question,
    stapled_front,
    conjunction_front,
    list_front,
    empty_back,
    vague_back,
    thin_back,
    no_example,
    context_dependent,
    dangling_pronoun,
    untagged,
    unbalanced_cloze,
    cloze_without_number,
)


def lint(note: Note, checks: Iterable[Check]) -> list[Flag]:
    return [flag for check in checks if (flag := check(note))]


def parse_args() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    _ = argument_parser.add_argument(
        "path", help="deck JSON (from anki-io to-json) or a deck .txt/.tsv/.csv"
    )
    _ = argument_parser.add_argument("--report", help="write markdown report here")
    _ = argument_parser.add_argument(
        "--json", dest="json_out", help="write JSON summary here"
    )
    _ = argument_parser.add_argument(
        "--max-examples",
        type=int,
        default=6,
        help="cards shown per issue in the report",
    )
    return argument_parser.parse_args()


def main() -> None:
    args = parse_args()
    deck = read_deck(args.path)

    notes = deck.notes
    widths = Counter(len(n.fields) for n in notes)
    checks = [
        *DEFAULT_CHECKS,
        field_count(widths.most_common(1)[0][0] if widths else 0),
    ]

    results = []
    by_code = defaultdict(list)
    for note in notes:
        flags = lint(note, checks)
        if flags:
            results.append(
                {
                    "index": note.index,
                    "front": note.front[:100],
                    "flags": [
                        {"rule": flag.rule, "code": flag.code, "detail": flag.detail}
                        for flag in flags
                    ],
                }
            )
            for flag in flags:
                by_code[flag.code].append((note.index, note.front[:80], flag.detail))
    # Reading arguments

    # Duplicate / near-duplicate fronts (normalised).
    norm = defaultdict(list)
    for note in notes:
        # Lowercase and drop trailing punctuation only — stripping all symbols
        # would make "What does % match?" and "What does _ match?" collide.
        key = re.sub(r"[\s?.!:]+$", "", note.front.lower()).strip()
        if key:
            norm[key].append(note.index)
    dupes = {k: v for k, v in norm.items() if len(v) > 1}
    for key, idxs in dupes.items():
        by_code[Code.DUPLICATE_FRONT].append(
            (idxs[0], key[:80], f"also at note(s) {idxs[1:]}")
        )

    total = len(notes)
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
    for code, items in sorted(by_code.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| {code.rule} | `{code}` | {len(items)} |")
    lines.append("")

    for code, items in sorted(by_code.items(), key=lambda kv: -len(kv[1])):
        lines += [f"### `{code}` (rule {code.rule}) — {len(items)} card(s)", ""]
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
        "counts": {f"{code} (rule {code.rule})": len(v) for code, v in by_code.items()},
        "notes": results,
    }
    if args.json_out:
        json.dump(
            summary,
            open(args.json_out, "w", encoding="utf-8"),
            indent=2,
            ensure_ascii=False,
        )
        print(f"json   -> {args.json_out}")


if __name__ == "__main__":
    main()
