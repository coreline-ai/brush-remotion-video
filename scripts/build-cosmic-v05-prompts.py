#!/usr/bin/env python3
"""Build 60 production image prompts from the locked master scene specification."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/cosmic-fullscreen-60-scene-master-spec.md"
OUT = ROOT / "examples/cosmic-fullscreen-v05/prompts.json"

ROW = re.compile(r"^\|\s*(\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def main() -> int:
    scenes = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        scene = int(match.group(1))
        title = match.group(2).strip()
        required = match.group(3).strip()
        forbidden = match.group(4).strip()
        chapter_style = {
            0: "indigo, ultramarine, charcoal, mineral white, and restrained warm gold",
            1: "charcoal, iron gray, rust red, ochre, mineral white, and deep indigo",
            2: "charcoal, muted ochre, pale gold, mineral white, teal, and deep blue",
            3: "indigo, teal, mineral white, muted crimson, violet, and restrained gold",
            4: "indigo-black, mineral white, muted crimson, ochre, teal, and violet",
            5: "indigo-black, mineral white, ultramarine, teal, restrained violet, and warm gold",
        }[(scene - 1) // 10]
        prompt = f"""Use case: stylized-concept
Asset type: scene {scene:02d} production image for a 1920x1080 Remotion space video
Primary request: Create '{title}' as a realistic-form Korean ink-and-mineral-pigment painting. Astronomical form, proportions, perspective, and identifying scientific structure must remain accurate and immediately recognizable, but the image surface and material must be 100 percent hand-painted ink wash, never a photograph or CGI image with a filter.
Required scene: {required}
Style/medium: traditional Korean sumukhwa on dark indigo-dyed hanji, layered translucent ink wash, wet-on-wet ink blooms, expressive dry-brush contours, long natural brush strokes, visible paper fibers, mineral-pigment granulation, hand-painted irregularities. Use a restrained palette of {chapter_style}. Stars are mineral-white pigment dots and natural ink splatter, not a photographic starfield. Bright light is white-pigment bloom and dry-brush radiance, never lens flare.
Composition/framing: exact landscape 16:9 full bleed; one continuous coherent painted scene naturally reaches all four edges; every required main subject is completely visible with at least 8 percent safe margin; no key object may touch or leave the frame; use the entire canvas rather than placing a small picture inside a background.
Lighting/mood: deep quiet indigo-black space, restrained mineral-pigment highlights, monumental and contemplative, strong subject separation created by ink density and pigment bloom.
Constraints: the first impression must be 'space painted with brush, ink, mineral color, and hanji.' Preserve recognizable scientific structure. No text, labels, watermark, logo, UI, infographic, collage, split screen, inset, rectangular panel, border, letterbox, pillarbox, black bars, blurred duplicate background, or square source pasted into a wide background.
Avoid: {forbidden}; photorealistic astrophotography; photograph; NASA-photo look; CGI; 3D render; glossy digital sphere; HDR; digital VFX; neon glow; lens flare; razor-sharp photo stars; filter-over-photo appearance; white-paper traditional landscape; cropped subjects; empty filler bands; oversaturated fantasy art; low resolution; visible seams."""
        scenes.append({"scene": scene, "title": title, "required": required,
                       "forbidden": forbidden, "prompt": prompt})
    if [s["scene"] for s in scenes] != list(range(1, 61)):
        raise ValueError(f"master spec did not yield scenes 1..60: {[s['scene'] for s in scenes]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"version": "v0.5-fullscreen-realistic-ink-v1", "scenes": scenes},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
