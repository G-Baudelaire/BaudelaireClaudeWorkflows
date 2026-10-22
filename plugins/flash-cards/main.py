import wave
from enum import StrEnum

from piper import PiperVoice


class KoreanSentences(StrEnum):
    GREETING = "안녕하세요, 만나서 반갑습니다."
    HELLO = "안녕하세요"


voice = PiperVoice.load("voices/ko_KR-kss-medium.onnx")
with wave.open("out.wav", "wb") as wav_file:
    _ = voice.synthesize_wav(KoreanSentences.GREETING.value, wav_file)
