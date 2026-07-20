#!/usr/bin/env python3
"""Render one Qwen3 life-tone demo with its native model; no fallback path."""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from brushvid.tts_engines.qwen import QwenAdapter, QwenCustomVoiceAdapter  # noqa: E402


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(np.asarray(samples, dtype=np.float32).reshape(-1), -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: render-qwen3-life-tone.py TONE_ID JOBS_JSON OUT_DIR SPEED")
    tone_id, jobs_path, out_path, speed_raw = sys.argv[1:]
    payload = json.loads(Path(jobs_path).read_text(encoding="utf-8"))
    tone = next((item for item in payload["tones"] if item["id"] == tone_id), None)
    if tone is None:
        raise SystemExit(f"unknown tone: {tone_id}")
    items = payload["items"]
    out_dir = Path(out_path); out_dir.mkdir(parents=True, exist_ok=True)
    speed = float(speed_raw)
    if tone["engine"] == "qwen3-customvoice":
        adapter = QwenCustomVoiceAdapter(
            speaker=tone["speaker"], instruction=tone["instruction"], work_root=out_dir / ".qwen-work",
        )
        voice = tone["speaker"]
    elif tone["engine"] == "qwen3-base":
        reference_dir = ROOT / "projects" / "seoyun-a-day-60-qwen-fullscreen" / "inputs" / "voices"
        reference = {
            "audio": reference_dir / "seoyun-f1-reference.wav",
            "transcript": reference_dir / "seoyun-f1-reference.txt",
        }
        if not all(path.is_file() and not path.is_symlink() for path in reference.values()):
            raise RuntimeError("현재 Base 복제형 reference pair가 없거나 유효하지 않음")
        adapter = QwenAdapter(reference=reference, work_root=out_dir / ".qwen-work")
        voice = "seoyun-f1-reference"
    else:
        raise SystemExit(f"unsupported engine: {tone['engine']}")
    try:
        results = adapter.synthesize_batch(
            [item["text"] for item in items], voice=voice, language="ko", speed=speed,
        )
    finally:
        adapter.close()
    if len(results) != len(items):
        raise RuntimeError("native Qwen output count mismatch")
    entries = []
    for item, result in zip(items, results, strict=True):
        wav = out_dir / f"{tone_id}-{item['id']}.wav"
        write_wav(wav, result.samples, result.sample_rate)
        entries.append({"id": item["id"], "rawWav": wav.name, "nativeSampleRate": result.sample_rate})
    metadata = dict(results[0].metadata)
    metadata.update({"speed": speed, "speedAppliedBy": "ffmpeg-atempo"})
    output = {
        "toneId": tone_id,
        "label": tone["name"],
        "engine": tone["engine"],
        "voice": voice,
        "metadata": metadata,
        "qualityGate": "PASS: official pinned Qwen model only; no fallback; instruction/reference contract preserved.",
        "entries": entries,
    }
    (out_dir / f"{tone_id}-result.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tone": tone_id, "status": "PASS", "entries": len(entries)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
