"""stt.py — 더빙 오디오 → 로컬 whisper → SRT.

기존 new-video-gen 의 .venv-whisper 를 재사용한다 (부재 시 설치 안내 에러).
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

WHISPER_BIN = Path("/Users/hwanchoi/project_202606/new-video-gen/.venv-whisper/bin/whisper")


def transcribe(audio_path: str | Path, out_dir: str | Path, *, model: str = "small",
               language: str = "ko", whisper_bin: str | Path | None = None) -> Path:
    """whisper CLI 로 SRT 생성. 반환: 생성된 SRT 경로."""
    wb = Path(whisper_bin) if whisper_bin is not None else WHISPER_BIN
    if not wb.is_file():
        raise RuntimeError(
            f"whisper 바이너리 없음: {wb}\n"
            "설치 안내: python3.11 -m venv .venv-whisper && "
            ".venv-whisper/bin/pip install openai-whisper"
        )
    audio_path = Path(audio_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(wb), str(audio_path), "--model", model, "--language", language,
           "--output_format", "srt", "--output_dir", str(out_dir), "--fp16", "False"]
    log.info("$ %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    srt = out_dir / f"{audio_path.stem}.srt"
    if not srt.is_file():
        raise RuntimeError(f"whisper 실행 후 SRT 미생성: {srt}")
    return srt
