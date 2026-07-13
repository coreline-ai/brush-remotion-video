#!/usr/bin/env python3
"""Generate scene-fixed Supertonic narration and stage markers for storybook projects."""
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
from brushvid.voice_presets import tts_signature  # noqa: E402


SR = 44100
FPS = 30


def read_pcm16(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, SR):
            raise RuntimeError(f"unexpected wav format: {path}")
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").copy()


def write_pcm16(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(audio.astype("<i2", copy=False).tobytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--scene-count", type=int, default=10)
    parser.add_argument("--scene-seconds", type=float, default=10.0)
    parser.add_argument("--lead-seconds", type=float, default=0.4)
    parser.add_argument("--tail-seconds", type=float, default=0.6)
    parser.add_argument("--voice")
    parser.add_argument("--speed", type=float)
    parser.add_argument("--pause-ms", type=int, default=350)
    parser.add_argument("--max-tempo", type=float, default=1.15)
    args = parser.parse_args()

    project = args.project_dir.resolve()
    project_yaml = project / "project.yaml"
    config = yaml.safe_load(project_yaml.read_text(encoding="utf-8"))
    project_config = load_project(project_yaml)
    if project_config.tts is None:
        raise SystemExit("project.yaml input.tts가 필요합니다")
    voice = args.voice or project_config.tts["voice"]
    speed = args.speed if args.speed is not None else project_config.tts.get("speed", 1.05)
    if voice != project_config.tts["voice"] or speed != project_config.tts.get("speed", 1.05):
        raise SystemExit("--voice/--speed는 project.yaml input.tts와 같아야 재현 가능한 stage cache를 만들 수 있습니다")
    project_id = config.get("projectId") or project.name
    data = REPO / "data" / project_id
    tts = data / "tts"
    stages = data / "stages"
    tts.mkdir(parents=True, exist_ok=True)
    stages.mkdir(parents=True, exist_ok=True)

    lines = [
        line.strip()
        for line in (project / "narration.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(lines) != args.scene_count:
        raise SystemExit(f"narration lines must be {args.scene_count}, got {len(lines)}")

    max_speech = args.scene_seconds - args.lead_seconds - args.tail_seconds
    if max_speech <= 0:
        raise SystemExit("scene duration must exceed lead + tail")
    scene_samples = round(args.scene_seconds * SR)
    lead_samples = round(args.lead_seconds * SR)
    blocks: list[np.ndarray] = []
    scene_meta: list[dict] = []
    voice_metadata: dict | None = None

    for index, text in enumerate(lines, 1):
        raw_wav = tts / f"scene-{index:02d}.raw.wav"
        raw_srt = tts / f"scene-{index:02d}.raw.srt"
        fitted_wav = tts / f"scene-{index:02d}.fitted.wav"
        result = synthesize_narration(
            text,
            raw_wav,
            raw_srt,
            engine="supertonic",
            voice=voice,
            speed=speed,
            pause_ms=args.pause_ms,
        )
        if voice_metadata is None:
            voice_metadata = result["voice"]
        elif result["voice"]["styleSha256"] != voice_metadata["styleSha256"]:
            raise SystemExit("scene별 Supertonic style hash가 달라 결정성을 보장할 수 없습니다")
        raw_duration = probe_duration(raw_wav)
        tempo = max(1.0, raw_duration / max_speech)
        if tempo > args.max_tempo:
            raise SystemExit(
                f"scene {index} narration too long ({raw_duration:.2f}s, tempo {tempo:.3f}); shorten text"
            )
        subprocess.run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(raw_wav), "-af", f"atempo={tempo:.9f}",
                "-ar", str(SR), "-ac", "1", str(fitted_wav),
            ],
            check=True,
        )
        speech = read_pcm16(fitted_wav)
        limit = round(max_speech * SR)
        if len(speech) > limit:
            speech = speech[:limit]
        block = np.zeros(scene_samples, dtype="<i2")
        block[lead_samples : lead_samples + len(speech)] = speech
        blocks.append(block)
        scene_meta.append(
            {
                "index": index,
                "text": text,
                "rawDuration": raw_duration,
                "tempo": tempo,
                "speechDuration": len(speech) / SR,
                "entries": [
                    {
                        "text": entry["text"],
                        "start": entry["start"] / tempo,
                        "end": entry["end"] / tempo,
                    }
                    for entry in result["entries"]
                ],
            }
        )

    final_wav = tts / "narration.wav"
    write_pcm16(final_wav, np.concatenate(blocks))
    final_duration = probe_duration(final_wav)

    srt_blocks: list[str] = []
    scenes: list[dict] = []
    cue_index = 1
    for meta in scene_meta:
        scene_start = (meta["index"] - 1) * args.scene_seconds
        cues = []
        for entry in meta["entries"]:
            local_start = args.lead_seconds + entry["start"]
            local_end = min(args.scene_seconds - args.tail_seconds, args.lead_seconds + entry["end"])
            srt_blocks.append(
                f"{cue_index}\n"
                f"{format_srt_time(scene_start + local_start)} --> "
                f"{format_srt_time(scene_start + local_end)}\n"
                f"{entry['text']}\n"
            )
            cues.append(
                {
                    "text": entry["text"],
                    "from": round(local_start * FPS),
                    "to": round(local_end * FPS),
                }
            )
            cue_index += 1
        scenes.append({"durationInFrames": round(args.scene_seconds * FPS), "cues": cues})

    (tts / "narration.srt").write_text("\n".join(srt_blocks), encoding="utf-8")
    (data / "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")

    images = config.get("background", {}).get("images") or []
    if len(images) != args.scene_count:
        raise SystemExit(f"background.images must contain {args.scene_count} paths, got {len(images)}")
    public_bg = REPO / "public" / project_id / "bg"
    public_bg.mkdir(parents=True, exist_ok=True)
    for index, rel in enumerate(images, 1):
        source = project / rel
        if not source.exists():
            raise SystemExit(f"missing scene image: {source}")
        shutil.copy2(source, public_bg / f"scene-{index:02d}.png")

    total_frames = round(args.scene_count * args.scene_seconds * FPS)
    assert voice_metadata is not None
    voice_manifest = {
        "schemaVersion": 1,
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "projectId": project_id,
        **voice_metadata,
        "pauseMs": args.pause_ms,
        "timing": project_config.tts.get("timing", "tts"),
        "durationSec": final_duration,
        "sentenceCount": sum(len(meta["entries"]) for meta in scene_meta),
        "fixedSceneTimeline": True,
    }
    voice_manifest_path = tts / "voice-manifest.json"
    voice_manifest_path.write_text(
        json.dumps(voice_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    marker_payloads = {
        "stt": {
            "srt": str(tts / "narration.srt"), "wav": str(final_wav),
            "durationSec": final_duration,
            "sentences": sum(len(meta["entries"]) for meta in scene_meta),
            "signature": tts_signature(project_config.tts_text(), project_config.tts),
            "voiceManifest": str(voice_manifest_path),
            "voice": voice_metadata,
            "fixedSceneTimeline": True,
        },
        "cues": {
            "sceneCount": args.scene_count, "totalFrames": total_frames,
            "scenePolicy": "sentence-cues-in-fixed-scenes",
        },
        "background": {"strategies": ["user-images-one-to-one"] * args.scene_count},
    }
    for stage, payload in marker_payloads.items():
        (stages / f"{stage}.json").write_text(
            json.dumps({"stage": stage, "completedAt": "custom", **payload}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    report = {
        "projectId": project_id,
        "durationSec": final_duration,
        "sceneCount": args.scene_count,
        "totalFrames": total_frames,
        "voice": voice,
        "speed": speed,
        "voiceManifest": str(voice_manifest_path),
        "scenes": scene_meta,
    }
    (data / "storybook-preparation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
