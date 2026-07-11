#!/usr/bin/env python3
"""bin/build.py — project.yaml 하나로 완성 mp4 를 만드는 단일 진입점.

스테이지: stt → cues → background → clean → routes → layout → props → render → mux → qa
산출물 캐시: data/{projectId}/stages/{stage}.json — 마커가 있으면 스킵.
재개: --from <stage> 로 해당 스테이지부터 다시 실행 (앞 스테이지는 캐시 스킵).

사용:
  pipeline/.venv/bin/python bin/build.py examples/narration/project.yaml
  pipeline/.venv/bin/python bin/build.py examples/ambient/project.yaml --from render
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PY = REPO_ROOT / "pipeline" / ".venv" / "bin" / "python"

# pipeline venv 밖에서 실행되면 venv 파이썬으로 재실행 (명령 1회 원칙)
try:
    import brushvid  # noqa: F401
except ImportError:  # pragma: no cover
    if VENV_PY.is_file() and Path(sys.executable) != VENV_PY:
        import os
        os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
    raise SystemExit("brushvid 미설치 — pipeline/README.md 의 부트스트랩 절차를 먼저 실행하세요")

from brushvid import audio as bv_audio
from brushvid import background as bv_bg
from brushvid import qa as bv_qa
from brushvid import render as bv_render
from brushvid import stt as bv_stt
from brushvid import tts as bv_tts
from brushvid.cues import FPS, group_scenes, srt_to_cues, title_color
from brushvid.layout import validate_layout
from brushvid.project import ProjectConfig, load_project
from brushvid.props import build_props, build_scene, load_schema, write_props
from brushvid.routes import RouteParams, generate_routes, write_routes

log = logging.getLogger("build")

STAGES = ["stt", "cues", "background", "clean", "routes", "layout", "props", "render", "mux", "qa"]

# pen 프로파일 상수 (dev-plan pen Phase 1 "핵심 발견" 3요소: 잉크-알파 분리 + 정밀 routes + contain 배경)
PEN_PAPER_HEX = "#f2eee3"
PEN_BRUSH = {"kind": "pen", "w": 140}
PEN_SCENE_PRESET = {
    "faint": 1.0, "edgeFeather": 1, "developFrames": 8,
    "prewashOpacity": 0, "prewashFrames": 0, "prewashHoldFrames": 0,
}
PEN_BRUSH_DYNAMICS = {"drawSpeedScale": 1.0, "touchScale": 1.0, "touchJitter": 0,
                      "pathJitter": 0, "randomizeOrder": False, "randomReverse": False}


def pen_route_params(duration: int, seed: int) -> RouteParams:
    """pen 프로파일 정밀 routes 파라미터 — drawEnd 를 앞당겨(35%) 감상 구간 확보."""
    draw_end = round(duration * 0.35)
    return RouteParams(
        duration=duration, draw_start=8, draw_end=draw_end, pen_invisible_after=draw_end + 8,
        seed=seed, analyze_scale=1.5, contour_width=18, rdp_eps=1.5, max_len=300,
        min_route_len=12, seal_width=24, seal_step=18,
        group_by_zone=True,  # 매크로 존(오브젝트) 단위 드로잉 순서
    )


# 앰비언트 모드 기본값
AMBIENT_SCENE_FRAMES = 300
AMBIENT_DEFAULT_CUES = [
    "바람이 지나간 자리에 고요가 남는다",
    "숲은 서두르지 않는다",
    "눈 내린 아침, 세상이 한 뼘 느려진다",
    "물소리는 길을 묻지 않는다",
    "노을은 하루를 천천히 접는다",
]


class StageLedger:
    """스테이지 마커(data/{pid}/stages/*.json) 기반 캐시/스킵/재개 관리."""

    def __init__(self, stages_dir: Path):
        self.dir = stages_dir
        self.dir.mkdir(parents=True, exist_ok=True)

    def marker(self, stage: str) -> Path:
        return self.dir / f"{stage}.json"

    def is_done(self, stage: str) -> bool:
        return self.marker(stage).is_file()

    def payload(self, stage: str) -> dict:
        return json.loads(self.marker(stage).read_text(encoding="utf-8"))

    def mark_done(self, stage: str, payload: dict | None = None) -> None:
        data = {"stage": stage, "completedAt": time.strftime("%Y-%m-%d %H:%M:%S"), **(payload or {})}
        self.marker(stage).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def invalidate_from(self, stage: str) -> None:
        """stage 및 이후 스테이지 마커 제거 (--from 재개)."""
        if stage not in STAGES:
            raise ValueError(f"--from 스테이지는 {STAGES} 중 하나여야 함 (입력: {stage!r})")
        for s in STAGES[STAGES.index(stage):]:
            self.marker(s).unlink(missing_ok=True)


class Pipeline:
    """스테이지 오케스트레이션. 경로 규약:

    data/{pid}/   — props.json, scenes.json, stages/, qa/, bgm.wav
    public/{pid}/ — bg/*.png, routes/*.routes.json (Remotion staticFile 대상)
    output/{pid}.mp4 — 최종 산출물
    """

    def __init__(self, cfg: ProjectConfig):
        self.cfg = cfg
        pid = cfg.project_id
        self.data_dir = REPO_ROOT / "data" / pid
        self.public_dir = REPO_ROOT / "public" / pid
        self.output = REPO_ROOT / "output" / f"{pid}.mp4"
        self.video_only = self.data_dir / "video-noaudio.mp4"
        self.scenes_json = self.data_dir / "scenes.json"
        self.props_json = self.data_dir / "props.json"
        self.ledger = StageLedger(self.data_dir / "stages")

    # ── 실행 ──
    def run(self, from_stage: str | None = None) -> Path:
        if from_stage:
            self.ledger.invalidate_from(from_stage)
        for stage in STAGES:
            fn = getattr(self, f"stage_{stage}")
            if self.ledger.is_done(stage):
                log.info("[skip] %s (캐시: %s)", stage, self.ledger.marker(stage).relative_to(REPO_ROOT))
                continue
            log.info("[run ] %s", stage)
            payload = fn() or {}
            self.ledger.mark_done(stage, payload)
        log.info("완료 → %s", self.output.relative_to(REPO_ROOT))
        return self.output

    # ── 공용 헬퍼 ──
    def _scenes(self) -> list[dict]:
        return json.loads(self.scenes_json.read_text(encoding="utf-8"))

    def _write_scenes(self, scenes: list[dict]) -> None:
        self.scenes_json.parent.mkdir(parents=True, exist_ok=True)
        self.scenes_json.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")

    def _audio_path(self) -> Path | None:
        """mux 대상 오디오 (내레이션/whisper: 더빙, tts: 합성 더빙, 앰비언트: 합성 BGM)."""
        if self.cfg.audio is not None:
            return self.cfg.audio
        if self.cfg.mode == "tts":
            return self.data_dir / "tts" / "narration.wav"
        if self.cfg.mode == "ambient":
            return self.data_dir / "bgm.wav"
        return None

    # ── 스테이지 ──
    def stage_stt(self) -> dict:
        """stt 자리 분기: whisper 는 전사, tts 는 더빙 합성 (둘 다 SRT 산출)."""
        if self.cfg.mode == "tts":
            res = bv_tts.synthesize_narration(
                self.cfg.tts_text(),
                self.data_dir / "tts" / "narration.wav",
                self.data_dir / "tts" / "narration.srt",
                engine=self.cfg.tts["engine"], voice=self.cfg.tts["voice"],
                pause_ms=self.cfg.tts["pauseMs"],
            )
            return {"srt": res["srt"], "wav": res["wav"], "durationSec": res["durationSec"],
                    "sentences": len(res["entries"])}
        if self.cfg.mode != "whisper":
            log.info("stt: %s 모드 — 해당 없음", self.cfg.mode)
            return {"skippedReason": self.cfg.mode}
        srt = bv_stt.transcribe(self.cfg.audio, self.data_dir / "stt")
        return {"srt": str(srt)}

    def stage_cues(self) -> dict:
        if self.cfg.mode == "ambient":
            lines = self.cfg.ambient_cues or AMBIENT_DEFAULT_CUES
            scenes = []
            for i in range(self.cfg.ambient_scenes):
                text = lines[i % len(lines)]
                scenes.append({
                    "durationInFrames": AMBIENT_SCENE_FRAMES,
                    "cues": [{"text": text, "from": 40, "to": AMBIENT_SCENE_FRAMES - 40}],
                })
        else:
            # tts/whisper 는 stt 스테이지 산출 SRT 사용 (tts 모드는 TTS duration이 타이밍의 시계)
            srt_path = self.cfg.srt if self.cfg.mode == "narration" \
                else Path(self.ledger.payload("stt")["srt"])
            cues = srt_to_cues(srt_path.read_text(encoding="utf-8"), fps=FPS)
            scenes = group_scenes(cues)
            # TC-4.E2: 더빙 오디오 길이와 씬 합산 정합 (>1s 불일치 시 경고+보정)
            timing_audio = self.cfg.audio if self.cfg.audio is not None \
                else (self._audio_path() if self.cfg.mode == "tts" else None)
            if timing_audio is not None:
                bv_audio.reconcile_scenes_with_audio(scenes, bv_audio.probe_duration(timing_audio), fps=FPS)
        self._write_scenes(scenes)
        return {"sceneCount": len(scenes), "totalFrames": sum(s["durationInFrames"] for s in scenes)}

    def stage_background(self) -> dict:
        results = []
        for i in range(len(self._scenes())):
            out = self.public_dir / "bg" / f"scene-{i + 1:02d}.png"
            res = bv_bg.generate(self.cfg.bg_strategy, out, subject=self.cfg.bg_subject,
                                 images=self.cfg.bg_images or None, seed=self.cfg.seed + i * 37)
            results.append(res["strategy"])
        return {"strategies": results}

    def stage_clean(self) -> dict:
        if self.cfg.drawing_profile == "pen":
            # pen: 잉크-알파 분리 (contain + 종이색 패딩, 잘림 금지). flat 은 routes 입력.
            fracs = []
            for i in range(len(self._scenes())):
                bg = self.public_dir / "bg" / f"scene-{i + 1:02d}.png"
                res = bv_bg.separate_ink(bg, self.public_dir / "bg" / f"scene-{i + 1:02d}-ink.png",
                                         self.public_dir / "bg" / f"scene-{i + 1:02d}-content.png")
                fracs.append(round(res["inkFraction"], 4))
            return {"profile": "pen", "inkFractions": fracs}
        for i in range(len(self._scenes())):
            bg = self.public_dir / "bg" / f"scene-{i + 1:02d}.png"
            bv_bg.clean(bg, self.public_dir / "bg" / f"scene-{i + 1:02d}-content.png")
        return {}

    def stage_routes(self) -> dict:
        pen = self.cfg.drawing_profile == "pen"
        coverages = []
        for i, scene in enumerate(self._scenes()):
            content = self.public_dir / "bg" / f"scene-{i + 1:02d}-content.png"
            d = scene["durationInFrames"]
            seed = self.cfg.seed + i * 37
            if pen:
                params = pen_route_params(d, seed)
                image_rel = f"{self.cfg.project_id}/bg/scene-{i + 1:02d}-ink.png"  # 리빌 대상은 잉크-알파
            else:
                params = RouteParams(
                    duration=d, draw_start=8, draw_end=round(d * 0.73), pen_invisible_after=round(d * 0.76),
                    seed=seed, contour_width=40, seal_width=56, seal_step=20,
                )
                image_rel = f"{self.cfg.project_id}/bg/scene-{i + 1:02d}-content.png"
            data = generate_routes(content, params, image_rel=image_rel)
            write_routes(data, self.public_dir / "routes" / f"scene-{i + 1:02d}.routes.json")
            coverages.append(data["meta"]["coverage"])
        return {"coverages": coverages, "profile": self.cfg.drawing_profile}

    def stage_layout(self) -> dict:
        if self.cfg.widgets != "authored" or not self.cfg.authored_widgets:
            log.info("layout: widgets=%s — 배치/검증 대상 없음 (auto 는 보류)", self.cfg.widgets)
            return {"widgets": self.cfg.widgets}
        # authored 위젯 겹침 검증 (첫 씬 배경 기준, hard-fail)
        scenes = self._scenes()
        content = self.public_dir / "bg" / "scene-01-content.png"
        res = validate_layout(self.cfg.authored_widgets, has_cues=bool(scenes[0].get("cues")),
                              image_path=content if content.is_file() else None)
        if not res.ok:
            raise SystemExit("레이아웃 검증 실패(hard-fail): " + "; ".join(res.fails))
        return {"widgets": "authored", "count": len(self.cfg.authored_widgets), "warns": res.warns}

    def stage_props(self) -> dict:
        scenes_meta = self._scenes()
        scene_props = []
        schema_scene_props = load_schema()["definitions"]["RenderProps"]["properties"]["scenes"]["items"]["properties"]
        for i, sm in enumerate(scenes_meta):
            kwargs: dict = {}
            if i == 0 and self.cfg.title:
                accent = title_color(self.public_dir / "bg" / "scene-01-content.png")
                kwargs["top_title"] = {"lines": [self.cfg.title], "enterAt": 12, "accent": accent}
            if self.cfg.widgets == "authored" and self.cfg.authored_widgets and i == 0:
                if "widgets" in schema_scene_props:
                    kwargs["widgets"] = self.cfg.authored_widgets
                else:  # 위젯 워크스트림 통합 전 — 스키마에 없으면 제외
                    log.warning("스키마에 scenes[].widgets 없음 — authored 위젯은 props 에서 제외(통합 대기)")
            pen = self.cfg.drawing_profile == "pen"
            if pen:
                kwargs.update(PEN_SCENE_PRESET)  # 즉시 또렷 + 선화 feather + prewash 없음
                dynamics = {**PEN_BRUSH_DYNAMICS, "seed": self.cfg.seed + i}
            else:
                dynamics = {"drawSpeedScale": 1.0, "touchScale": 1.45, "touchJitter": 0.22,
                            "randomizeOrder": True, "randomReverse": True, "seed": self.cfg.seed + i}
            scene_props.append(build_scene(
                f"scene-{i + 1:02d}", f"{self.cfg.project_id}/routes/scene-{i + 1:02d}.routes.json",
                sm["durationInFrames"], cues=sm.get("cues") or None,
                brush_dynamics=dynamics,
                **kwargs,
            ))
        pen = self.cfg.drawing_profile == "pen"
        props = build_props(self.cfg.project_id, scene_props, title=self.cfg.title,
                            fmt=self.cfg.fmt, audio=None,  # 오디오는 렌더 후 ffmpeg mux
                            paper=PEN_PAPER_HEX if pen else "#fbfaf6",
                            brush=dict(PEN_BRUSH) if pen else None)
        write_props(props, self.props_json)
        return {"props": str(self.props_json.relative_to(REPO_ROOT)), "profile": self.cfg.drawing_profile}

    def stage_render(self) -> dict:
        composition = "BrushPortrait" if self.cfg.fmt == "shorts" else "BrushLandscape"
        bv_render.render(self.props_json, self.video_only, composition=composition)
        return {"video": str(self.video_only.relative_to(REPO_ROOT)), "composition": composition}

    def stage_mux(self) -> dict:
        audio = self._audio_path()
        if self.cfg.mode == "ambient":
            total_sec = sum(s["durationInFrames"] for s in self._scenes()) / FPS
            bv_audio.synth_ambient_bgm(audio, total_sec, seed=self.cfg.seed)
        if audio is None:
            log.info("mux: 오디오 없음 — 영상만 복사")
            self.output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.video_only, self.output)
            return {"audio": None}
        bv_render.mux_audio(self.video_only, audio, self.output)
        return {"audio": str(audio)}

    def stage_qa(self) -> dict:
        frames, labels = [], {}
        offset = 0
        for i, sm in enumerate(self._scenes()):
            d = sm["durationInFrames"]
            for tag, f in (("start", offset + 12), ("mid", offset + d // 2), ("end", offset + d - 8)):
                frames.append(f)
                labels[f] = f"scene-{i + 1:02d} {tag}"
            offset += d
        composition = "BrushPortrait" if self.cfg.fmt == "shorts" else "BrushLandscape"
        qa_dir = self.data_dir / "qa"
        entries = bv_qa.capture_frames(self.props_json, frames, qa_dir,
                                       composition=composition, labels=labels)
        bv_qa.write_manifest(entries, qa_dir, project_id=self.cfg.project_id,
                             props=str(self.props_json.relative_to(REPO_ROOT)))
        sheet = bv_qa.contact_sheet(qa_dir, cols=3)
        gallery = bv_qa.build_gallery(self.props_json, qa_dir)  # 씬 갤러리(카드뷰)
        return {"captures": len(entries), "contactSheet": str(sheet.relative_to(REPO_ROOT)),
                "gallery": str(gallery.relative_to(REPO_ROOT))}


def main() -> None:
    ap = argparse.ArgumentParser(description="project.yaml → 완성 mp4 (스테이지 캐시 + --from 재개)")
    ap.add_argument("project_yaml", help="project.yaml 경로")
    ap.add_argument("--from", dest="from_stage", default=None,
                    help=f"이 스테이지부터 다시 실행 {STAGES}")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname).1s %(name)s: %(message)s")
    cfg = load_project(a.project_yaml)
    log.info("project=%s mode=%s format=%s", cfg.project_id, cfg.mode, cfg.fmt)
    Pipeline(cfg).run(a.from_stage)


if __name__ == "__main__":
    main()
