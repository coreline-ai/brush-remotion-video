#!/usr/bin/env python3
"""Mechanical QA for the curated v0.4 60-scene asset set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "examples/cosmic-random-brush-v04/assets/manifest.json"
REPORT = ROOT / "data/cosmic-random-brush-v04-assets-review/asset-qa-report.json"
GOLDEN = ROOT / "examples/cosmic-random-brush-v03/assets/scene-01-earth-orbit-sunrise.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    checks: list[dict] = []
    hashes: list[str] = []
    for entry in manifest["scenes"]:
        path = ROOT / entry["file"]
        size = Image.open(path).size if path.is_file() else None
        actual_hash = sha256(path) if path.is_file() else None
        flags = entry.get("manualQuality") or {}
        passed = bool(
            size == (1920, 1080)
            and actual_hash == entry.get("normalizedSha256")
            and float(entry.get("sourceRetention", 0)) >= 0.88
            and all(flags.get(key) is True for key in (
                "subjectFullyVisible", "recognizableAtContactSheetSize",
                "noDiagramOrEmbeddedLabels", "noMultiPanelCollage"))
        )
        if not passed:
            failures.append(f"scene-{entry['scene']:02d}: asset contract")
        hashes.append(actual_hash or "")
        checks.append({"scene": entry["scene"], "file": entry["file"], "size": size,
                       "hash": actual_hash, "composition": entry["composition"],
                       "sourceRetention": entry["sourceRetention"], "pass": passed})
    if len(checks) != 60:
        failures.append(f"scene count {len(checks)} != 60")
    if len(set(hashes)) != 60:
        failures.append("normalized hashes are not unique")
    scene1 = ROOT / manifest["scenes"][0]["file"]
    golden_equal = scene1.read_bytes() == GOLDEN.read_bytes()
    if not golden_equal:
        failures.append("scene-01 is not byte-identical to golden source")
    result = {
        "projectId": manifest["projectId"],
        "pass": not failures,
        "sceneCount": len(checks),
        "uniqueHashes": len(set(hashes)),
        "goldenScene01ByteIdentical": golden_equal,
        "replacementCount": sum(bool(e.get("replacedV03Source")) for e in manifest["scenes"]),
        "compositionCounts": {
            kind: sum(e["composition"] == kind for e in manifest["scenes"])
            for kind in sorted({e["composition"] for e in manifest["scenes"]})
        },
        "failures": failures,
        "scenes": checks,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("pass", "sceneCount", "uniqueHashes",
                                             "goldenScene01ByteIdentical", "replacementCount",
                                             "compositionCounts", "failures")},
                     ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
