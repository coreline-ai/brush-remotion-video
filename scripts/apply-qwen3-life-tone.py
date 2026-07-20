#!/usr/bin/env python3
"""Apply the user-approved Qwen3 life tone to both 60-scene project defaults."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = (
    ROOT / "projects" / "seoyun-a-day-60-qwen-fullscreen",
    ROOT / "projects" / "seoyun-a-day-60-qwen-pen-brush-fullscreen",
)
TONES = {
    "sohee-neutral": {
        "label": "Sohee 담백형", "engine": "qwen3-customvoice", "voice": "Sohee", "speed": 0.90,
        "instruction": "따뜻하고 맑은 한국어 여성 목소리로, 숨을 고르듯 차분하고 담백하게 읽어 주세요. 감정을 과장하지 말고 문장 끝은 부드럽고 자연스럽게 내려 주세요.",
    },
    "sohee-emotional": {
        "label": "Sohee 감성 내레이션형", "engine": "qwen3-customvoice", "voice": "Sohee", "speed": 0.88,
        "instruction": "따뜻하고 부드러운 한국어 여성 내레이션으로, 삶의 장면을 조용히 회상하듯 깊고 다정하게 읽어 주세요. 느린 호흡과 잔잔한 여운을 살리되 과장된 연기는 피하세요.",
    },
    "base-reference": {
        "label": "현재 Base 복제형", "engine": "qwen3-base", "voice": "seoyun-f1-reference", "speed": 0.98,
        "reference": {"audio": "inputs/voices/seoyun-f1-reference.wav", "transcript": "inputs/voices/seoyun-f1-reference.txt"},
    },
}


def selected_tts(tone: dict) -> dict:
    result = {
        "engine": tone["engine"], "voice": tone["voice"], "language": "ko", "speed": tone["speed"],
        "pauseMs": 0, "timing": "tts",
    }
    if tone["engine"] == "qwen3-customvoice":
        result["instruction"] = tone["instruction"]
    else:
        result["reference"] = tone["reference"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tone", choices=sorted(TONES), required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    tone = TONES[args.tone]
    tts = selected_tts(tone)
    if args.dry_run:
        print(yaml.safe_dump({"tone": args.tone, "tts": tts}, allow_unicode=True, sort_keys=False))
        return
    changes = []
    for project in PROJECTS:
        path = project / "project.yaml"
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        raw["input"]["tts"] = tts
        temporary = path.with_suffix(".yaml.tmp")
        temporary.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
        temporary.replace(path)
        changes.append({"project": str(project.relative_to(ROOT)), "projectYaml": str(path), "tts": tts})
    audit = {
        "kind": "qwen3-life-tone-selection", "status": "USER_SELECTED", "toneId": args.tone,
        "toneLabel": tone["label"], "selectedAt": datetime.now(timezone.utc).isoformat(),
        "changes": changes,
        "aiDisclosure": "선택된 60씬 내레이션은 AI 합성 음성으로 제작되며, build 시 voice-manifest.json에 모델·speaker·instruction·속도·AI 고지가 기록됩니다.",
    }
    output = ROOT / "output" / "qwen3-life-tone-9-demo" / "selected-tone.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"APPLIED {args.tone}: {output}")


if __name__ == "__main__":
    main()
