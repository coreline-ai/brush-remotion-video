#!/usr/bin/env python3
"""Validate the production cosmic-random-brush render against its golden contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent


def _mean_diff_pct(left: Path, right: Path) -> float:
    a = np.asarray(Image.open(left).convert("RGB"), dtype=np.float32)
    b = np.asarray(Image.open(right).convert("RGB"), dtype=np.float32)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} != {b.shape}")
    return float(np.abs(a - b).mean() / 255.0 * 100.0)


def _geometry_hash(routes: dict) -> str:
    geometry = [
        {
            "id": stroke["id"],
            "width": stroke["width"],
            "start": stroke["start"],
            "end": stroke["end"],
            "opacity": stroke["opacity"],
            "dryness": stroke["dryness"],
            "points": stroke["points"],
        }
        for stroke in routes["strokes"]
    ]
    encoded = json.dumps(
        geometry,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        type=Path,
        default=ROOT / "data/cosmic-random-brush-golden/qa",
        help="Directory containing rendered frame-*.png files.",
    )
    parser.add_argument(
        "--routes",
        type=Path,
        default=ROOT
        / "public/cosmic-random-brush-golden/routes/scene-01.routes.json",
    )
    args = parser.parse_args()

    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    production = manifest["production"]
    threshold = float(production["goldenFrameThresholdPct"])
    failures: list[str] = []

    print(f"Golden frame threshold: {threshold:.3f}%")
    for frame in manifest["frames"]:
        name = f"frame-{frame:05d}.png"
        baseline = FIXTURE / "baseline" / name
        candidate = args.candidate / name
        if not candidate.is_file():
            failures.append(f"missing candidate: {candidate}")
            continue
        diff = _mean_diff_pct(baseline, candidate)
        verdict = "PASS" if diff <= threshold else "FAIL"
        print(f"{verdict} {name}: {diff:.3f}%")
        if diff > threshold:
            failures.append(f"{name}: {diff:.3f}% > {threshold:.3f}%")

    if not args.routes.is_file():
        failures.append(f"missing routes: {args.routes}")
    else:
        routes = json.loads(args.routes.read_text())
        actual_hash = _geometry_hash(routes)
        expected_hash = production["geometrySha256"]
        verdict = "PASS" if actual_hash == expected_hash else "FAIL"
        print(f"{verdict} geometry sha256: {actual_hash}")
        if actual_hash != expected_hash:
            failures.append(
                f"geometry sha256: {actual_hash} != expected {expected_hash}"
            )

        expected = production["routeMetrics"]
        meta = routes["meta"]
        checks = {
            "family": meta["family"] == expected["family"],
            "seed": meta["seed"] == expected["seed"],
            "deterministic": meta["deterministic"] is True,
            "strokeCount": len(routes["strokes"]) == expected["strokeCount"],
            "baseStrokeCount": meta["baseStrokeCount"]
            == expected["baseStrokeCount"],
            "coverageStrokeCount": meta["coverageStrokeCount"]
            == expected["coverageStrokeCount"],
            "maskCoverage": meta["maskCoverage"]
            >= expected["targetMaskCoverage"],
        }
        for name, ok in checks.items():
            print(f"{'PASS' if ok else 'FAIL'} route metric: {name}")
            if not ok:
                failures.append(f"route metric failed: {name}")

    if failures:
        print("\nGolden contract failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nGolden contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
