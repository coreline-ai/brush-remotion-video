#!/usr/bin/env python3
"""Mix approved directly-generated piano BGM beneath a fixed-scene Qwen narration."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipeline"))

from brushvid.mix import mix_voice_and_bgm, prepare_bgm, write_mix_report  # noqa: E402

DEFAULT_PROJECT_ID = "seoyun-a-day-60-qwen-fullscreen"
DURATION_SEC = 600.0
SOURCE_BGM = REPO / "output/original-audio/piano-bgm/seoyun-a-day-600s/seoyun-a-day-600s-piano-candidate-48k24.wav"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    args = parser.parse_args()
    project_id = args.project_id
    voice = REPO / "data" / project_id / "tts" / "narration.wav"
    audio_dir = REPO / "data" / project_id / "audio"
    if not voice.is_file() or not SOURCE_BGM.is_file():
        raise SystemExit("Qwen narration 또는 original piano BGM source가 없음")
    audio_dir.mkdir(parents=True, exist_ok=True)
    bgm_master, bgm_report = prepare_bgm(
        [SOURCE_BGM], audio_dir / "bgm-master.wav", duration_sec=DURATION_SEC,
        work_dir=audio_dir / "work-bgm", gain_db=3.0, fade_in_sec=1.5, fade_out_sec=3.0,
        crossfade_sec=0.0,
    )
    master, voice_report = mix_voice_and_bgm(
        voice, bgm_master, audio_dir / "final-master.wav", duration_sec=DURATION_SEC,
        ducking_enabled=True, ducking_amount_db=8.0, attack_ms=120, release_ms=600,
        work_dir=audio_dir / "work-final-bgm-mix",
    )
    report = {
        "schemaVersion": 1, "projectId": project_id, "durationSec": DURATION_SEC,
        "mode": "directly-generated-original-piano",
        "bgm": {
            **bgm_report,
            "source": str(SOURCE_BGM),
            "rights": "directly-generated original piano candidate; no external asset",
        },
        "voice": voice_report,
        "settings": {
            "duckingEnabled": True, "duckingAmountDb": 8.0,
            "attackMs": 120, "releaseMs": 600, "master": str(master),
        },
    }
    report_path = write_mix_report(audio_dir / "final-bgm-mix-report.json", report)
    print(json.dumps({"master": str(master), "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
