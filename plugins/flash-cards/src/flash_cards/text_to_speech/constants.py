from enum import IntEnum, StrEnum
from pathlib import Path


CACHE_DIR = Path.home() / ".cache" / "korean-flashcards"
VOICE = "ko_KR-kss-medium"


class LetterReadings(StrEnum):
    """How a Korean speaker reads each Latin letter aloud: LetterReadings.A == "에이"."""

    A = "에이"
    B = "비"
    C = "씨"
    D = "디"
    E = "이"
    F = "에프"
    G = "지"
    H = "에이치"
    I = "아이"
    J = "제이"
    K = "케이"
    L = "엘"
    M = "엠"
    N = "엔"
    O = "오"
    P = "피"
    Q = "큐"
    R = "알"
    S = "에스"
    T = "티"
    U = "유"
    V = "브이"
    W = "더블유"
    X = "엑스"
    Y = "와이"
    Z = "제트"


class Digits(IntEnum):
    영 = 0
    일 = 1
    이 = 2
    삼 = 3
    사 = 4
    오 = 5
    육 = 6
    칠 = 7
    팔 = 8
    구 = 9


class SmallUnits(IntEnum):
    십 = 10
    백 = 100
    천 = 1000


class BigUnits(IntEnum):
    만 = 10**4
    억 = 10**8
    조 = 10**12
