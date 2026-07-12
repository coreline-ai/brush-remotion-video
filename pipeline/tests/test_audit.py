"""audit.py 테스트 — 임계 로직(순수) + 합성 클립(ffmpeg) 검출 + 독립성 가드."""
import subprocess
import wave
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from brushvid import audit as A

FPS = 30


# ── 독립성 (1급 요구) ──

def test_audit_standalone_imports():
    """audit.py 는 brushvid 타 모듈을 import 하지 않는다."""
    src = Path(A.__file__).read_text(encoding="utf-8")
    assert "from ." not in src
    assert "from brushvid" not in src
    assert "import brushvid" not in src


# ── 임계 로직 (순수 함수) ──

def test_classify_boundary_thresholds():
    assert A.classify_boundary(12.0) == "FAIL"   # city 수정 전 실측 12~23%
    assert A.classify_boundary(7.0) == "WARN"
    assert A.classify_boundary(5.3) is None      # city 수정 후 실측 상한


def test_classify_spike_thresholds():
    assert A.classify_spike(2.97, 2.97, 0.7) == "FAIL"   # develop 스파이크 실측
    assert A.classify_spike(1.8, 1.8, 0.5) == "WARN"
    assert A.classify_spike(0.94, 0.94, 0.7) is None     # 수정 후 정상 페이드 수준
    assert A.classify_spike(3.0, 3.0, 2.0) is None       # 배수 미달(주변도 높음)


def test_judge_candidate_three_way():
    """transient=스파이크 / 지속+구도유지=워시 / 지속+구도변화=하드컷."""
    kind, sev = A.judge_candidate(3.0, 3.0, 0.5, transient=True, corr=1.0, near_scene_end=False)
    assert (kind, sev) == ("spike", "FAIL")
    kind, sev = A.judge_candidate(8.0, 8.0, 0.5, transient=False, corr=0.98, near_scene_end=True)
    assert (kind, sev) == ("outro-wash", "INFO")     # 씬 끝 워시 온셋은 연출
    kind, sev = A.judge_candidate(8.0, 8.0, 0.5, transient=False, corr=0.98, near_scene_end=False)
    assert (kind, sev) == ("wash-jump", "WARN")
    kind, sev = A.judge_candidate(12.0, 12.0, 0.5, transient=False, corr=0.2, near_scene_end=True)
    assert (kind, sev) == ("hardcut", "FAIL")


def test_pearson_corr():
    rng = np.random.default_rng(1)
    a = rng.integers(0, 255, 1000).astype(np.int16)
    washed = (a * 0.2 + 200).astype(np.int16)   # 같은 구도의 워시
    assert A.pearson_corr(a, washed) > 0.99
    other = rng.integers(0, 255, 1000).astype(np.int16)
    assert A.pearson_corr(a, other) < 0.5
    flat = np.full(1000, 128, dtype=np.int16)
    assert A.pearson_corr(flat, flat) == 0.0     # 분산 0 → 구조 비교 불능


def test_spike_candidates_cluster_and_exclude():
    d = np.full(200, 0.3)
    d[100], d[102] = 5.0, 6.0   # 근접 클러스터 → 피크(102)만
    d[150] = 9.0                # 경계 제외 대상
    roll = np.full(200, 0.3)
    peaks = A.spike_candidates(d, roll, exclude={149, 150, 151})
    assert peaks == [102]


def test_find_freeze_runs_and_severity():
    d = np.full(400, 1.0)
    d[50:145] = 0.0    # 95프레임(3.2s) 정지
    d[200:260] = 0.0   # 60프레임(2s) — 미달
    runs = A.find_freeze_runs(d, FPS)
    assert runs == [(50, 144)]
    # 씬 끝(경계 160 직전) → info / 경계에서 먼 정지 → WARN
    assert A.freeze_severity((50, 144), [160], 400, FPS) == "INFO"
    assert A.freeze_severity((50, 144), [350], 400, FPS) == "WARN"
    assert A.freeze_severity((50, 144), [], 165, FPS) == "INFO"  # 영상 끝 감상


