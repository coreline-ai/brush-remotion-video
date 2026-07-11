#!/usr/bin/env python3
"""골든 스틸 픽셀 diff 게이트.

baseline 디렉토리의 각 PNG를 candidate 디렉토리의 동명 파일과 비교해
평균 채널 오차(%)가 임계값(기본 2%)을 넘으면 실패(exit 1)한다.

사용:
  python3 tests/golden/diff.py --baseline tests/golden/baseline --candidate <dir>
  python3 tests/golden/diff.py --baseline ... --candidate ... --update   # 의도적 변경 시 기준 갱신
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def mean_diff_pct(a: Path, b: Path) -> float:
    ia = np.asarray(Image.open(a).convert("RGB"), dtype=np.float32)
    ib = np.asarray(Image.open(b).convert("RGB"), dtype=np.float32)
    if ia.shape != ib.shape:
        return 100.0
    return float(np.abs(ia - ib).mean() / 255.0 * 100.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--threshold", type=float, default=2.0)
    ap.add_argument("--update", action="store_true", help="candidate를 새 기준으로 복사 (의도적 변경 시에만)")
    args = ap.parse_args()

    frames = sorted(args.baseline.glob("*.png"))
    if not frames:
        print(f"FAIL: baseline에 PNG가 없음: {args.baseline}")
        return 1

    if args.update:
        for f in frames:
            src = args.candidate / f.name
            if src.exists():
                shutil.copy2(src, f)
                print(f"updated: {f.name}")
        return 0

    failed = False
    for f in frames:
        cand = args.candidate / f.name
        if not cand.exists():
            print(f"FAIL {f.name}: candidate 파일 없음")
            failed = True
            continue
        pct = mean_diff_pct(f, cand)
        ok = pct <= args.threshold
        print(f"{'PASS' if ok else 'FAIL'} {f.name}: {pct:.3f}% (임계 {args.threshold}%)")
        failed = failed or not ok

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
