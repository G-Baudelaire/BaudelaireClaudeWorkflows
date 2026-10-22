"""Golden test: lint-cards output on the TODO_MAIN_REFACTOR deck must not drift.

The expected files are the output of the pre-package scripts. If a change to the
report is intended, regenerate them and say so in the commit.
"""

import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"


def test_report_and_json_match_baseline(tmp_path: Path) -> None:
    report, summary = tmp_path / "lint.md", tmp_path / "lint.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "flash_cards.anki_utilities.lint_cards",
            DATA / "lint_deck.json",
            "--report",
            report,
            "--json",
            summary,
        ],
        check=True,
        capture_output=True,
    )
    assert report.read_text() == (DATA / "lint_expected.md").read_text()
    assert summary.read_text() == (DATA / "lint_expected.json").read_text()