def test_estimate_boundaries_white_runs():
    lums = np.full(300, 180.0)
    lums[95:101] = 250.0   # 6프레임 순백 유지 → 경계 101
    lums[200] = 250.0      # 1프레임 화이트 플래시 → 경계 아님
    assert A.estimate_boundaries(lums) == [101]


def test_check_spec_rules():
    base = {"width": 1920, "height": 1080, "fps": 30.0, "vcodec": "h264",
            "acodec": "aac", "hasAudio": True, "duration": 600.0}
    assert A.check_spec(base) == []
    shorts_long = {**base, "width": 1080, "height": 1920, "duration": 181.0}
    assert any(i.severity == "FAIL" for i in A.check_spec(shorts_long))  # 쇼츠 180s 초과
    assert any(i.severity == "FAIL" and i.kind == "audio-missing"
               for i in A.check_spec({**base, "hasAudio": False, "acodec": None}))
    warns = A.check_spec({**base, "width": 320, "height": 180, "fps": 25.0, "vcodec": "vp9"})
    assert {i.severity for i in warns} == {"WARN"} and len(warns) == 3


def test_audio_issue_rules():
    dur = 30.0
    # 무음 2s 초과 → WARN
    parsed = {"silences": [(5.0, 8.5)], "meanVolume": -25.0, "maxVolume": -3.0}
    issues = A.audio_issues(parsed, dur)
    assert [i.severity for i in issues] == ["WARN"] and issues[0].kind == "audio-silence"
    # 전체 무음 → FAIL 하나로 종결
    parsed = {"silences": [(0.0, 30.0)], "meanVolume": -80.0, "maxVolume": -60.0}
    issues = A.audio_issues(parsed, dur)
    assert [(i.severity, i.kind) for i in issues] == [("FAIL", "audio-silence")]
    # 클리핑 > -0.5dB → WARN
    parsed = {"silences": [], "meanVolume": -12.0, "maxVolume": -0.1}
    issues = A.audio_issues(parsed, dur)
    assert [(i.severity, i.kind) for i in issues] == [("WARN", "audio-clipping")]


def test_parse_audio_stderr():
    text = ("[silencedetect @ 0x0] silence_start: 3.2\n"
            "[silencedetect @ 0x0] silence_end: 6.4 | silence_duration: 3.2\n"
            "[silencedetect @ 0x0] silence_start: 25.0\n"   # EOF 까지 무음 (end 없음)
            "[Parsed_volumedetect @ 0x0] mean_volume: -21.3 dB\n"
            "[Parsed_volumedetect @ 0x0] max_volume: -0.2 dB\n")
    p = A.parse_audio_stderr(text, 30.0)
    assert p["silences"] == [(3.2, 6.4), (25.0, 30.0)]
    assert p["meanVolume"] == -21.3 and p["maxVolume"] == -0.2


# ── 합성 클립 통합 (ffmpeg) ──

SIZE = "320x180"


