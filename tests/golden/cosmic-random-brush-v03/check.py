#!/usr/bin/env python3
"""Validate the 60-scene cosmic-random-brush v0.3 production matrix."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MATRIX = Path(__file__).with_name("scene-matrix.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_hash(routes: dict) -> str:
    keys = ("id", "width", "start", "end", "opacity", "dryness", "points")
    geometry = [{key: stroke[key] for key in keys} for stroke in routes["strokes"]]
    payload = json.dumps(geometry, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes-dir", type=Path,
                        default=ROOT / "public/cosmic-random-brush-v03-60/routes")
    parser.add_argument("--qa-report", type=Path,
                        default=ROOT / "data/cosmic-random-brush-v03-60/qa/cosmic-random-brush-report.json")
    args = parser.parse_args()
    matrix = json.loads(MATRIX.read_text())
    quality = matrix["quality"]
    failures: list[str] = []
    for item in matrix["scenes"]:
        scene_id = f"scene-{item['scene']:02d}"
        source = ROOT / item["file"]
        if not source.is_file() or sha256(source) != item["normalizedSha256"]:
            failures.append(f"{scene_id}: source hash mismatch")
            continue
        route_path = args.routes_dir / f"{scene_id}.routes.json"
        if not route_path.is_file():
            failures.append(f"{scene_id}: routes missing")
            continue
        routes = json.loads(route_path.read_text())
        meta = routes["meta"]
        widths = meta.get("brushWidthRange", [0, 9999])
        checks = {
            "seed": meta.get("seed") == item["seed"],
            "base": meta.get("baseStrokeCount") == quality["baseStrokeCount"],
            "supplements": quality["coverageStrokeCountRange"][0]
            <= int(meta.get("coverageStrokeCount", -1))
            <= quality["coverageStrokeCountRange"][1],
            "brushWidth": widths[0] >= quality["brushWidthRange"][0]
            and widths[1] <= quality["brushWidthRange"][1],
            "maskCoverage": float(meta.get("maskCoverage", 0)) >= quality["maskCoverageMin"],
            "visibleContentCoverage": float(meta.get("visibleContentCoverage", 0))
            >= quality["visibleContentCoverageMin"],
            "meanJump": float(meta.get("meanCenterJump", 0)) >= quality["meanCenterJumpMin"],
            "maxJump": float(meta.get("maxCenterJump", 0)) >= quality["maxCenterJumpMin"],
            "drawEnd": float(meta.get("drawEnd", 999)) <= quality["drawEndMax"],
        }
        for name, ok in checks.items():
            if not ok:
                failures.append(f"{scene_id}: {name}")
        print(f"{'PASS' if all(checks.values()) else 'FAIL'} {scene_id} "
              f"mask={meta.get('maskCoverage')} content={meta.get('visibleContentCoverage')} "
              f"strokes={meta.get('strokeCount')}")
        if item["scene"] == 1:
            actual = geometry_hash(routes)
            expected = matrix["v01Control"]["routesGeometrySha256"]
            if actual != expected:
                failures.append(f"scene-01: geometry {actual} != {expected}")
    if not args.qa_report.is_file():
        failures.append("profile QA report missing")
    else:
        report = json.loads(args.qa_report.read_text())
        if report.get("pass") is not True or len(report.get("scenes", [])) != 60:
            failures.append("profile QA report did not pass 60 scenes")
    if failures:
        print("\nv0.3 matrix failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nv0.3 60-scene production matrix passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
