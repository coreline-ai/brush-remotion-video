#!/usr/bin/env python3
"""Prepare one narration line per fixed-duration scene for every supported TTS engine.

Qwen is intentionally synthesized as one batch so the 1.7B model is loaded once.
Each returned sentence waveform is then placed in its own fixed scene block; it is
never time-stretched to fill an entire scene.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipeline"))

from brushvid.audio import probe_duration  # noqa: E402
from brushvid.project import load_project  # noqa: E402
from brushvid.tts import format_srt_time, synthesize_narration  # noqa: E402
from brushvid.tts_contract import tts_cache_signature  # noqa: E402
from brushvid.tts_manifest import build_engine_manifest, write_manifest_atomic  # noqa: E402
from brushvid.voice_presets import tts_signature  # noqa: E402

SR = 44100
FPS = 30


def read_pcm16(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav_file:
        expected = (1, 2, SR)
        actual = (wav_file.getnchannels(), wav_file.getsampwidth(), wav_file.getframerate())
        if actual != expected:
            raise RuntimeError(f"unexpected wav format: {path}: {actual} != {expected}")
        return np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype="<i2").copy()


def write_pcm16(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SR)
        wav_file.writeframes(np.asarray(samples, dtype="<i2").tobytes())


def write_single_srt(path: Path, text: str, duration_sec: float) -> None:
    path.write_text(
        f"1\n{format_srt_time(0)} --> {format_srt_time(duration_sec)}\n{text}\n",
        encoding="utf-8",
    )


def run_atempo(source: Path, target: Path, tempo: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-af", f"atempo={tempo:.9f}", "-ar", str(SR), "-ac", "1",
            "-c:a", "pcm_s16le", str(target),
        ],
        check=True,
    )


def tts_signature_for(project_config) -> str:
    assert project_config.tts is not None
    if project_config.tts["engine"] == "supertonic":
        return tts_signature(project_config.tts_text(), project_config.tts)
    return tts_cache_signature(project_config.tts_text(), project_config.tts)


def create_qwen_segments(*, lines: list[str], tts_dir: Path, cfg: dict) -> tuple[list[dict], dict]:
    """Synthesize Qwen once, then split exact sentence waveforms by returned sample timing."""
    aggregate_wav = tts_dir / "qwen-batch.raw.wav"
    aggregate_srt = tts_dir / "qwen-batch.raw.srt"
    result = synthesize_narration(
        "\n".join(lines), aggregate_wav, aggregate_srt,
        engine=cfg["engine"], voice=cfg["voice"], speed=float(cfg["speed"]),
        pause_ms=int(cfg["pauseMs"]), lang=cfg.get("language", "ko"),
        reference=cfg.get("reference"), work_root=tts_dir / ".work",
    )
    entries = result["entries"]
    if len(entries) != len(lines):
        raise RuntimeError(f"Qwen batch entry count mismatch: {len(entries)} != {len(lines)}")
    aggregate = read_pcm16(aggregate_wav)
    scenes: list[dict] = []
    for index, (line, entry) in enumerate(zip(lines, entries, strict=True), 1):
        start = round(float(entry["start"]) * SR)
        end = round(float(entry["end"]) * SR)
        samples = aggregate[start:end]
        if samples.size == 0:
            raise RuntimeError(f"scene {index}: Qwen segment is empty")
        raw_wav = tts_dir / f"scene-{index:02d}.raw.wav"
        raw_srt = tts_dir / f"scene-{index:02d}.raw.srt"
        write_pcm16(raw_wav, samples)
        duration = len(samples) / SR
        write_single_srt(raw_srt, line, duration)
        scenes.append({"rawWav": raw_wav, "rawDuration": duration, "text": line})
    return scenes, result


def create_standard_segments(*, lines: list[str], tts_dir: Path, cfg: dict) -> tuple[list[dict], dict]:
    """Melo/Supertonic use one independent synthesis per scene."""
    scenes: list[dict] = []
    first_result: dict | None = None
    expected_identity: tuple | None = None
    for index, line in enumerate(lines, 1):
        raw_wav = tts_dir / f"scene-{index:02d}.raw.wav"
        raw_srt = tts_dir / f"scene-{index:02d}.raw.srt"
        result = synthesize_narration(
            line, raw_wav, raw_srt,
            engine=cfg["engine"], voice=cfg["voice"], speed=float(cfg["speed"]),
            pause_ms=int(cfg["pauseMs"]), lang=cfg.get("language", "ko"),
            reference=cfg.get("reference"), work_root=tts_dir / ".work",
        )
        identity = (
            result["voice"].get("engine"), result["voice"].get("model"),
            result["voice"].get("modelRevision"), result["voice"].get("speaker"),
            result["voice"].get("styleSha256"),
        )
        if expected_identity is None:
            expected_identity = identity
            first_result = result
        elif identity != expected_identity:
            raise RuntimeError(f"scene {index}: TTS voice/model identity changed")
        scenes.append({"rawWav": raw_wav, "rawDuration": probe_duration(raw_wav), "text": line})
    assert first_result is not None
    return scenes, first_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--scene-count", type=int, default=10)
    parser.add_argument("--scene-seconds", type=float, default=10.0)
    parser.add_argument("--lead-seconds", type=float, default=0.4)
    parser.add_argument("--tail-seconds", type=float, default=0.6)
    parser.add_argument("--max-tempo", type=float, default=1.15)
    args = parser.parse_args()

    project = args.project_dir.resolve()
    raw_project = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
    project_config = load_project(project / "project.yaml")
    if project_config.tts is None:
        raise SystemExit("project.yaml input.tts가 필요합니다")
    cfg = project_config.tts
    project_id = project_config.project_id
    lines = [line.strip() for line in (project / "narration.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != args.scene_count:
        raise SystemExit(f"narration lines must be {args.scene_count}, got {len(lines)}")
    if args.scene_seconds <= args.lead_seconds + args.tail_seconds:
        raise SystemExit("scene duration must exceed lead + tail")

    data_dir = REPO / "data" / project_id
    tts_dir = data_dir / "tts"
    stages = data_dir / "stages"
    tts_dir.mkdir(parents=True, exist_ok=True)
    stages.mkdir(parents=True, exist_ok=True)

    if cfg["engine"] == "qwen3-base":
        raw_scenes, voice_result = create_qwen_segments(lines=lines, tts_dir=tts_dir, cfg=cfg)
    else:
        raw_scenes, voice_result = create_standard_segments(lines=lines, tts_dir=tts_dir, cfg=cfg)
    voice_metadata = dict(voice_result["voice"])

    max_speech = args.scene_seconds - args.lead_seconds - args.tail_seconds
    scene_samples = round(args.scene_seconds * SR)
    lead_samples = round(args.lead_seconds * SR)
    blocks: list[np.ndarray] = []
    scene_meta: list[dict] = []
    for index, raw in enumerate(raw_scenes, 1):
        raw_wav = Path(raw["rawWav"])
        fitted_wav = tts_dir / f"scene-{index:02d}.fitted.wav"
        raw_duration = float(raw["rawDuration"])
        tempo = max(1.0, raw_duration / max_speech)
        if tempo > args.max_tempo:
            raise SystemExit(f"scene {index} narration too long ({raw_duration:.2f}s, tempo {tempo:.3f}); shorten text")
        run_atempo(raw_wav, fitted_wav, tempo)
        speech = read_pcm16(fitted_wav)
        limit = round(max_speech * SR)
        speech = speech[:limit]
        block = np.zeros(scene_samples, dtype="<i2")
        block[lead_samples:lead_samples + len(speech)] = speech
        blocks.append(block)
        scene_meta.append({
            "index": index, "text": raw["text"], "rawDuration": raw_duration,
            "tempo": tempo, "speechDuration": len(speech) / SR,
            "entries": [{"text": raw["text"], "start": 0.0, "end": len(speech) / SR}],
        })

    final_wav = tts_dir / "narration.wav"
    write_pcm16(final_wav, np.concatenate(blocks))
    final_duration = probe_duration(final_wav)
    expected_duration = args.scene_count * args.scene_seconds
    if abs(final_duration - expected_duration) > 0.01:
        raise RuntimeError(f"fixed timeline mismatch: {final_duration:.3f}s != {expected_duration:.3f}s")

    srt_blocks: list[str] = []
    scenes: list[dict] = []
    cue_index = 1
    for meta in scene_meta:
        scene_start = (meta["index"] - 1) * args.scene_seconds
        local_start = args.lead_seconds
        local_end = min(args.scene_seconds - args.tail_seconds, args.lead_seconds + meta["speechDuration"])
        srt_blocks.append(
            f"{cue_index}\n{format_srt_time(scene_start + local_start)} --> {format_srt_time(scene_start + local_end)}\n{meta['text']}\n"
        )
        scenes.append({"durationInFrames": round(args.scene_seconds * FPS), "cues": [{
            "text": meta["text"], "from": round(local_start * FPS), "to": round(local_end * FPS),
        }]})
        cue_index += 1
    narration_srt = tts_dir / "narration.srt"
    narration_srt.write_text("\n".join(srt_blocks), encoding="utf-8")
    (data_dir / "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")

    images = raw_project.get("background", {}).get("images") or []
    if len(images) != args.scene_count:
        raise SystemExit(f"background.images must contain {args.scene_count} paths, got {len(images)}")
    public_bg = REPO / "public" / project_id / "bg"
    public_bg.mkdir(parents=True, exist_ok=True)
    for index, rel in enumerate(images, 1):
        source = project / rel
        if not source.is_file():
            raise SystemExit(f"missing scene image: {source}")
        shutil.copy2(source, public_bg / f"scene-{index:02d}.png")

    final_result = {
        "wav": str(final_wav), "srt": str(narration_srt),
        "entries": [{"index": item["index"], "text": item["text"]} for item in scene_meta],
        "durationSec": final_duration, "voice": voice_metadata,
    }
    manifest_path = tts_dir / "voice-manifest.json"
    if cfg["engine"] == "supertonic":
        manifest = {
            "schemaVersion": 1, "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "projectId": project_id, **voice_metadata, "pauseMs": cfg["pauseMs"],
            "timing": cfg.get("timing", "tts"), "requestedTiming": cfg.get("timing", "tts"),
            "appliedTiming": "fixed-scene", "durationSec": final_duration,
            "sentenceCount": len(scene_meta), "fixedSceneTimeline": True,
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        # Engine v2 manifest schema fixes appliedTiming to the native TTS clock.
        # Fixed scene placement is recorded in the preparation report and stage marker.
        manifest = build_engine_manifest(project_id=project_id, config=cfg, result=final_result)
        write_manifest_atomic(manifest, manifest_path)

    total_frames = round(args.scene_count * args.scene_seconds * FPS)
    markers = {
        "stt": {
            "srt": str(narration_srt), "wav": str(final_wav), "durationSec": final_duration,
            "sentences": len(scene_meta), "signature": tts_signature_for(project_config),
            "voiceManifest": str(manifest_path), "voice": voice_metadata, "fixedSceneTimeline": True,
        },
        "cues": {"sceneCount": len(scenes), "totalFrames": total_frames,
                 "scenePolicy": "one-narration-line-per-fixed-scene"},
        "background": {"strategies": ["user-images-one-to-one-cover"] * len(scenes)},
    }
    for stage, payload in markers.items():
        (stages / f"{stage}.json").write_text(
            json.dumps({"stage": stage, "completedAt": "custom-fixed-scene", **payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    report = {
        "projectId": project_id, "engine": cfg["engine"], "durationSec": final_duration,
        "sceneCount": len(scenes), "totalFrames": total_frames, "voice": cfg["voice"],
        "speed": cfg["speed"], "pauseMs": cfg["pauseMs"], "fixedSceneTimeline": True,
        "voiceManifest": str(manifest_path), "scenes": scene_meta,
    }
    (data_dir / "fixed-scene-tts-preparation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "projectId": project_id, "engine": cfg["engine"], "sceneCount": len(scenes),
        "durationSec": final_duration, "voiceManifest": str(manifest_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
