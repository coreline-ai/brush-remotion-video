#!/usr/bin/env python3
"""Harmony-aware, original solo piano BGM skill CLI."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
# Run the repository source directly so a newly added independent skill does not
# depend on a stale installed wheel. The project venv remains preferred by users.
PIPELINE_SOURCE = str(REPO_ROOT / "pipeline")
if PIPELINE_SOURCE not in sys.path:
    sys.path.insert(0, PIPELINE_SOURCE)
from brushvid.piano_bgm import (OUTPUT_ROOT, PROJECTS_ROOT, PianoBgmError, PRESETS, approve_listening, media_tool,
                                compose, lint_score, load_request, load_score_bundle,
                                performance_from_score, qa_project, write_listening_review,
                                write_score_bundle)
from brushvid.piano_render import render_to_wav, write_render_report

DEFAULT_INSTRUMENT = REPO_ROOT / "local-assets" / "instruments" / "noct-salamander-grand-v6-1a"
DEFAULT_SFZ = DEFAULT_INSTRUMENT / "sfz_minimum" / "Noct-SalamanderGrandPiano_treble2.0db.Recommended.sfz"


def _output_roots(args: argparse.Namespace) -> tuple[Path, Path]:
    return Path(args.projects_root).resolve(), Path(args.output_root).resolve()


def _request_for(args: argparse.Namespace) -> dict:
    return load_request(args.request)


def _compose(args: argparse.Namespace) -> dict:
    request = _request_for(args)
    projects_root, _ = _output_roots(args)
    score = compose(request)
    lint = lint_score(score)
    if lint["status"] != "PASS":
        raise PianoBgmError("music lint FAIL: " + json.dumps(lint["errors"], ensure_ascii=False))
    performance = performance_from_score(score)
    paths = write_score_bundle(request, score, performance, lint, projects_root=projects_root)
    return {"request": request, "paths": {key: str(value) for key, value in paths.items()}, "lint": lint}


def _render(args: argparse.Namespace) -> dict:
    projects_root, output_root = _output_roots(args)
    request, score, performance = load_score_bundle(args.project_id, projects_root=projects_root)
    lint = lint_score(score)
    if lint["status"] != "PASS":
        raise PianoBgmError("music lint FAIL: " + json.dumps(lint["errors"], ensure_ascii=False))
    output = output_root / args.project_id
    output.mkdir(parents=True, exist_ok=True)
    instrument = Path(args.instrument_root).resolve()
    sfz = Path(args.sfz).resolve()
    raw = output / "raw-48k24.wav"
    report = render_to_wav(performance, instrument_root=instrument, sfz=sfz, output=raw)
    write_render_report(output / "render-report.json", report)
    master = output / "master-48k24.wav"
    delivery = output / f"{args.project_id}-44k16.wav"
    ffmpeg = media_tool("ffmpeg")
    try:
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-af",
                        "loudnorm=I=-20:LRA=7:TP=-1.5", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(master)], check=True)
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(master), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(delivery)], check=True)
    except subprocess.CalledProcessError as exc:
        raise PianoBgmError("master WAV export 실패") from exc
    preview = output / "preview-30s-44k16.wav"
    if request["output"].get("preview", True):
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(delivery), "-t", "30", "-c:a", "pcm_s16le", str(preview)], check=True)
    return {"projectId": args.project_id, "raw": str(raw), "master": str(master), "delivery": str(delivery), "report": report}


def _build(args: argparse.Namespace) -> dict:
    composed = _compose(args)
    request = composed["request"]
    args.project_id = request["projectId"]
    rendered = _render(args)
    projects_root, output_root = _output_roots(args)
    qa = qa_project(args.project_id, projects_root=projects_root, output_root=output_root)
    return {"compose": composed, "render": rendered, "qa": qa}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects-root", default=str(PROJECTS_ROOT))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="request schema/key/preset 검증")
    validate.add_argument("--request", required=True)
    validate.set_defaults(func=lambda args: {"request": _request_for(args), "presets": sorted(PRESETS)})
    compose_cmd = sub.add_parser("compose", help="request -> harmony-aware score/performance/lint")
    compose_cmd.add_argument("--request", required=True)
    compose_cmd.set_defaults(func=_compose)
    render = sub.add_parser("render", help="PASS score -> local SFZ sample raw/master/delivery WAV")
    render.add_argument("--project-id", required=True)
    render.add_argument("--instrument-root", default=str(DEFAULT_INSTRUMENT))
    render.add_argument("--sfz", default=str(DEFAULT_SFZ))
    render.set_defaults(func=_render)
    build = sub.add_parser("build", help="validate + compose + render + technical QA")
    build.add_argument("--request", required=True)
    build.add_argument("--project-id", default="")
    build.add_argument("--instrument-root", default=str(DEFAULT_INSTRUMENT))
    build.add_argument("--sfz", default=str(DEFAULT_SFZ))
    build.set_defaults(func=_build)
    lint = sub.add_parser("lint", help="saved score의 음악 lint")
    lint.add_argument("--project-id", required=True)
    lint.set_defaults(func=lambda args: lint_score(load_score_bundle(args.project_id, projects_root=_output_roots(args)[0])[1]))
    qa = sub.add_parser("qa", help="format/loudness/provenance QA; human listening remains pending")
    qa.add_argument("--project-id", required=True)
    qa.set_defaults(func=lambda args: qa_project(args.project_id, projects_root=_output_roots(args)[0], output_root=_output_roots(args)[1]))
    review = sub.add_parser("review", help="HTML + JSON people-listening review template")
    review.add_argument("--project-id", required=True)
    review.set_defaults(func=lambda args: {"review": str(write_listening_review(args.project_id, output_root=_output_roots(args)[1]))})
    approve = sub.add_parser("approve", help="two-environment listening approval JSON import")
    approve.add_argument("--project-id", required=True)
    approve.add_argument("--review-result", required=True)
    approve.set_defaults(func=lambda args: approve_listening(args.project_id, args.review_result, output_root=_output_roots(args)[1]))
    args = parser.parse_args(argv)
    try:
        print(json.dumps(args.func(args), ensure_ascii=False, indent=2))
        return 0
    except PianoBgmError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
