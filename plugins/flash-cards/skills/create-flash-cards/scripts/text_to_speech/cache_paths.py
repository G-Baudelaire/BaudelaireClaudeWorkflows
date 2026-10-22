import hashlib
import shutil
from importlib.metadata import version
from pathlib import Path

from .constants import CACHE_DIR


class CachePaths:
    """Where the voice model, espeak-ng data and generated audio live on disk."""

    def __init__(self, root: Path = CACHE_DIR) -> None:
        self._root: Path = root
        self._audio_dir: Path = root / "audio"
        self._audio_dir.mkdir(parents=True, exist_ok=True)

    def is_cached(self, text: str, speed: float) -> bool:
        return self.audio_path(text, speed).exists()

    def audio_path(self, text: str, speed: float) -> Path:
        return self._audio_dir / self.audio_filename(text, speed)

    @staticmethod
    def audio_filename(text: str, speed: float = 1.0) -> str:
        """ko_<hash>.mp3 at normal speed, ko_<hash>_s060.mp3 at 0.6x."""
        suffix = "" if speed == 1.0 else f"_s{round(speed * 100):03d}"
        return (
            "ko_"
            + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
            + suffix
            + ".mp3"
        )

    def voice_model(self, voice: str) -> Path:
        """Download the Piper voice into the cache on first use."""
        from piper.download_voices import download_voice

        voices = self._root / "voices"
        voices.mkdir(parents=True, exist_ok=True)
        download_voice(voice, voices)
        return voices / f"{voice}.onnx"

    def espeak_data(self) -> Path:
        """Short-path copy of piper's bundled espeak-ng data.

        espeak-ng silently ignores data paths over ~160 chars and falls back to a
        build-time path that doesn't exist (a 'phontab' error). uv's environments live
        deep enough to hit that, so copy the data somewhere short, once per piper
        version.
        """
        import piper

        target = self._root / f"espeak-ng-data-{version('piper-tts')}"
        if not target.exists():
            tmp = target.with_suffix(".tmp")
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.copytree(Path(piper.__file__).parent / "espeak-ng-data", tmp)
            tmp.rename(target)
        return target
