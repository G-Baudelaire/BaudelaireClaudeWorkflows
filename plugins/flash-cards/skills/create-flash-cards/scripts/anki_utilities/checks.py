import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from protocols import Note

FRONT_CHAR_LIMIT = 120  # ~2 rendered lines
FRONT_WORD_LIMIT = 22
THIN_BACK_WORDS = 4

CONTEXT_PATTERNS = [
    r"\bfigure\s*\d",
    r"\bfig\.?\s*\d",
    r"\bdiagram above\b",
    r"\bimage above\b",
    r"\btable\s*\d+\.\d",
    r"\bslide\s*\d",
    r"\blecture\s*\d",
    r"\bchapter\s*\d",
    r"\bpage\s*\d+\b",
    r"\bas (?:seen|shown|discussed) (?:above|earlier|in class)\b",
    r"\bthe (?:above|previous|following)\b",
    r"\bmy notes\b",
    r"\bthis (?:course|module|unit)\b",
]

VAGUE_BACK_PATTERNS = [
    r"^\s*(?:it'?s )?complicated\.?\s*$",
    r"^\s*(?:it )?depends\.?\s*$",
    r"^\s*see (?:notes|slides|book|above)",
    r"^\s*tbd\.?\s*$",
    r"^\s*\?+\s*$",
    r"^\s*todo\b",
    r"^\s*n/?a\.?\s*$",
    r"^\s*\.\.\.\s*$",
]

EXAMPLE_MARKERS = [
    r"<div class=\"code\">",
    r"<pre",
    r"<code",
    r"\bexample\b",
    r"\be\.g\.",
    r"\bfor instance\b",
]

# Fronts that legitimately ask one thing while containing "and".
AND_EXEMPT = [
    r"\bstand for\b",
    r"\bstands for\b",
    r"\bmean\b",
    r"\bdifference between\b",
    r"\bvs\.?\b",
    r"\bcompared? (?:to|with)\b",
    r"\bbetween .+ and .+\?$",
]


class Code(StrEnum):
    """An issue a check can raise, bound to the one rule it breaks."""

    rule: str  # "1".."8", or "-" for field hygiene

    def __new__(cls, value: str, rule: str) -> "Code":
        member = str.__new__(cls, value)
        member._value_ = value
        member.rule = rule
        return member

    MULTI_QUESTION = "multi_question", "1"
    STAPLED_FRONT = "stapled_front", "1"
    CONJUNCTION_FRONT = "conjunction_front", "1"
    LIST_FRONT = "list_front", "1"
    DUPLICATE_FRONT = "duplicate_front", "1"
    BROKEN_CLOZE = "broken_cloze", "2"
    CONTEXT_DEPENDENT = "context_dependent", "3"
    DANGLING_PRONOUN = "dangling_pronoun", "3"
    THIN_BACK = "thin_back", "4"
    EMPTY_FRONT = "empty_front", "5"
    EMPTY_BACK = "empty_back", "5"
    VAGUE_BACK = "vague_back", "5"
    LONG_FRONT = "long_front", "6"
    NO_EXAMPLE = "no_example", "7"
    UNTAGGED = "untagged", "8"
    FIELD_COUNT = "field_count", "-"


@dataclass(frozen=True)
class Flag:
    code: Code
    detail: str

    @property
    def rule(self) -> str:
        return self.code.rule


Check = Callable[[Note], Flag | None]


def empty_front(note: Note) -> Flag | None:
    """Rule 5: the front must exist."""
    if not note.front:
        return Flag(Code.EMPTY_FRONT, "note has no first field")
    return None


def long_front(note: Note) -> Flag | None:
    """Rule 6: the front must be short."""
    if len(note.front) > FRONT_CHAR_LIMIT or len(note.words) > FRONT_WORD_LIMIT:
        return Flag(
            Code.LONG_FRONT, f"{len(note.front)} chars / {len(note.words)} words"
        )
    return None


def multi_question(note: Note) -> Flag | None:
    """Rule 1: one question per front."""
    if note.front.count("?") > 1:
        return Flag(
            Code.MULTI_QUESTION,
            f"{note.front.count('?')} question marks on the front",
        )
    return None


def stapled_front(note: Note) -> Flag | None:
    """Rule 1: no numbered sub-questions on one front."""
    if re.search(r"\bextra\s*\d", note.front, flags=re.IGNORECASE) or re.search(
        r"\bpart\s*\d\s*:", note.front, flags=re.IGNORECASE
    ):
        return Flag(Code.STAPLED_FRONT, "front bundles numbered sub-questions")
    return None


