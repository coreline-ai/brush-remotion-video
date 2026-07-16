#!/usr/bin/env python3
"""TTS 환경 점검·명시적 준비 도구.

`--check`는 network와 모델 다운로드를 사용하지 않는다. 패키지 설치와
Hugging Face snapshot 준비는 사용자가 명시적으로 `--prepare`를 요청한
경우에만 실행한다.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
VENV_PY = PIPELINE / ".venv" / "bin" / "python"
ENGINES = ("supertonic", "melo-ko", "qwen3-base")
MODEL_IDS = {
    "melo-ko": "myshell-ai/MeloTTS-Korean",
    "qwen3-base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}
MODEL_REVISIONS = {
    "melo-ko": "0207e5adfc90129a51b6b03d89be6d84360ed323",
    "qwen3-base": "fd4b254389122332181a7c3db7f27e918eec64e3",
}
EXTRAS = {"supertonic": "tts", "melo-ko": "tts-melo", "qwen3-base": "tts-qwen"}


def selected_python(engine: str) -> Path:
    if engine == "qwen3-base" and os.environ.get("BRUSHVID_QWEN_PYTHON"):
        return Path(os.environ["BRUSHVID_QWEN_PYTHON"]).expanduser()
    return VENV_PY


def snapshot_path(engine: str) -> Path:
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    return (
        hf_home / "hub" / f"models--{MODEL_IDS[engine].replace('/', '--')}"
        / "snapshots" / MODEL_REVISIONS[engine]
    )


def run(command: list[str]) -> int:
    print("$", " ".join(command))
    return subprocess.run(command, cwd=ROOT).returncode


def check_engine(engine: str) -> bool:
    python = selected_python(engine)
    ok = True
    if not python.is_file():
        print(f"FAIL {engine}: Python 없음: {python}")
        return False
    if shutil.which("ffmpeg") is None:
        print(f"FAIL {engine}: ffmpeg 없음")
        ok = False
    snapshot = snapshot_path(engine) if engine != "supertonic" else None
    if snapshot is not None:
        required = ("config.json", "checkpoint.pth") if engine == "melo-ko" else ()
        if not snapshot.is_dir() or any(not (snapshot / name).is_file() for name in required):
            print(f"FAIL {engine}: pinned model snapshot 없음: {snapshot}")
            ok = False
        else:
            print(f"PASS {engine}: pinned snapshot {MODEL_REVISIONS[engine]}")
    probes = {
        "supertonic": "import supertonic; print(supertonic.__version__)",
        "melo-ko": "import melo.api; print('melo import ok')",
        "qwen3-base": "import qwen_tts; print('qwen import ok')",
    }
    result = subprocess.run(
        [str(python), "-c", probes[engine]], cwd=ROOT,
        capture_output=True, text=True,
    )
    if result.returncode:
        print(f"FAIL {engine}: import 실패: {result.stderr.strip()[-400:]}")
        ok = False
    else:
        print(f"PASS {engine}: {result.stdout.strip()}")
    if engine == "melo-ko":
        check = subprocess.run([str(python), "-m", "pip", "check"], cwd=ROOT)
        ok = ok and check.returncode == 0
    return ok


def prepare_engine(engine: str) -> int:
    python = selected_python(engine)
    if not python.is_file():
        print(f"Python 없음: {python}", file=sys.stderr)
        return 1
    extra = ROOT / "pipeline"
    status = run([str(python), "-m", "pip", "install", "-e", f"{extra}[{EXTRAS[engine]}]"])
    if status:
        return status
    if engine == "melo-ko":
        status = run([str(python), "-m", "unidic", "download"])
        if status:
            return status
    if engine in MODEL_IDS:
        code = (
            "from huggingface_hub import snapshot_download; "
            f"snapshot_download(repo_id={MODEL_IDS[engine]!r}, "
            f"revision={MODEL_REVISIONS[engine]!r})"
        )
        status = run([str(python), "-c", code])
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", choices=ENGINES, nargs="?", const="all")
    group.add_argument("--prepare", choices=ENGINES)
    args = parser.parse_args()
    if args.prepare:
        return prepare_engine(args.prepare)
    targets = ENGINES if args.check == "all" else (args.check,)
    statuses = [check_engine(engine) for engine in targets]
    return 0 if all(statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
