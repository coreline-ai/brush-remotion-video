"""props.py — render-props 빌더 + jsonschema 검증.

스키마의 유일한 진실은 TS(Zod)에서 내보낸 schema/render-props.schema.json —
여기서는 소비(검증)만 하고 형태를 재정의하지 않는다.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

# 리포 루트/스키마 위치 (pipeline/brushvid/props.py 기준 2단계 위가 리포 루트)
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schema" / "render-props.schema.json"

_schema_cache: dict[str, dict] = {}


def load_schema(schema_path: str | Path = SCHEMA_PATH) -> dict:
    """render-props JSON Schema 로드 (캐시)."""
    key = str(schema_path)
    if key not in _schema_cache:
        _schema_cache[key] = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return _schema_cache[key]


def default_brush() -> dict:
    """공용 붓 커서 에셋 블록 (public/brush-draw/brush.png)."""
    return {"src": "brush-draw/brush.png", "w": 556, "h": 344, "tipx": 25, "tipy": 315}


def build_scene(scene_id: str, routes: str | None, duration_in_frames: int, *,
                cues: list[dict] | None = None, top_title: dict | None = None,
                subtitle_style: dict | None = None, natural_effects: dict | None = None,
                brush_dynamics: dict | None = None, **overrides) -> dict:
    """씬 1개 빌드. 기본 연출 값은 golden-single 프로파일을 따른다."""
    scene: dict = {
        "id": scene_id,
        "durationInFrames": int(duration_in_frames),
        "faint": 0.68,
        "edgeFeather": 12,
        "linearDraw": True,
        "developFrames": 20,
        "prewashOpacity": 0.65,
        "prewashFrames": 36,
        "prewashHoldFrames": 10,
        "prewashBlur": 12,
    }
    if routes is not None:
        scene["routes"] = routes
    scene["brushDynamics"] = brush_dynamics if brush_dynamics is not None else {
        "drawSpeedScale": 1.0,
        "touchScale": 1.45,
        "touchJitter": 0.22,
        "randomizeOrder": True,
        "randomReverse": True,
        "seed": 7701,
    }
    if cues:
        scene["cues"] = cues
    if top_title:
        scene["topTitle"] = top_title
    if subtitle_style:
        scene["subtitleStyle"] = subtitle_style
    if natural_effects:
        scene["naturalEffects"] = natural_effects
    scene.update(overrides)
    return scene


def build_props(project_id: str, scenes: list[dict], *, title: str | None = None,
                fmt: str = "youtube", audio: str | None = None, paper: str = "#fbfaf6",
                brush: dict | None = None) -> dict:
    """canonical render-props 빌드 (schemaVersion=1)."""
    props: dict = {
        "schemaVersion": 1,
        "projectId": project_id,
        "format": fmt,
        "paper": paper,
        "brush": brush if brush is not None else default_brush(),
        "scenes": scenes,
    }
    if title is not None:
        props["title"] = title
    if audio is not None:
        props["audio"] = audio
    return props


def validate_props(props: dict, schema_path: str | Path = SCHEMA_PATH) -> dict:
    """schema/render-props.schema.json 으로 검증. 위반 시 jsonschema.ValidationError."""
    jsonschema.validate(instance=props, schema=load_schema(schema_path))
    return props


def write_props(props: dict, out_path: str | Path, schema_path: str | Path = SCHEMA_PATH) -> Path:
    """검증 후 저장."""
    validate_props(props, schema_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
