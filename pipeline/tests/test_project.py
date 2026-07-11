"""project.py 테스트 — 모드 판정 3종(TC-4.1/4.2/4.3 판정부) + TC-4.E1(format 오타)."""
import logging

import pytest

from brushvid.project import load_project


def _write_yaml(tmp_path, body: str):
    p = tmp_path / "project.yaml"
    p.write_text(body, encoding="utf-8")
    return p


@pytest.fixture()
def media(tmp_path):
    srt = tmp_path / "voice.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:02,000\n안녕\n", encoding="utf-8")
    audio = tmp_path / "voice.mp3"
    audio.write_bytes(b"fake-mp3")
    return srt, audio


def test_tc_4_1_srt_and_audio_is_narration(tmp_path, media):
    """TC-4.1 판정부: srt+audio 제공 → narration (whisper 미호출 모드)."""
    cfg = load_project(_write_yaml(tmp_path, """
projectId: demo
format: youtube
input:
  srt: voice.srt
  audio: voice.mp3
"""))
    assert cfg.mode == "narration"
    assert cfg.srt.name == "voice.srt"
    assert cfg.audio.name == "voice.mp3"


def test_tc_4_2_audio_only_is_whisper(tmp_path, media):
    """TC-4.2 판정부: audio 만 → whisper 모드."""
    cfg = load_project(_write_yaml(tmp_path, """
projectId: demo
input:
  audio: voice.mp3
"""))
    assert cfg.mode == "whisper"


def test_tc_4_3_neither_is_ambient(tmp_path):
    """TC-4.3 판정부: 둘 다 없음 → ambient (기본 3씬)."""
    cfg = load_project(_write_yaml(tmp_path, """
projectId: demo
ambient:
  scenes: 3
"""))
    assert cfg.mode == "ambient"
    assert cfg.ambient_scenes == 3


def test_tc_4_e1_format_typo_rejected(tmp_path):
    """TC-4.E1: format 오타 → 즉시 ValueError (파이프라인 미진입)."""
    with pytest.raises(ValueError, match="format"):
        load_project(_write_yaml(tmp_path, """
projectId: demo
format: youtub
"""))


def test_missing_files_and_bad_strategy_rejected(tmp_path):
    """존재하지 않는 입력 파일 / 잘못된 배경 전략도 검증 단계에서 거부."""
    with pytest.raises(ValueError, match="input.srt"):
        load_project(_write_yaml(tmp_path, """
projectId: demo
input:
  srt: no-such.srt
"""))
    with pytest.raises(ValueError, match="strategy"):
        load_project(_write_yaml(tmp_path, """
projectId: demo
background:
  strategy: presett
"""))


def test_widgets_auto_deferred_to_none(tmp_path, caplog):
    """widgets: auto 는 보류 — 경고 후 none 으로 처리."""
    with caplog.at_level(logging.WARNING, logger="brushvid.project"):
        cfg = load_project(_write_yaml(tmp_path, """
projectId: demo
widgets: auto
"""))
    assert cfg.widgets == "none"
    assert any("보류" in r.message for r in caplog.records)


def test_widgets_authored_inline(tmp_path):
    """widgets 에 목록을 주면 authored 모드."""
    cfg = load_project(_write_yaml(tmp_path, """
projectId: demo
widgets:
  - type: stat
    label: 성장률
"""))
    assert cfg.widgets == "authored"
    assert cfg.authored_widgets[0]["type"] == "stat"
