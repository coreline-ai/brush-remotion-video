"""tts.py 테스트 — 문장 분리 / duration↔SRT 정합 / 미설치 에러 (전부 mock, 모델 불필요)."""
import wave

import numpy as np
import pytest

import brushvid.tts as tts_mod
from brushvid.cues import parse_srt
from brushvid.tts import SR, split_sentences, synthesize_narration


def _fake_synth(seconds_per_char=0.02):
    """문장 길이에 비례하는 가짜 wav 를 내는 합성기."""
    def synth(text: str) -> np.ndarray:
        n = max(1, int(SR * len(text) * seconds_per_char))
        return np.zeros(n, dtype=np.float32)
    return synth


def test_split_sentences_korean():
    text = "안녕하세요. 반갑습니다! 오늘 어때요? 마침표 없는 마지막 문장"
    assert split_sentences(text) == [
        "안녕하세요.", "반갑습니다!", "오늘 어때요?", "마침표 없는 마지막 문장"]


def test_duration_srt_wav_consistency(tmp_path):
    """문장별 duration 합 + pause = 최종 wav 길이 = SRT 마지막 타임스탬프."""
    text = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
    res = synthesize_narration(text, tmp_path / "n.wav", tmp_path / "n.srt",
                               pause_ms=300, synth=_fake_synth())
    entries = res["entries"]
    assert len(entries) == 3
    # wav 실제 길이
    with wave.open(str(tmp_path / "n.wav")) as w:
        wav_sec = w.getnframes() / w.getframerate()
        assert w.getframerate() == SR
    # 문장 duration 합 + pause 2회
    dur_sum = sum(e["end"] - e["start"] for e in entries) + 0.3 * 2
    assert wav_sec == pytest.approx(dur_sum, abs=1e-3)
    assert res["durationSec"] == pytest.approx(wav_sec, abs=1e-3)
    # SRT 마지막 타임스탬프 = 마지막 문장 end (pause 는 문장 사이에만)
    parsed = parse_srt((tmp_path / "n.srt").read_text(encoding="utf-8"))
    assert len(parsed) == 3
    assert parsed[-1].end == pytest.approx(entries[-1]["end"], abs=2e-3)
    assert parsed[-1].end == pytest.approx(wav_sec, abs=2e-3)
    # 문장 사이 pause 반영 확인
    assert parsed[1].start == pytest.approx(parsed[0].end + 0.3, abs=2e-3)


def test_missing_supertonic_clear_error(tmp_path, monkeypatch):
    """supertonic 미설치 → 설치 명령 포함 명확한 에러 (침묵 폴백 금지)."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "supertonic":
            raise ImportError("No module named 'supertonic'")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match=r'pip install -e "pipeline\[tts\]"'):
        synthesize_narration("한 문장.", tmp_path / "x.wav", tmp_path / "x.srt")


def test_unknown_engine_rejected(tmp_path):
    with pytest.raises(ValueError, match="엔진"):
        synthesize_narration("한 문장.", tmp_path / "x.wav", tmp_path / "x.srt",
                             engine="elevenlabs", synth=_fake_synth())


def test_empty_text_rejected(tmp_path):
    with pytest.raises(ValueError, match="문장"):
        synthesize_narration("   \n ", tmp_path / "x.wav", tmp_path / "x.srt",
                             synth=_fake_synth())
