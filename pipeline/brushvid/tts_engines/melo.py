"""MeloTTS-Korean pinned local snapshot adapter."""
from __future__ import annotations

import importlib.metadata
import importlib.machinery
import sys
from types import ModuleType
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from ..tts_contract import (
    ENGINE_LICENSES,
    ENGINE_MODEL_IDS,
    MODEL_REVISIONS,
    resolve_local_snapshot,
)
from .base import AudioResult, TtsEngineUnavailableError


MODEL_FILES = ("config.json", "checkpoint.pth")


def _ensure_korean_mecab() -> None:
    """macOS case-insensitive FS에서 MeCab/mecab 패키지 충돌을 보정한다."""
    try:
        import mecab  # noqa: F401
        return
    except ModuleNotFoundError:
        pass
    try:
        import MeCab
        import mecab_ko_dic
    except ImportError as exc:
        raise TtsEngineUnavailableError("mecab-python3와 mecab-ko-dic가 필요함") from exc

    # g2pkk 0.1.2는 소문자 `mecab.MeCab().pos()` API를 기대한다. macOS
    # case-insensitive site-packages에서는 대문자 `MeCab` 패키지와 충돌하므로,
    # mecab-ko-dic를 사용하는 얇은 호환 모듈을 메모리에 등록한다.
    class KoreanMecab:
        def __init__(self):
            self._tagger = MeCab.Tagger(
                f'-r "{Path(MeCab.__file__).parent / "mecabrc"}" '
                f'-d "{mecab_ko_dic.dictionary_path}"'
            )

        def pos(self, sentence: str) -> list[tuple[str, str]]:
            node = self._tagger.parseToNode(sentence)
            result = []
            while node is not None:
                if node.surface:
                    result.append((node.surface, node.feature))
                node = node.next
            return result

    module = ModuleType("mecab")
    module.__spec__ = importlib.machinery.ModuleSpec("mecab", loader=None)
    module.MeCab = KoreanMecab
    sys.modules["mecab"] = module


class MeloAdapter:
    engine_id = "melo-ko"

    def __init__(
        self,
        *,
        model_dir: str | Path | None = None,
        device: str = "cpu",
        tts_factory: Callable[..., Any] | None = None,
    ) -> None:
        try:
            if tts_factory is None:
                _ensure_korean_mecab()
                from melo.api import TTS
                tts_factory = TTS
        except (ImportError, RuntimeError) as exc:
            raise TtsEngineUnavailableError(
                "melo-ko 환경을 사용할 수 없음. 설치: pipeline/.venv/bin/pip install -e 'pipeline[tts-melo]'"
            ) from exc
        snapshot = resolve_local_snapshot(
            ENGINE_MODEL_IDS[self.engine_id],
            MODEL_REVISIONS[self.engine_id],
            explicit_dir=model_dir,
            required_files=MODEL_FILES,
        )
        try:
            model = tts_factory(
                language="KR",
                device=device,
                use_hf=False,
                config_path=str(snapshot / "config.json"),
                ckpt_path=str(snapshot / "checkpoint.pth"),
            )
        except Exception as exc:
            raise TtsEngineUnavailableError(f"melo-ko pinned model 로드 실패: {exc}") from exc
        speakers = getattr(getattr(getattr(model, "hps", None), "data", None), "spk2id", {})
        if "KR" not in speakers:
            raise RuntimeError(f"melo-ko speaker KR 없음; 임의 fallback 금지: {sorted(speakers)}")
        self._model = model
        self._speaker_id = speakers["KR"]
        self._sample_rate = int(model.hps.data.sampling_rate)
        try:
            package_version = importlib.metadata.version("melotts")
        except importlib.metadata.PackageNotFoundError:
            package_version = "0.1.2"
        self.metadata = {
            "engine": self.engine_id,
            "model": ENGINE_MODEL_IDS[self.engine_id],
            "modelRevision": MODEL_REVISIONS[self.engine_id],
            "packageVersion": package_version,
            "language": "ko",
            "speaker": "KR",
            "nativeSampleRate": self._sample_rate,
            "speedAppliedBy": "melo-native-length-scale",
            "license": {**ENGINE_LICENSES[self.engine_id], "aiDisclosureRequired": True},
        }

    def synthesize(
        self,
        text: str,
        *,
        voice: str,
        language: str,
        speed: float,
        reference=None,
    ) -> AudioResult:
        if voice != "kr-default":
            raise ValueError(f"melo-ko voice는 kr-default만 지원함: {voice!r}")
        if language != "ko":
            raise ValueError(f"melo-ko language는 ko만 지원함: {language!r}")
        if reference is not None:
            raise ValueError("melo-ko는 reference를 지원하지 않음")
        _ensure_korean_mecab()
        samples = self._model.tts_to_file(
            text,
            self._speaker_id,
            output_path=None,
            speed=float(speed),
            quiet=True,
        )
        return AudioResult(np.asarray(samples, dtype=np.float32).reshape(-1), self._sample_rate, self.metadata)
