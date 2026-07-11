"""render.py / qa.py 유닛 테스트 — remotion 없이 ffmpeg/PIL 경로만 검증."""
import json
import subprocess

import pytest
from PIL import Image

from brushvid.qa import contact_sheet, write_manifest
from brushvid.render import concat, mux_audio, probe_duration


def _mk_clip(path, seconds=0.2, color="red"):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30:d={seconds}",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True)


@pytest.fixture()
def clips(tmp_path):
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    _mk_clip(a, color="red")
    _mk_clip(b, color="blue")
    return a, b


def test_concat_and_probe(tmp_path, clips):
    """세그먼트 concat 결과 길이 = 합산."""
    out = concat(list(clips), tmp_path / "joined.mp4")
    assert out.is_file()
    assert probe_duration(out) == pytest.approx(0.4, abs=0.1)


def test_mux_audio(tmp_path, clips):
    """오디오 mux 후 오디오 스트림 1개 존재."""
    audio = tmp_path / "tone.m4a"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.4",
         "-c:a", "aac", str(audio)],
        check=True, capture_output=True)
    out = mux_audio(clips[0], audio, tmp_path / "muxed.mp4")
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True, check=True)
    assert res.stdout.strip() == "audio"


def test_manifest_and_contact_sheet(tmp_path):
    """capture-manifest.json 작성 → 콘택트시트 생성."""
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir()
    entries = []
    for f, color in [(0, (200, 60, 60)), (30, (60, 60, 200)), (59, (60, 200, 60))]:
        name = f"frame-{f:05d}.png"
        Image.new("RGB", (320, 180), color).save(qa_dir / name)
        entries.append({"frame": f, "file": name, "label": f"check-{f}"})
    manifest = write_manifest(entries, qa_dir, project_id="demo", props="data/demo/props.json")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["projectId"] == "demo"
    assert len(data["captures"]) == 3

    sheet = contact_sheet(qa_dir, cols=2)
    assert sheet.is_file()
    assert Image.open(sheet).width > 320
