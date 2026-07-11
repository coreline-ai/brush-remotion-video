"""project.py — project.yaml 로드/검증 + 빌드 모드 판정.

모드 매트릭스:
  - srt + audio           → narration (실더빙 우선 — tts 설정은 무시+경고)
  - srt + tts / script+tts → tts      (Supertonic 합성 더빙, TTS duration이 타이밍 시계)
  - input.audio 만 제공   → whisper   (stt 스테이지로 SRT 생성)
  - 둘 다 없음            → ambient   (300f×N씬 + 합성 BGM + 시적 한줄 cue)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

FORMATS = ("youtube", "shorts")
BG_STRATEGIES = ("imagegen", "preset", "user-images")
WIDGET_MODES = ("auto", "none", "authored")
TTS_ENGINES = ("supertonic",)
TTS_TIMINGS = ("tts", "srt")
DRAWING_PROFILES = ("brush", "pen")


@dataclass
class ProjectConfig:
    """검증 완료된 project.yaml 설정. 경로는 yaml 위치 기준으로 해석된 절대 경로."""

    project_id: str
    fmt: str = "youtube"
    title: str | None = None
    srt: Path | None = None
    audio: Path | None = None
    script: Path | None = None
    tts: dict | None = None  # {engine, voice, pauseMs, timing}
    bg_strategy: str = "preset"
    bg_subject: str | None = None
    bg_images: list[Path] = field(default_factory=list)
    widgets: str = "none"
    authored_widgets: list[dict] = field(default_factory=list)
    drawing_profile: str = "brush"  # brush(수묵 리빌) | pen(선화 펜 드로잉)
    ambient_scenes: int = 3
    ambient_cues: list[str] = field(default_factory=list)
    seed: int = 1
    base_dir: Path = Path(".")

    @property
    def mode(self) -> str:
        """narration | tts | whisper | ambient."""
        if self.srt is not None and self.audio is not None:
            return "narration"  # 실더빙 우선
        if self.tts is not None and (self.srt is not None or self.script is not None):
            return "tts"
        if self.srt is not None:
            return "narration"
        if self.audio is not None:
            return "whisper"
        return "ambient"

    def tts_text(self) -> str:
        """TTS 입력 텍스트 — script 우선, 없으면 SRT 의 텍스트만 추출 (타이밍은 버림)."""
        if self.script is not None:
            return self.script.read_text(encoding="utf-8")
        if self.srt is not None:
            from .cues import parse_srt
            return "\n".join(e.text for e in parse_srt(self.srt.read_text(encoding="utf-8")))
        raise ValueError("TTS 입력 텍스트 없음 (script 또는 srt 필요)")


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(f"project.yaml 검증 실패: {msg}")


def load_project(yaml_path: str | Path) -> ProjectConfig:
    """project.yaml 로드 + 검증. 위반 시 ValueError (파이프라인 미진입)."""
    yaml_path = Path(yaml_path).resolve()
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), "최상위가 매핑이 아님")
    base = yaml_path.parent

    project_id = raw.get("projectId")
    _require(isinstance(project_id, str) and project_id.strip() != "", "projectId 필수")
    fmt = raw.get("format", "youtube")
    _require(fmt in FORMATS, f"format 은 {FORMATS} 중 하나여야 함 (입력: {fmt!r})")

    inp = raw.get("input") or {}
    _require(isinstance(inp, dict), "input 은 매핑이어야 함")
    srt = inp.get("srt")
    audio = inp.get("audio")
    script = inp.get("script")
    srt_p = (base / srt).resolve() if srt else None
    audio_p = (base / audio).resolve() if audio else None
    script_p = (base / script).resolve() if script else None
    if srt_p is not None:
        _require(srt_p.is_file(), f"input.srt 파일 없음: {srt_p}")
    if audio_p is not None:
        _require(audio_p.is_file(), f"input.audio 파일 없음: {audio_p}")
    if script_p is not None:
        _require(script_p.is_file(), f"input.script 파일 없음: {script_p}")

    # input.tts — {engine, voice, pauseMs, timing}. timing: srt 는 후속 여지(옵션 자리만).
    tts_raw = inp.get("tts")
    tts_cfg: dict | None = None
    if tts_raw is not None:
        _require(isinstance(tts_raw, dict), "input.tts 는 매핑이어야 함")
        engine = tts_raw.get("engine", "supertonic")
        _require(engine in TTS_ENGINES, f"input.tts.engine 은 {TTS_ENGINES} 중 하나여야 함 (입력: {engine!r})")
        timing = tts_raw.get("timing", "tts")
        _require(timing in TTS_TIMINGS, f"input.tts.timing 은 {TTS_TIMINGS} 중 하나여야 함 (입력: {timing!r})")
        pause_ms = int(tts_raw.get("pauseMs", 300))
        _require(pause_ms >= 0, "input.tts.pauseMs 는 0 이상")
        tts_cfg = {"engine": engine, "voice": str(tts_raw.get("voice", "F1")),
                   "pauseMs": pause_ms, "timing": timing}
        if audio_p is not None:
            log.warning("input.audio(실더빙)와 tts 가 함께 설정됨 — 실더빙 우선, TTS 무시")
    if script_p is not None:
        _require(tts_cfg is not None, "input.script 은 input.tts 와 함께 사용해야 함 (타이밍/더빙 소스 없음)")

    bg = raw.get("background") or {}
    _require(isinstance(bg, dict), "background 는 매핑이어야 함")
    strategy = bg.get("strategy", "preset")
    _require(strategy in BG_STRATEGIES, f"background.strategy 는 {BG_STRATEGIES} 중 하나여야 함 (입력: {strategy!r})")
    images = [(base / p).resolve() for p in (bg.get("images") or [])]
    if strategy == "user-images":
        _require(len(images) >= 1, "user-images 전략에는 background.images 최소 1장 필요")
        for p in images:
            _require(p.is_file(), f"background.images 파일 없음: {p}")

    widgets_raw = raw.get("widgets", "none")
    authored: list[dict] = []
    if isinstance(widgets_raw, list):  # 인라인 authored 위젯 목록
        widgets_mode = "authored"
        authored = widgets_raw
    else:
        widgets_mode = widgets_raw
        _require(widgets_mode in WIDGET_MODES, f"widgets 는 {WIDGET_MODES} 또는 위젯 목록이어야 함 (입력: {widgets_raw!r})")
    if widgets_mode == "auto":
        # 위젯 auto 배치는 위젯 워크스트림 통합 후 지원 — 지금은 none 으로 처리
        log.warning("widgets: auto 는 보류 상태 — none 으로 처리합니다")
        widgets_mode = "none"

    # drawing — {profile: brush|pen}. 기본 brush, 오타는 즉시 거부.
    drawing = raw.get("drawing") or {}
    _require(isinstance(drawing, dict), "drawing 은 매핑이어야 함")
    profile = drawing.get("profile", "brush")
    _require(profile in DRAWING_PROFILES,
             f"drawing.profile 은 {DRAWING_PROFILES} 중 하나여야 함 (입력: {profile!r})")

    amb = raw.get("ambient") or {}
    _require(isinstance(amb, dict), "ambient 는 매핑이어야 함")
    ambient_scenes = int(amb.get("scenes", 3))
    _require(ambient_scenes >= 1, "ambient.scenes 는 1 이상")

    return ProjectConfig(
        project_id=project_id.strip(),
        fmt=fmt,
        title=raw.get("title"),
        srt=srt_p,
        audio=audio_p,
        script=script_p,
        tts=tts_cfg,
        bg_strategy=strategy,
        bg_subject=bg.get("subject") or bg.get("style"),
        bg_images=images,
        widgets=widgets_mode,
        authored_widgets=authored,
        drawing_profile=profile,
        ambient_scenes=ambient_scenes,
        ambient_cues=list(amb.get("cues") or []),
        seed=int(raw.get("seed", 1)),
        base_dir=base,
    )