def _lavfi_concat(tmp_path, name, srcs):
    """lavfi 소스 여러 개를 concat 한 무음 mp4 생성."""
    out = tmp_path / name
    args = ["ffmpeg", "-v", "error", "-y"]
    for s in srcs:
        args += ["-f", "lavfi", "-i", s]
    args += ["-filter_complex", "".join(f"[{i}]" for i in range(len(srcs))) +
             f"concat=n={len(srcs)}:v=1[v]", "-map", "[v]",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(args, check=True, capture_output=True)
    return out


def _kinds(result, severity=None):
    return {i["kind"] for i in result["issues"]
            if severity is None or i["severity"] == severity}


def test_synthetic_hardcut_detected(tmp_path):
    """중간에 하드컷이 있는 합성 클립 → props 없이 hardcut FAIL."""
    clip = _lavfi_concat(tmp_path, "cut.mp4", [
        f"color=c=0x909090:s={SIZE}:d=2:r={FPS}",
        f"color=c=0x202020:s={SIZE}:d=2:r={FPS}"])
    r = A.run_audit(clip, out_dir=None)
    assert r["verdict"] == "FAIL"
    fails = [i for i in r["issues"] if i["severity"] == "FAIL" and i["kind"] == "hardcut"]
    assert fails and abs(fails[0]["frame"] - 60) <= 2


def test_synthetic_spike_detected(tmp_path):
    """1프레임 백색 플래시(번쩍 후 복귀) → spike FAIL (transient 분류)."""
    frames_dir = tmp_path / "fr"
    frames_dir.mkdir()
    for i in range(75):
        lum = 250 if i == 40 else 120
        Image.new("RGB", (320, 180), (lum, lum, lum)).save(frames_dir / f"{i:04d}.png")
    clip = tmp_path / "spike.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS),
                    "-i", str(frames_dir / "%04d.png"), "-c:v", "libx264",
                    "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(clip)],
                   check=True, capture_output=True)
    r = A.run_audit(clip, out_dir=None)
    spikes = [i for i in r["issues"] if i["kind"] == "spike" and i["severity"] == "FAIL"]
    assert spikes and abs(spikes[0]["frame"] - 40) <= 2
    assert spikes[0]["metrics"]["transient"] is True


def test_synthetic_freeze_warn_and_report(tmp_path):
    """4.5s 정지 후 2.5s 모션 → 씬 끝이 아닌 정지 WARN + 리포트 파일 산출."""
    clip = _lavfi_concat(tmp_path, "freeze.mp4", [
        f"color=c=0x707070:s={SIZE}:d=4.5:r={FPS}",
        f"testsrc=size={SIZE}:d=2.5:r={FPS}"])
    out = tmp_path / "report"
    r = A.run_audit(clip, out_dir=out)
    fz = [i for i in r["issues"] if i["kind"] == "freeze"]
    assert fz and fz[0]["severity"] == "WARN"
    assert (out / "audit-report.md").is_file() and (out / "audit-report.json").is_file()
    assert "FIELD-LOG 초안" in (out / "audit-report.md").read_text(encoding="utf-8")


def _write_wav(path, chunks, sr=44100):
    """chunks: [(초, 진폭)] 사인/무음 연결 wav."""
    data = np.concatenate([
        (amp * np.sin(2 * np.pi * 440 * np.arange(int(sr * sec)) / sr)) for sec, amp in chunks])
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def test_synthetic_audio_silence_and_clipping(tmp_path):
    """중간 3s 무음 + 클리핑 사인(진폭 1.2) → audio-silence WARN + audio-clipping WARN."""
    wav = tmp_path / "a.wav"
    _write_wav(wav, [(2, 1.2), (3, 0.0), (2, 1.2)])
    clip = tmp_path / "audio.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"color=c=0x808080:s={SIZE}:d=7:r={FPS}",
                    "-i", str(wav), "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)],
                   check=True, capture_output=True)
    r = A.run_audit(clip, out_dir=None)
    kinds = _kinds(r, "WARN")
    assert "audio-silence" in kinds and "audio-clipping" in kinds


def test_synthetic_clean_clip_passes(tmp_path):
    """서서히 변하는 모션 + 정상 오디오 → FAIL 0 (verdict 는 spec WARN 무관 PASS)."""
    wav = tmp_path / "a.wav"
    _write_wav(wav, [(4, 0.4)])
    clip = tmp_path / "clean.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc=size={SIZE}:d=4:r={FPS}",
                    "-i", str(wav), "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)],
                   check=True, capture_output=True)
    r = A.run_audit(clip, out_dir=None)
    assert r["verdict"] == "PASS"
    assert r["summary"]["FAIL"] == 0
