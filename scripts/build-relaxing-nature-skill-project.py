#!/usr/bin/env python3
"""Build current-repo render props for the 660s relaxing nature master.

This keeps the imported Korean titles, cues, and natural-effect choices while
adapting the project to the native BrushLandscape schema.  The full render is
split into six deterministic chapters so a long Remotion job can be resumed.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "relaxing-nature-youtube-660s-skill"
SOURCE = ROOT / "data/relaxing-nature-youtube-600s/props-imported.json"
OUT_DIR = ROOT / "data" / PROJECT_ID
FINAL_AUDIO = "relaxing-nature-youtube-600s/audio/relaxing-nature-original-bgm-master-660s.wav"
YOUTUBE_SAFE_AUDIO = FINAL_AUDIO
PILOT_SCENES = {1, 4, 30, 48, 60}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def adapt_scene(scene: dict, index: int) -> dict:
    adapted = deepcopy(scene)
    adapted["durationInFrames"] = 330
    adapted["routes"] = (
        f"relaxing-nature-youtube-600s/routes-soft-transition/scene-{index:02d}.routes.json"
    )
    adapted["faint"] = 0.72
    adapted["edgeFeather"] = 12
    adapted["linearDraw"] = True
    adapted["developFrames"] = 20

    # Only the opening scene needs a prewash.  Later scenes already enter from
    # the preceding paper dissolve, so another prewash would delay the drawing.
    if index == 1:
        adapted["prewashOpacity"] = 0.68
        adapted["prewashFrames"] = 24
        adapted["prewashHoldFrames"] = 8
        adapted["prewashBlur"] = 10
    else:
        adapted["prewashOpacity"] = 0.0
        adapted["prewashFrames"] = 0

    # The imported 45f dissolve left too much white hold at each boundary.
    # Eighteen frames keeps the transition soft without stopping the picture.
    adapted["outroFadeFrames"] = 90 if index == 60 else 18
    adapted["outroWashOpacity"] = 1.0 if index == 60 else 0.86
    adapted["outroBlur"] = 3.0 if index == 60 else 1.2

    effect = adapted.get("naturalEffects")
    if effect:
        # Subtle motion during the completed-painting hold prevents a static
        # freeze while staying below the threshold of visible camera movement.
        effect["parallaxScale"] = round(1.006 + (index % 5) * 0.0012, 4)
        effect["opacity"] = min(float(effect.get("opacity", 0.045)), 0.052)

    return adapted


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes = [adapt_scene(scene, i) for i, scene in enumerate(source["scenes"], start=1)]
    if len(scenes) != 60:
        raise SystemExit(f"expected 60 scenes, got {len(scenes)}")

    master = {
        "schemaVersion": 1,
        "projectId": PROJECT_ID,
        "title": "편안한 자연 · 11분 수채화 힐링",
        "format": "youtube",
        "audio": FINAL_AUDIO,
        "paper": source.get("paper", "#fbfaf6"),
        "brush": {
            **source["brush"],
            "kind": "image",
            "visible": True,
            "opacity": 0.82,
        },
        "scenes": scenes,
    }
    video_only = {**master, "audio": None}
    youtube_safe = {
        **master,
        "projectId": f"{PROJECT_ID}-youtube-safe",
        "title": "편안한 자연 · 11분 수채화 힐링 · 자연 앰비언스",
        "audio": YOUTUBE_SAFE_AUDIO,
    }
    pilot = {**video_only, "projectId": f"{PROJECT_ID}-pilot"}
    pilot["scenes"] = [scene for i, scene in enumerate(scenes, start=1) if i in PILOT_SCENES]

    write_json(OUT_DIR / "props-final.json", master)
    write_json(OUT_DIR / "props-final-youtube-safe.json", youtube_safe)
    write_json(OUT_DIR / "props-video-only.json", video_only)
    write_json(OUT_DIR / "props-pilot.json", pilot)

    chapter_paths = []
    for chapter_index in range(6):
        start = chapter_index * 10
        chapter = {
            **video_only,
            "projectId": f"{PROJECT_ID}-chapter-{chapter_index + 1:02d}",
            "scenes": scenes[start : start + 10],
        }
        path = OUT_DIR / "chapters" / f"chapter-{chapter_index + 1:02d}.props.json"
        write_json(path, chapter)
        chapter_paths.append(str(path.relative_to(ROOT)))

    manifest = {
        "projectId": PROJECT_ID,
        "renderer": "current repository BrushLandscape composition",
        "authoringSkill": "remotion-new-video-builder",
        "sourceProps": str(SOURCE.relative_to(ROOT)),
        "sceneCount": len(scenes),
        "durationFrames": sum(scene["durationInFrames"] for scene in scenes),
        "durationSeconds": sum(scene["durationInFrames"] for scene in scenes) / 30,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "audio": FINAL_AUDIO,
        "youtubeSafeAudio": YOUTUBE_SAFE_AUDIO,
        "pilotSceneNumbers": sorted(PILOT_SCENES),
        "chapterProps": chapter_paths,
        "modifications": [
            "replaced third-party music with a 660s project-owned procedural piano BGM",
            "reduced intermediate paper dissolves from 45 frames to 18 frames",
            "kept a 90-frame final fade on scene 60",
            "added subtle completed-image parallax",
            "reduced brush cursor opacity to 0.82",
            "preserved all 60 Korean titles, cues, and natural-effect selections",
        ],
    }
    write_json(OUT_DIR / "authoring-manifest.json", manifest)
    print(f"[DONE] {OUT_DIR}")
    print(f"[SCENES] {len(scenes)}")
    print(f"[FRAMES] {manifest['durationFrames']}")
    print(f"[SECONDS] {manifest['durationSeconds']:.3f}")


if __name__ == "__main__":
    main()
