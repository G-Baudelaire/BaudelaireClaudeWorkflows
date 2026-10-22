import html
import re
from dataclasses import dataclass
from functools import cached_property
from typing import Any


@dataclass(frozen=True)  # noqa: F821
class Note:
    index: int
    fields: tuple[str, ...]
    tags: tuple[str, ...]

    @cached_property
    def front_raw(self) -> str:
        return self.fields[0] if self.fields else ""

    @cached_property
    def back_raw(self) -> str:
        return " ".join(f for f in self.fields[1:] if f.strip())

    @cached_property
    def front(self) -> str:
        return _strip_html(self.front_raw)

    @cached_property
    def back(self) -> str:
        return _strip_html(self.back_raw)

    @cached_property
    def words(self) -> list[str]:
        return self.front.split()


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()
