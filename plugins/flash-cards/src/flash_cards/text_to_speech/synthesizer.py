import shutil
import subprocess
import wave
from io import BytesIO
from pathlib import Path

from .cache_paths import CachePaths
from .constants import VOICE
from .text_normalisation import TextNormalisation


class Synthesizer:
    def __init__(self, voice: str, paths: CachePaths) -> None:
        from piper import PiperVoice

        self._assert_ffmpeg_installed()
        self._paths: CachePaths = paths
        model_path = self._paths.voice_model(voice)
        espeak_data_dir = self._paths.espeak_data()
        self._voice: PiperVoice = PiperVoice.load(
            model_path=model_path, espeak_data_dir=espeak_data_dir
        )

    @staticmethod
    def _assert_ffmpeg_installed():
        ffmpeg_missing = not shutil.which("ffmpeg")
        if ffmpeg_missing:
            raise SystemExit(
                "ffmpeg not found on PATH - install it with `brew install ffmpeg`"
            )

    def synthesize(self, korean: str, speed: float) -> Path:
        """Return the path of the MP3 for this card text, generating it if not cached.

        Speed slows the voice itself (Piper's length_scale) rather than time-stretching
        the audio, which keeps slow speech natural.
        """

        normalised_text = TextNormalisation.speech_text(korean)
        path = self._paths.audio_path(normalised_text, speed)
        if self._paths.is_cached(normalised_text, speed):
            return path

        buffer = BytesIO()
        self._synthesize_wav(normalised_text, buffer, speed)
        self._encode_mp3(path, buffer)
        return path

    def _synthesize_wav(self, text: str, buffer: BytesIO, speed: float):
        from piper import SynthesisConfig

        with wave.open(buffer, "wb") as wav_file:
            length_scale = self._voice.config.length_scale / speed
            config = SynthesisConfig(length_scale=length_scale)
            _ = self._voice.synthesize_wav(text, wav_file, syn_config=config)

    @staticmethod
    def _encode_mp3(path: Path, buffer: BytesIO):
        subprocess_arguments = (
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "wav",
            "-i",
            "pipe:0",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            path,
        )
        _ = subprocess.run(
            subprocess_arguments,
            input=buffer.getvalue(),
            check=True,
        )
