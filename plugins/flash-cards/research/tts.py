"""Korean text-to-speech: normalise card text for speech, synthesise with Piper, encode MP3.

Prototype of the plugin's scripts/tts.py. Must not import any Anki or note code.

Needs `piper-tts` (declared by the calling script) and `ffmpeg` on PATH. The voice model
and a short-path copy of espeak-ng's data are fetched into CACHE_DIR on first use.
"""

import hashlib
import io
import os
import re
import shutil
import subprocess
import wave
from importlib.metadata import version
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "korean-flashcards"
VOICE = "ko_KR-kss-medium"

DIGITS = "영일이삼사오육칠팔구"
SMALL_UNITS = ["", "십", "백", "천"]
BIG_UNITS = ["", "만", "억", "조"]
LATIN = {"A": "에이", "B": "비", "C": "씨", "D": "디", "E": "이", "F": "에프", "G": "지",
         "H": "에이치", "I": "아이", "J": "제이", "K": "케이", "L": "엘", "M": "엠", "N": "엔",
         "O": "오", "P": "피", "Q": "큐", "R": "알", "S": "에스", "T": "티", "U": "유",
         "V": "브이", "W": "더블유", "X": "엑스", "Y": "와이", "Z": "제트"}


def sino_korean(n):
    """Read an integer in Sino-Korean: 4100 -> 사천백, 10000 -> 만."""
    if n == 0:
        return DIGITS[0]
    out = []
    group = 0
    while n:
        n, chunk = divmod(n, 10000)
        if chunk:
            words = []
            for pos in range(3, -1, -1):
                d = chunk // 10 ** pos % 10
                if d:
                    # 일 is dropped before 십/백/천 (십, not 일십)
                    words.append(("" if d == 1 and pos else DIGITS[d]) + SMALL_UNITS[pos])
            text = "".join(words)
            # a bare 만 is read without 일 (만, not 일만)
            if group == 1 and text == "일":
                text = ""
            out.append(text + BIG_UNITS[group])
        group += 1
    return "".join(reversed(out))


def speech_text(korean):
    """Turn card notation into what should actually be spoken.

    잘 지냈어(요)? -> 잘 지냈어요?   (네/예), ... -> 네, ...   ₩1,200 -> 천이백원
    저는 ___이에요/예요 -> 저는 이에요   A-58번 -> 에이 오십팔번
    """
    s = re.sub(r"<[^>]+>", " ", korean)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = s.replace("_", "")
    s = re.sub(r"\(([^)]*)\)", lambda m: m.group(1).split("/")[0], s)
    s = re.sub(r"(\S+?)\s*/\s*\S+", r"\1", s)
    s = re.sub(r"₩\s*([\d,]+)", r"\1원", s)
    s = re.sub(r"\d[\d,]*", lambda m: sino_korean(int(m.group().replace(",", ""))), s)
    s = re.sub(r"[A-Za-z]", lambda m: LATIN[m.group().upper()] + " ", s)
    s = s.replace("-", " ")
    return re.sub(r"\s+", " ", s).strip()


def audio_filename(text, speed=1.0):
    """ko_<hash>.mp3 at normal speed, ko_<hash>_s060.mp3 at 0.6x."""
    suffix = "" if speed == 1.0 else f"_s{round(speed * 100):03d}"
    return "ko_" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + suffix + ".mp3"


def voice_path(voice=VOICE):
    """Download the Piper voice into the cache on first use."""
    from piper.download_voices import download_voice

    voices = CACHE_DIR / "voices"
    voices.mkdir(parents=True, exist_ok=True)
    download_voice(voice, voices)
    return voices / f"{voice}.onnx"


def espeak_data_dir():
    """Short-path copy of piper's bundled espeak-ng data.

    espeak-ng silently ignores data paths over ~160 chars and falls back to a build-time
    path that doesn't exist (a 'phontab' error). uv's environments live deep enough to
    hit that, so copy the data somewhere short, once per piper version.
    """
    import piper

    target = CACHE_DIR / f"espeak-ng-data-{version('piper-tts')}"
    if not target.exists():
        tmp = target.with_suffix(".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.copytree(Path(piper.__file__).parent / "espeak-ng-data", tmp)
        tmp.rename(target)
    return target


class Synthesizer:
    def __init__(self, cache_dir=CACHE_DIR / "audio", voice=VOICE):
        from piper import PiperVoice

        if not shutil.which("ffmpeg"):
            raise SystemExit("ffmpeg not found on PATH - install it with `brew install ffmpeg`")
        self.voice = PiperVoice.load(voice_path(voice), espeak_data_dir=espeak_data_dir())
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def synthesize(self, korean, speed=1.0):
        """Return the path of the MP3 for this card text, generating it if not cached.

        Speed slows the voice itself (Piper's length_scale) rather than time-stretching
        the audio, which keeps slow speech natural.
        """
        from piper import SynthesisConfig

        text = speech_text(korean)
        path = os.path.join(self.cache_dir, audio_filename(text, speed))
        if os.path.exists(path):
            return path
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            config = SynthesisConfig(length_scale=self.voice.config.length_scale / speed)
            self.voice.synthesize_wav(text, wav_file, syn_config=config)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "wav", "-i", "pipe:0",
                        "-codec:a", "libmp3lame", "-q:a", "4", path],
                       input=buf.getvalue(), check=True)
        return path
