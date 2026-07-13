#!/usr/bin/env python3
"""Import selected new-video-gen projects into brush_remotion_video.

The public assets are copied separately. This script keeps an untouched copy of
the chosen legacy props and writes a schema-v1 props file that the independent
BrushLandscape / BrushPortrait compositions can consume.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


PROJECTS = {
    "ai-personal-rules-imagegen-fhd": ("ai-personal-rules-imagegen-fhd", "render-props-brush-bgm.json"),
    "ai-personal-rules-white-brush": ("ai-personal-rules-white-brush", "render-props.json"),
    "brush-draw-full": ("brush-draw-full", "render-props-authored.json"),
    "city-watercolor-600s": ("city-watercolor-600s", "render-props.json"),
    "earth-quiet-day-60": ("earth-quiet-day-60", "render-props.json"),
    "idea-to-product-brush-white": ("idea-to-product-brush-white", "render-props.json"),
    "idea-to-product-brush-white-imagegen": (
        "idea-to-product-brush-white-imagegen",
        "render-props-brush-bgm.json",
    ),
    "morning-tea-table-brush": ("morning-tea-table-brush", "render-props-stable.json"),
    "rainy-window-lofi-brush": ("rainy-window-lofi-brush", "render-props.json"),
    "relaxing-nature-shorts-1000s": ("relaxing-nature-1000s", "render-props-1000s.json"),
    "relaxing-nature-shorts-300s": ("relaxing-nature-300s", "render-props-300s.json"),
    "relaxing-nature-youtube-600s": (
        "relaxing-nature-youtube-600s",
        "render-props-soft-transition.json",
    ),
    "winter-snow-pine-brush": ("winter-snow-pine-brush", "render-props-stable.json"),
}

SCENE_KEYS = {
    "routes",
    "durationInFrames",
    "faint",
    "edgeFeather",
    "linearDraw",
    "developFrames",
    "completionMode",
    "prewashOpacity",
    "prewashFrames",
    "prewashHoldFrames",
    "prewashBlur",
    "outroFadeFrames",
    "outroWashOpacity",
    "outroBlur",
    "brushDynamics",
    "cues",
    "topTitle",
    "subtitleStyle",
    "naturalEffects",
}

CARD_WIDGET_TYPES = {
    "FlowDiagram",
    "TimelineStepper",
    "DataTable",
    "ProcessStepCard",
    "WarningCard",
    "PersonAvatar",
    "ChatBubble",
    "CompareBars",
    "BulletList",
    "QuoteText",
    "Headline",
}

WHITE_WIDGET_FALLBACKS = {
    "InsightTile": "ProcessStepCard",
    "Grid": "DataTable",
    "AccentRing": "Headline",
    "ArrowConnector": "FlowDiagram",
    "Badge": "Headline",
    "RingChart": "CompareBars",
}

WIDGET_BASE_KEYS = {"x", "y", "w", "h", "enterAt", "title", "kicker", "caption", "accent"}


def _scene_id(scene: dict[str, Any], index: int) -> str:
    if scene.get("id"):
        return str(scene["id"])
    match = re.search(r"scene[-_](\d+)", str(scene.get("routes", "")), re.IGNORECASE)
    return f"scene-{int(match.group(1)):02d}" if match else f"scene-{index:02d}"


def _base_widget(widget: dict[str, Any]) -> dict[str, Any]:
    base = {key: widget[key] for key in WIDGET_BASE_KEYS if key in widget}
    base.setdefault("x", 0)
    base.setdefault("y", 0)
    base.setdefault("w", 360)
    base.setdefault("h", 200)
    base.setdefault("enterAt", 0)
    base.setdefault("title", str(widget.get("caption") or widget.get("type") or "Widget"))
    return base


def _convert_widget(widget: dict[str, Any]) -> dict[str, Any] | None:
    widget_type = str(widget.get("type", ""))
    base = _base_widget(widget)
    if widget_type == "stat":
        return {"type": "stat", **base, "value": widget.get("value", ""), **({"sub": widget["sub"]} if "sub" in widget else {})}
    if widget_type == "text":
        lines = widget.get("lines") or [widget.get("caption") or widget.get("title") or ""]
        return {"type": "text", **base, "lines": [str(line) for line in lines if str(line)]}
    if widget_type == "donut":
        return {"type": "donut", **base, "pct": float(widget.get("pct", 50))}
    if widget_type == "bars":
        return {"type": "bars", **base, "values": widget.get("values") or [35, 60, 82]}

    mapped = widget_type if widget_type in CARD_WIDGET_TYPES else WHITE_WIDGET_FALLBACKS.get(widget_type)
    if not mapped:
        return None
    items = []
    for item in widget.get("items") or []:
        if not isinstance(item, dict):
            continue
        clean = {key: item[key] for key in ("label", "detail", "value", "tone") if key in item}
        if "label" in clean:
            items.append(clean)
    return {"type": mapped, **base, "items": items}


def convert_props(public_id: str, source: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    dropped_widgets = 0
    mapped_white_widgets = 0
    for index, legacy in enumerate(source.get("scenes") or [], start=1):
        scene = {"id": _scene_id(legacy, index)}
        for key in SCENE_KEYS:
            if key in legacy and legacy[key] is not None:
                scene[key] = legacy[key]

        widgets = []
        for widget in legacy.get("widgets") or []:
            converted = _convert_widget(widget)
            if converted:
                widgets.append(converted)
            else:
                dropped_widgets += 1
        for widget in legacy.get("whiteWidgets") or []:
            converted = _convert_widget(widget)
            if converted:
                widgets.append(converted)
                mapped_white_widgets += 1
            else:
                dropped_widgets += 1
        if widgets:
            scene["widgets"] = widgets
        scenes.append(scene)

    brush = source.get("brush")
    if isinstance(brush, dict) and "src" in brush:
        brush = {"kind": "image", **brush}

    converted = {
        "schemaVersion": 1,
        "projectId": public_id,
        "title": source.get("title") or public_id,
        "format": "shorts" if "shorts" in public_id else "youtube",
        "audio": source.get("audio"),
        "paper": source.get("paper", "#fbfaf6"),
        "scenes": scenes,
    }
    if brush:
        converted["brush"] = brush

    manifest = {
        "publicProjectId": public_id,
        "sceneCount": len(scenes),
        "durationFrames": sum(int(scene.get("durationInFrames", 0)) for scene in scenes),
        "composition": "BrushPortrait" if converted["format"] == "shorts" else "BrushLandscape",
        "mappedWhiteWidgets": mapped_white_widgets,
        "droppedWidgets": dropped_widgets,
        "notes": [
            "Legacy whiteWidgets are mapped to the independent renderer's 15-type widget catalog.",
            "Unsupported transition-only fields are intentionally omitted from schema v1.",
        ],
    }
    return converted, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default="/Users/hwanchoi/project_202606/new-video-gen",
        help="new-video-gen repository root",
    )
    parser.add_argument("--target-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    target_root = Path(args.target_root).resolve()
    library_manifest = []

    for public_id, (source_data_id, filename) in PROJECTS.items():
        source_path = source_root / "data" / source_data_id / filename
        target_dir = target_root / "data" / public_id
        target_dir.mkdir(parents=True, exist_ok=True)
        raw_target = target_dir / "source-render-props.json"
        shutil.copy2(source_path, raw_target)
        source_props = json.loads(source_path.read_text(encoding="utf-8"))
        converted, manifest = convert_props(public_id, source_props)
        manifest["sourceDataProject"] = source_data_id
        manifest["sourceProps"] = str(source_path)
        manifest["convertedProps"] = str(target_dir / "props-imported.json")
        (target_dir / "props-imported.json").write_text(
            json.dumps(converted, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (target_dir / "import-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        library_manifest.append(manifest)
        print(f"[IMPORTED] {public_id}: {manifest['sceneCount']} scenes -> {manifest['composition']}")

    output = target_root / "data" / "new-video-gen-library.json"
    output.write_text(json.dumps(library_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] {output}")


if __name__ == "__main__":
    main()
