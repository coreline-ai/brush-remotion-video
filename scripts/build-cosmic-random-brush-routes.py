#!/usr/bin/env python3
"""승인 데모 호환 래퍼 — 실제 로직은 brushvid.cosmic_random_routes가 유일한 소스다."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from brushvid.cosmic_random_routes import (  # noqa: E402
    CosmicRandomRouteParams,
    build_route_mask,
    generate_cosmic_random_routes,
    route_report,
    write_cosmic_random_routes,
)

PUBLIC = ROOT / "public" / "cosmic-dark-pilot"
DATA = ROOT / "data" / "cosmic-dark-pilot" / "random-brush"
SOURCE = PUBLIC / "luminous.png"
OUT = PUBLIC / "random-brush-routes.json"
MASK_OUT = DATA / "route-mask.png"
REPORT_OUT = DATA / "route-report.json"


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    data = generate_cosmic_random_routes(
        SOURCE,
        image_rel="cosmic-dark-pilot/luminous.png",
        params=CosmicRandomRouteParams(seed=260712),
    )
    write_cosmic_random_routes(data, OUT)
    build_route_mask(data["strokes"], data["meta"]["width"], data["meta"]["height"]).save(MASK_OUT)
    report = {**route_report(data), "routes": str(OUT.relative_to(ROOT))}
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
