#!/usr/bin/env python3
"""Build the 48-scene, 10-minute cinematic cut of Earth Quiet Day."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/earth-quiet-day-60/props-imported.json"
OUT_DIR = ROOT / "data/earth-quiet-day-48-cinematic"
OUT_PROPS = OUT_DIR / "props-final.json"

# Eight scenes per chapter. Two visually redundant water/forest/landscape beats
# are removed from every ten-scene chapter while the six chapter openers remain.
SELECTED = [
    1, 2, 3, 4, 5, 8, 9, 10,
    11, 12, 13, 14, 16, 18, 19, 20,
    21, 23, 24, 25, 26, 28, 29, 30,
    31, 32, 34, 35, 36, 37, 39, 40,
    41, 42, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 57, 58, 60,
]

CHAPTER_OPENERS = {1, 11, 21, 31, 41, 51}
KEY_SCENES = {
    3, 4, 10,
    13, 18, 19,
    23, 25, 30,
    35, 36, 40,
    42, 45, 50,
    52, 53, 60,
}

OMITTED = [n for n in range(1, 61) if n not in SELECTED]


def scene_number(scene_id: str) -> int:
    return int(scene_id.rsplit("-", 1)[-1])


def timing_for(number: int) -> tuple[str, int]:
    if number in CHAPTER_OPENERS:
        return "chapter", 420
    if number in KEY_SCENES:
        return "key", 390
    return "standard", 330


def cue(text: str, start: int, end: int) -> dict[str, object]:
    return {"text": text, "from": start, "to": end}


def build() -> dict[str, object]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_number = {scene_number(scene["id"]): scene for scene in source["scenes"]}
    scenes: list[dict[str, object]] = []

    for position, number in enumerate(SELECTED):
        scene = copy.deepcopy(by_number[number])
        role, duration = timing_for(number)

        # The opening adds a 17-frame preview/fade/draw-delay window. The final
        # dawn carries the twelve-second title return and paper fade. The 163
        # frames saved from the former six-second intro are distributed across
        # the other scenes so the complete cut remains exactly ten minutes.
        if number == 1:
            duration += 17
        elif position <= 22:
            duration += 4
        else:
            duration += 3
        if number == 60:
            duration += 360

        scene["durationInFrames"] = duration
        scene["developFrames"] = 34
        # 단일 이미지 마스크에서 누락 영역만 채운 뒤, 전체 이미지가 완성된
        # 다음에 밝기 변화 없이 색감만 천천히 깊어진다.
        scene["completionMode"] = "integrated-develop"
        scene["colorSettleFrames"] = 48
        scene["outroFadeFrames"] = 36
        scene["outroWashOpacity"] = 1.0
        scene["outroBlur"] = 1

        dynamics = scene.setdefault("brushDynamics", {})
        dynamics["drawSpeedScale"] = {
            "chapter": 0.58,
            "key": 0.62,
            "standard": 0.55,
        }[role]
        dynamics["touchScale"] = 1.12 + (position % 4) * 0.035
        dynamics["touchJitter"] = 0.06 + (position % 3) * 0.025
        dynamics["pathJitter"] = [4, 7, 10, 6][position % 4]
        dynamics["randomReverse"] = role != "chapter" and position % 3 == 1
        dynamics["randomizeOrder"] = False

        effects = scene.get("naturalEffects")
        if effects:
            effects["parallaxScale"] = 1.018 if role == "key" else 1.012
            effects["opacity"] = min(0.04, float(effects.get("opacity", 0.032)))

        original_text = str(scene.get("cues", [{}])[0].get("text", ""))
        if number == 1:
            scene["prewashOpacity"] = 0.32
            scene["prewashFrames"] = 17
            scene["prewashHoldFrames"] = 0
            scene["prewashFadeOutFrames"] = 9
            scene["prewashBlur"] = 12
            scene["cues"] = [cue(original_text, 190, duration - 36)]
            if scene.get("topTitle"):
                scene["topTitle"]["enterAt"] = 17
        elif number == 60:
            scene["prewashOpacity"] = 0
            scene["prewashFrames"] = 0
            scene["prewashHoldFrames"] = 0
            scene["prewashFadeOutFrames"] = 0
            scene["cues"] = [
                cue(original_text, 200, 495),
                cue("하루가 끝난 자리에서, 또 하나의 빛이 시작됩니다", 510, 630),
            ]
            scene["topTitle"] = {
                "kicker": "EARTH · QUIET DAY",
                "lines": ["지구의", "조용한 하루"],
                "x": 520,
                "y": 300,
                "width": 880,
                "align": "center",
                "enterAt": 525,
                "accent": "#C09A58",
                "firstWordColor": "#365F70",
                "fontSize": 72,
                "kickerFontSize": 19,
                "wash": True,
            }
            scene["outroFadeFrames"] = 120
            scene["outroWashOpacity"] = 1.0
            scene["outroBlur"] = 2
        else:
            # Every preceding scene now resolves to the same paper color at
            # 100% opacity. Start the next scene on clean paper so the visual
            # boundary is a deliberate breathing beat instead of a hard cut.
            scene["prewashOpacity"] = 0
            scene["prewashFrames"] = 0
            scene["prewashHoldFrames"] = 0
            scene["prewashFadeOutFrames"] = 0
            scene["prewashBlur"] = 0
            if role == "chapter":
                scene["cues"] = [cue(original_text, 200, duration - 18)]
                if scene.get("topTitle"):
                    scene["topTitle"]["enterAt"] = 24
            elif role == "key":
                scene["cues"] = [cue(original_text, 195, duration - 18)]
            else:
                scene["cues"] = [cue(original_text, 180, duration - 18)]

        scenes.append(scene)

    props = copy.deepcopy(source)
    props["projectId"] = "earth-quiet-day-48-cinematic"
    props["title"] = "지구의 조용한 하루 · 48 Scene Cinematic Cut"
    # User-selected Chopin recording, trimmed to remove its 0.24s leading
    # silence, extended to 600s with a six-second musical crossfade, normalized,
    # and faded only at the final six seconds.
    props["audio"] = "earth-quiet-day-48-cinematic/audio/funeral-march-chopin-600s.wav"
    props["scenes"] = scenes

    total = sum(int(scene["durationInFrames"]) for scene in scenes)
    if len(scenes) != 48 or total != 18_000:
        raise RuntimeError(f"invalid timeline: scenes={len(scenes)} frames={total}")
    return props


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    props = build()
    OUT_PROPS.write_text(json.dumps(props, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    editorial = {
        "projectId": props["projectId"],
        "sourceProject": "earth-quiet-day-60",
        "selectedSceneNumbers": SELECTED,
        "omittedSceneNumbers": OMITTED,
        "chapterOpeners": sorted(CHAPTER_OPENERS),
        "keyScenes": sorted(KEY_SCENES),
        "sceneCount": len(props["scenes"]),
        "durationFrames": sum(scene["durationInFrames"] for scene in props["scenes"]),
        "durationSeconds": 600,
    }
    (OUT_DIR / "editorial-manifest.json").write_text(
        json.dumps(editorial, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_PROPS}")
    print(f"scenes={editorial['sceneCount']} frames={editorial['durationFrames']}")


if __name__ == "__main__":
    main()
