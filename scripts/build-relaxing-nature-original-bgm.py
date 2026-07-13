#!/usr/bin/env python3
"""Generate a 660s project-owned BGM with no third-party audio material."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from brushvid.audio import synth_ambient_bgm  # noqa: E402


PROJECT_ID = "relaxing-nature-youtube-660s-skill"
DURATION = 660.0
SEED = 660917
AUDIO_DIR = ROOT / "public/relaxing-nature-youtube-600s/audio"
RAW = AUDIO_DIR / "relaxing-nature-original-piano-strings-bells-660s-raw.wav"
MASTER = AUDIO_DIR / "relaxing-nature-original-bgm-master-660s.wav"
ORIGIN = ROOT / "data" / PROJECT_ID / "original-bgm-origin.json"
SYNTH_SOURCE = ROOT / "pipeline/brushvid/audio.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def loudness(path: Path) -> dict[str, float]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    summary = result.stderr.rsplit("Summary:", 1)[-1]
    integrated = re.search(r"I:\s*(-?[0-9.]+) LUFS", summary)
    lra = re.search(r"LRA:\s*([0-9.]+) LU", summary)
    peak = re.search(r"Peak:\s*(-?[0-9.]+) dBFS", summary)
    if not integrated or not lra or not peak:
        raise RuntimeError("failed to parse ebur128 summary")
    return {
        "integratedLufs": float(integrated.group(1)),
        "loudnessRangeLu": float(lra.group(1)),
        "truePeakDbfs": float(peak.group(1)),
    }


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ORIGIN.parent.mkdir(parents=True, exist_ok=True)

    synth_ambient_bgm(RAW, DURATION, seed=SEED)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(RAW),
            "-af",
            "loudnorm=I=-18:LRA=8:TP=-1.5",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(MASTER),
        ],
        check=True,
    )

    duration = probe_duration(MASTER)
    if abs(duration - DURATION) > 0.01:
        raise RuntimeError(f"unexpected BGM duration: {duration}")
    metrics = loudness(MASTER)
    if metrics["integratedLufs"] < -19.5 or metrics["integratedLufs"] > -16.5:
        raise RuntimeError(f"BGM loudness outside target: {metrics}")
    if metrics["truePeakDbfs"] > -1.0:
        raise RuntimeError(f"BGM true peak too high: {metrics}")

    manifest = {
        "schemaVersion": 1,
        "projectId": PROJECT_ID,
        "title": "Relaxing Nature Original Piano, Soft Strings and Light Bells",
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "creator": "brush_remotion_video procedural synthesis",
        "rightsHolder": "project owner",
        "source": "procedural-local-synthesis",
        "license": "project-owned original audio",
        "commercialUseAllowed": True,
        "youtubeUseAllowed": True,
        "youtubeMonetizationAllowed": True,
        "externalSamplesUsed": False,
        "thirdPartyLoopsUsed": False,
        "thirdPartyMusicUsed": False,
        "contentIdStatus": "not-submitted-by-project",
        "durationSeconds": duration,
        "sampleRate": 48000,
        "seed": SEED,
        "composition": {
            "progression": "Dadd9 - Bm7 - G6 - A",
            "instruments": ["procedural felt-piano synthesis", "synthesized string pad", "synthesized bell"],
            "rendering": "NumPy oscillators, ADSR envelopes, deterministic echo and low-pass filtering",
            "targetLoudness": "-18 LUFS",
            "truePeakCeiling": "-1.5 dBTP",
        },
        "sourceCode": str(SYNTH_SOURCE.relative_to(ROOT)),
        "sourceCodeSha256": sha256_file(SYNTH_SOURCE),
        "rawAudio": str(RAW.relative_to(ROOT)),
        "rawAudioSha256": sha256_file(RAW),
        "masterAudio": str(MASTER.relative_to(ROOT)),
        "masterAudioSha256": sha256_file(MASTER),
        "measured": metrics,
        "rightsNote": (
            "The audio was rendered locally from project source code without external samples, "
            "royalty-free catalog tracks, Creative Commons material, or third-party loops."
        ),
    }
    ORIGIN.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[BGM] {MASTER}")
    print(f"[ORIGIN] {ORIGIN}")
    print(f"[METRICS] {json.dumps(metrics)}")


if __name__ == "__main__":
    main()
