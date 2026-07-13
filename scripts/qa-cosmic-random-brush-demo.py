#!/usr/bin/env python3
"""Compatibility QA entrypoint for the approved cosmic random-brush demo.

The profile QA and golden contract now live in the production pipeline. Keep
this legacy command as a thin wrapper so there is no second QA implementation
that can drift from ``brushvid.qa``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/cosmic-random-brush/project.yaml"
GOLDEN_CHECK = ROOT / "tests/golden/cosmic-random-brush/check.py"


def main() -> int:
    python = ROOT / "pipeline/.venv/bin/python"
    executable = str(python if python.is_file() else Path(sys.executable))
    subprocess.run(
        [executable, str(ROOT / "bin/build.py"), str(EXAMPLE), "--from", "qa", "--audit"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([executable, str(GOLDEN_CHECK)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
