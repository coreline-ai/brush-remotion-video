"""tts.py — Supertonic TTS: 대본/자막 텍스트 → 더빙 wav + 타이밍 SRT.

한국어 문장부호로 분리 → 문장별 합성 → pauseMs 무음 삽입 연결.
타이밍의 시계는 **합성된 각 wav 의 실제 샘플 길이** — 문장 길이 합 + pause 합 =
최종 wav 길이 = SRT 마지막 타임스탬프가 항상 정합한다.

supertonic 미설치 시 침묵 폴백 없이 설치 명령을 담은 명확한 에러를 낸다.
"""
from __future__ import annotations

import logging
import re
import wave
from pathlib import Path

import numpy as np

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


def _make_synthesizer(voice: str, lang: str):
    """문장 → (mono float wav 1D 배열) 합성 함수 생성."""
    st = _import_supertonic()
    tts = st.TTS(auto_download=True)
    style = tts.get_voice_style(voice)

    def synth(text: str) -> np.ndarray:
        wav, _dur = tts.synthesize(text, voice_style=style, lang=lang)
        return np.asarray(wav, dtype=np.float32).reshape(-1)

    return synth


def format_srt_time(sec: float) -> str:
    ms = round(sec * 1000)
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def synthesize_narration(text: str, out_wav: str | Path, out_srt: str | Path, *,
                         engine: str = "supertonic", voice: str = "F1", pause_ms: int = 300,
                         lang: str = "ko", synth=None) -> dict:
    """대본 텍스트 → 더빙 wav + SRT. 반환: {wav, srt, entries, durationSec}.

    synth 는 테스트 주입용 (문장 → 1D float 배열). 미지정 시 supertonic 사용.
    """
    if engine != "supertonic":
        raise ValueError(f"지원하지 않는 TTS 엔진: {engine!r} (현재 supertonic 만 지원)")
    sentences = split_sentences(text)
    if not sentences:
        raise ValueError("TTS 입력 텍스트에 문장이 없음")
    if synth is None:
        synth = _make_synthesizer(voice, lang)

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
    return {"wav": str(out_wav), "srt": str(out_srt), "entries": entries, "durationSec": total}