def conjunction_front(note: Note) -> Flag | None:
    """Rule 1: a long front joined by 'and' may be two questions."""
    if (
        re.search(r"\b(?:and|as well as|plus)\b", note.front, flags=re.IGNORECASE)
        and not _contains_any_patterns(AND_EXEMPT, note.front)
        and len(note.words) > 10
    ):
        return Flag(
            Code.CONJUNCTION_FRONT,
            "long front joined by 'and' — may be two questions",
        )
    return None


def list_front(note: Note) -> Flag | None:
    """Rule 1: list questions belong in a cloze or one card per item."""
    if re.search(
        r"\bname\s+(\d+|two|three|four|five|six)\b", note.front, flags=re.IGNORECASE
    ):
        return Flag(
            Code.LIST_FRONT, "asks for a list — consider cloze or one card per item"
        )
    return None


def empty_back(note: Note) -> Flag | None:
    """Rule 5: the back must exist."""
    if not note.back:
        return Flag(Code.EMPTY_BACK, "no answer content in any field after the first")
    return None


def vague_back(note: Note) -> Flag | None:
    """Rule 5: the back must say something, not a placeholder."""
    if note.back and _contains_any_patterns(VAGUE_BACK_PATTERNS, note.back):
        return Flag(Code.VAGUE_BACK, f"back reads as a placeholder: {note.back[:60]!r}")
    return None


def thin_back(note: Note) -> Flag | None:
    """Rule 4: a conceptual question needs more than a bare definition."""
    if not note.back or len(note.back.split()) > THIN_BACK_WORDS:
        return None
    conceptual = re.search(
        r"^(?:what is|what are|why|how|explain|describe)\b",
        note.front,
        flags=re.IGNORECASE,
    )
    lookup = re.search(
        r"\b(?:stand for|stands for|mean|called|keyword|syntax|which (?:clause|keyword|constraint|operator|function))\b",
        note.front,
        flags=re.IGNORECASE,
    )
    if conceptual and not lookup:
        return Flag(
            Code.THIN_BACK, f"{len(note.back.split())} words, conceptual question"
        )
    return None


def no_example(note: Note) -> Flag | None:
    """Rule 7: an explanatory card needs an example."""
    if (
        note.back
        and not _contains_any_patterns(EXAMPLE_MARKERS, note.back_raw)
        and re.search(
            r"^(?:explain|describe|how (?:do|can|does)|when (?:do|should)|why)\b",
            note.front,
            flags=re.IGNORECASE,
        )
        and len(note.back.split()) > THIN_BACK_WORDS
    ):
        return Flag(Code.NO_EXAMPLE, "explanatory card with no example on the back")
    return None


def context_dependent(note: Note) -> Flag | None:
    """Rule 3: the card must not rely on outside material."""
    if _contains_any_patterns(CONTEXT_PATTERNS, note.front) or _contains_any_patterns(
        CONTEXT_PATTERNS, note.back
    ):
        return Flag(Code.CONTEXT_DEPENDENT, "refers to material outside the card")
    return None


def dangling_pronoun(note: Note) -> Flag | None:
    """Rule 3: the front must not open with an unanchored pronoun."""
    if re.match(r"^(?:this|these|that|those|it)\b", note.front, flags=re.IGNORECASE):
        return Flag(Code.DANGLING_PRONOUN, "front opens with an unanchored pronoun")
    return None


def untagged(note: Note) -> Flag | None:
    """Rule 8: every note needs a topical tag."""
    if not note.tags or set(note.tags) <= {"leech", "marked"}:
        return Flag(Code.UNTAGGED, "no topical tag")
    return None


def unbalanced_cloze(note: Note) -> Flag | None:
    """Rule 2: cloze braces must balance."""
    blob = note.front_raw + note.back_raw
    if _contains_cloze(note) and blob.count("{{") != blob.count("}}"):
        return Flag(Code.BROKEN_CLOZE, "unbalanced cloze braces")
    return None


def cloze_without_number(note: Note) -> Flag | None:
    """Rule 2: cloze braces need a c-number."""
    blob = note.front_raw + note.back_raw
    if _contains_cloze(note) and not re.search(r"\{\{c\d+::", blob):
        return Flag(Code.BROKEN_CLOZE, "cloze braces without a c-number")
    return None


def _contains_cloze(note: Note) -> bool:
    """Rule 2 checks only apply when cloze markup is present."""
    return "{{c" in note.front_raw or "{{c" in note.back_raw


def field_count(expected: int) -> Check:
    """Field hygiene: every note has the deck's usual field count. Built per deck."""

    def check(note: Note) -> Flag | None:
        if expected and len(note.fields) != expected:
            return Flag(
                Code.FIELD_COUNT, f"{len(note.fields)} fields, deck uses {expected}"
            )
        return None

    return check


def _contains_any_patterns(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
