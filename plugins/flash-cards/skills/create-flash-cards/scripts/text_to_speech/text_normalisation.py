import re
from collections.abc import Callable

from .constants import BigUnits, Digits, LetterReadings, SmallUnits


class TextNormalisation:
    @staticmethod
    def speech_text(card_text: str) -> str:
        """Turn card notation into what should actually be spoken.

        Examples:
        잘 지냈어(요)? -> 잘 지냈어요?
        (네/예), ... -> 네, ...
        ₩1,200 -> 천이백원
        저는 ___이에요/예요 -> 저는 이에요
        A-58번 -> 에이 오십팔번
        """
        text = re.sub(r"<[^>]+>", " ", card_text)
        text = re.sub(r"\[[^\]]*\]", "", text)
        text = text.replace("_", "")
        text = re.sub(r"\(([^)]*)\)", lambda match: match.group(1).split("/")[0], text)
        text = re.sub(r"(\S+?)\s*/\s*\S+", r"\1", text)
        text = re.sub(r"₩\s*([\d,]+)", r"\1원", text)
        spell_out_number: Callable[..., str] = lambda match: (
            TextNormalisation.read_sino_korean(int(match.group().replace(",", "")))
        )
        text = re.sub(r"\d[\d,]*", spell_out_number, text)
        text = re.sub(
            r"[A-Za-z]",
            lambda match: LetterReadings[match.group().upper()] + " ",
            text,
        )
        text = text.replace("-", " ")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def read_sino_korean(number: int) -> str:
        """Read an integer in Sino-Korean: 4100 -> 사천백, 10000 -> 만."""
        if number == 0:
            return Digits.영.name

        readings: list[str] = []
        for unit in reversed(BigUnits):
            reading, number = TextNormalisation._read_big_unit(number, unit)
            if reading is not None:
                readings.append(reading)

        if number:
            readings.append(TextNormalisation._read_under_ten_thousand(number))
        return "".join(readings)

    @staticmethod
    def _read_big_unit(number: int, unit: BigUnits) -> tuple[str | None, int]:
        """Read the 만/억/조 part of a number, returning it with what's left below it."""
        count, remainder = divmod(number, unit)

        if count == 0:
            return None, remainder

        # a bare 만 is read without 일 (만, not 일만)
        omit_one = count == 1 and unit is BigUnits.만
        count_reading = (
            "" if omit_one else TextNormalisation._read_under_ten_thousand(count)
        )
        return count_reading + unit.name, remainder

    @staticmethod
    def _read_under_ten_thousand(number: int) -> str:
        """Read 1-9999: 4100 -> 사천백."""
        readings: list[str] = []
        for unit in reversed(SmallUnits):
            digit = (number // unit) % 10
            if digit:
                # 일 is dropped before 십/백/천 (십, not 일십)
                digit_reading = "" if digit == 1 else Digits(digit).name
                place_reading = digit_reading + unit.name
                readings.append(place_reading)
        ones = number % 10
        if ones != 0:
            readings.append(Digits(ones).name)
        return "".join(readings)
