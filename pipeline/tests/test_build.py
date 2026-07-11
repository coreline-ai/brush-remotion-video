"""bin/build.py 스테이지 캐시/스킵/재개 로직 단위 테스트."""
import importlib.util
import logging
from pathlib import Path

import pytest

BUILD_PY = Path(__file__).resolve().parents[2] / "bin" / "build.py"

spec = importlib.util.spec_from_file_location("buildmod", BUILD_PY)
buildmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(buildmod)


@pytest.fixture()
def ledger(tmp_path):
    return buildmod.StageLedger(tmp_path / "stages")


def test_ledger_mark_and_payload(ledger):
    assert not ledger.is_done("cues")
    ledger.mark_done("cues", {"sceneCount": 2})
    assert ledger.is_done("cues")
    assert ledger.payload("cues")["sceneCount"] == 2


def test_ledger_invalidate_from(ledger):
    for s in buildmod.STAGES:
        ledger.mark_done(s)
    ledger.invalidate_from("render")
    assert ledger.is_done("props")          # 앞 스테이지 유지
    for s in ("render", "mux", "qa"):       # 해당+이후 무효화
        assert not ledger.is_done(s)


def test_ledger_invalid_stage_rejected(ledger):
    with pytest.raises(ValueError, match="--from"):
        ledger.invalidate_from("renderr")


def _stub_pipeline(tmp_path, monkeypatch, calls):
    """무거운 스테이지를 기록용 스텁으로 바꾼 Pipeline."""
    monkeypatch.setattr(buildmod, "REPO_ROOT", tmp_path)
    cfg = buildmod.ProjectConfig(project_id="unit-demo")
    pipe = buildmod.Pipeline(cfg)
    for s in buildmod.STAGES:
        monkeypatch.setattr(pipe, f"stage_{s}", lambda s=s: calls.append(s) or {})
    return pipe


def test_pipeline_runs_then_skips(tmp_path, monkeypatch, caplog):
    """1회차 전 스테이지 실행 → 2회차 전부 캐시 스킵([skip] 로그)."""
    calls: list[str] = []
    pipe = _stub_pipeline(tmp_path, monkeypatch, calls)
    with caplog.at_level(logging.INFO, logger="build"):
        pipe.run()
        assert calls == buildmod.STAGES
        calls.clear()
        pipe.run()
    assert calls == []
    skips = [r.message for r in caplog.records if r.message.startswith("[skip]")]
    assert len(skips) == len(buildmod.STAGES)


def test_pipeline_from_stage_resumes(tmp_path, monkeypatch, caplog):
    """--from render: 앞 스테이지 스킵, render 이후만 재실행."""
    calls: list[str] = []
    pipe = _stub_pipeline(tmp_path, monkeypatch, calls)
    pipe.run()
    calls.clear()
    with caplog.at_level(logging.INFO, logger="build"):
        pipe.run(from_stage="render")
    assert calls == ["render", "mux", "qa"]
    skipped = [r.message.split()[1] for r in caplog.records if r.message.startswith("[skip]")]
    assert skipped == buildmod.STAGES[:buildmod.STAGES.index("render")]
