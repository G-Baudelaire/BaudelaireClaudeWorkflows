import json
from pathlib import Path

from flash_cards.anki_utilities.build_apkg import build, load_notetypes, verify

DATA = Path(__file__).parent / "data"


def test_notetypes_ship_with_the_package() -> None:
    assert set(load_notetypes()) >= {"basic", "cloze"}


def test_build_then_verify(tmp_path: Path) -> None:
    out = tmp_path / "deck.apkg"
    deck = json.loads((DATA / "build_deck.json").read_text())

    built = build(deck, str(out), "Test::Base")
    assert built == {"notes": 2, "cards": 2, "deck": "Test::Base", "basic": 1, "cloze": 1}

    assert verify(str(out)) == {
        "notes": 2,
        "cards": 2,
        "decks": {"Test::Base": 2},
        "notetypes": ["Basic (skill: front/back/extra)", "Cloze (skill)"],
        "untagged": 0,
        "cloze_render_ok": True,
    }
