"""tts.py — Supertonic TTS: 대본/자막 텍스트 → 더빙 wav + 타이밍 SRT.

한국어 문장부호로 분리 → 문장별 합성 → pauseMs 무음 삽입 연결.
타이밍의 시계는 **합성된 각 wav 의 실제 샘플 길이** — 문장 길이 합 + pause 합 =
최종 wav 길이 = SRT 마지막 타임스탬프가 항상 정합한다.

supertonic 미설치 시 침묵 폴백 없이 설치 명령을 담은 명확한 에러를 낸다.
"""
from __future__ import annotations

import logging
import math
import re
import wave
from pathlib import Path

import numpy as np

from .voice_presets import (
    SPEED_MAX,
    SPEED_MIN,
    build_voice_style,
    load_catalog,
    resolve_voice,
)

log = logging.getLogger(__name__)

SR = 44100  # supertonic 출력 샘플레이트
INSTALL_HINT = 'TTS 사용을 위해 supertonic 이 필요합니다. 설치: pipeline/.venv/bin/pip install -e "pipeline[tts]"'

_SENT_RE = re.compile(r"[^.!?。…]+[.!?。…]*")


def split_sentences(text: str) -> list[str]:
    """한국어 문장부호(.!?…) 기준 문장 분리. 빈 조각은 제거."""
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for m in _SENT_RE.finditer(line):
            s = m.group().strip()
            if s:
                out.append(s)
    return out


def _import_supertonic():
    """supertonic 임포트 — 미설치 시 설치 명령 포함 에러 (침묵 폴백 금지)."""
    try:
        import supertonic
        return supertonic
    except ImportError as e:
        raise RuntimeError(INSTALL_HINT) from e


def _make_synthesizer(voice: str, lang: str, speed: float):
    """문장 합성 함수와 실제 해석된 voice metadata를 생성."""
    st = _import_supertonic()
    catalog = load_catalog()
    expected_package = catalog["engine"]["packageVersion"]
    actual_package = getattr(st, "__version__", "unknown")
    if actual_package != expected_package:
        raise RuntimeError(
            f"Supertonic 버전 불일치: voice pack은 {expected_package}, 설치 버전은 {actual_package}. "
            f'설치: pipeline/.venv/bin/pip install "supertonic=={expected_package}"'
        )
    tts = st.TTS(auto_download=True)
    style, metadata = build_voice_style(tts, voice, catalog=catalog)
    metadata.update({
        "engine": "supertonic",
        "packageVersion": actual_package,
        "model": getattr(tts, "model_name", catalog["engine"]["model"]),
        "language": lang,
        "sampleRate": getattr(tts, "sample_rate", SR),
        "speed": speed,
    })

    def synth(text: str) -> np.ndarray:
        wav, _dur = tts.synthesize(text, voice_style=style, lang=lang, speed=speed)
        return np.asarray(wav, dtype=np.float32).reshape(-1)

    return synth, metadata


def format_srt_time(sec: float) -> str:
    ms = round(sec * 1000)
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def synthesize_narration(text: str, out_wav: str | Path, out_srt: str | Path, *,
                         engine: str = "supertonic", voice: str = "F1", pause_ms: int = 300,
                         speed: float = 1.05, lang: str = "ko", synth=None) -> dict:
    """대본 텍스트 → 더빙 wav + SRT. 반환: {wav, srt, entries, durationSec}.

    synth 는 테스트 주입용 (문장 → 1D float 배열). 미지정 시 supertonic 사용.
    """
    if engine != "supertonic":
        raise ValueError(f"지원하지 않는 TTS 엔진: {engine!r} (현재 supertonic 만 지원)")
    if not isinstance(speed, (int, float)) or isinstance(speed, bool) or not math.isfinite(float(speed)):
        raise ValueError("TTS speed는 유한한 숫자여야 함")
    speed = float(speed)
    if not SPEED_MIN <= speed <= SPEED_MAX:
        raise ValueError(f"TTS speed는 {SPEED_MIN:.2f}~{SPEED_MAX:.2f} 범위여야 함")
    sentences = split_sentences(text)
    if not sentences:
        raise ValueError("TTS 입력 텍스트에 문장이 없음")
    if synth is None:
        synth, voice_metadata = _make_synthesizer(voice, lang, speed)
    else:
        # 테스트/외부 주입 합성기도 ID 계약은 동일하게 검증한다.
        catalog = load_catalog()
        voice_metadata = resolve_voice(voice, catalog)
        voice_metadata.update({
            "engine": engine,
            "packageVersion": "injected-synth",
            "model": catalog["engine"]["model"],
            "language": lang,
            "sampleRate": SR,
            "speed": speed,
            "styleSourceSha256": {
                name: catalog["baseStyleSha256"].get(name)
                for name in voice_metadata["components"]
            },
            "styleSourceKind": "catalog-expected",
            "styleSha256": None,
        })

    pause = np.zeros(int(SR * pause_ms / 1000), dtype=np.float32)
    parts: list[np.ndarray] = []
    entries: list[dict] = []
    t = 0.0
    for i, s in enumerate(sentences):
        seg = synth(s)
        dur = len(seg) / SR  # 실제 샘플 길이가 타이밍의 시계
        entries.append({"index": i + 1, "start": t, "end": t + dur, "text": s})
        parts.append(seg)
        t += dur
        if i < len(sentences) - 1:
            parts.append(pause)
            t += len(pause) / SR
        log.info("tts %d/%d: %.2fs — %s", i + 1, len(sentences), dur, s[:32])

    audio = np.concatenate(parts)
    out_wav, out_srt = Path(out_wav), Path(out_srt)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    pcm16 = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16.tobytes())

    srt_text = "\n".join(
        f"{e['index']}\n{format_srt_time(e['start'])} --> {format_srt_time(e['end'])}\n{e['text']}\n"
        for e in entries)
    out_srt.parent.mkdir(parents=True, exist_ok=True)
    out_srt.write_text(srt_text, encoding="utf-8")
    total = len(audio) / SR
    log.info("tts 완료: 문장 %d개, %.2fs -> %s / %s", len(sentences), total, out_wav, out_srt)
    return {
        "wav": str(out_wav), "srt": str(out_srt), "entries": entries,
        "durationSec": total, "voice": voice_metadata,
    }
