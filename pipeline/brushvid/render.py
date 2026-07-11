"""render.py — Remotion 렌더 호출 + 세그먼트 concat + ffmpeg 오디오 mux.

리포 루트에서 `npx remotion render src/index.ts <composition>` 을 서브프로세스로 구동한다.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRY = "src/index.ts"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    log.info("$ %s", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], cwd=cwd, check=True)


def render(props_path: str | Path, out_path: str | Path, *, composition: str = "BrushLandscape",
           frames: str | None = None, concurrency: int = 4,
           repo_root: str | Path = REPO_ROOT) -> Path:
    """`npx remotion render` 1회 호출. frames 는 "0-59" 형식(옵션).

    서브프로세스는 repo_root 에서 돌므로 상대 경로는 절대 경로로 변환해 넘긴다.
    """
    out = Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "remotion", "render", ENTRY, composition, str(out),
           f"--props={Path(props_path).resolve()}", f"--concurrency={concurrency}"]
    if frames:
        cmd.append(f"--frames={frames}")
    _run(cmd, cwd=Path(repo_root))
    return out


def render_segments(props_path: str | Path, out_path: str | Path, segments: list[tuple[int, int]],
                    *, composition: str = "BrushLandscape", concurrency: int = 4,
                    work_dir: str | Path | None = None, repo_root: str | Path = REPO_ROOT) -> Path:
    """프레임 구간별 세그먼트 렌더 후 concat. segments = [(start, end), ...] (inclusive)."""
    out = Path(out_path)
    work = Path(work_dir) if work_dir else out.parent / f".{out.stem}-segments"
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for i, (f0, f1) in enumerate(segments):
        part = work / f"seg-{i:03d}.mp4"
        render(props_path, part, composition=composition, frames=f"{f0}-{f1}",
               concurrency=concurrency, repo_root=repo_root)
        parts.append(part)
    return concat(parts, out)


def concat(parts: list[Path], out_path: str | Path) -> Path:
    """ffmpeg concat demuxer 로 mp4 세그먼트 무손실 이어붙임."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    list_file = out.parent / f".{out.stem}-concat.txt"
    list_file.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in parts), encoding="utf-8")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out])
    list_file.unlink(missing_ok=True)
    return out


def mux_audio(video_path: str | Path, audio_path: str | Path, out_path: str | Path,
              *, audio_bitrate: str = "192k") -> Path:
    """영상 스트림은 copy, 오디오는 AAC 인코딩으로 mux. 짧은 쪽에 맞춰 종료(-shortest)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-i", video_path, "-i", audio_path,
          "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
          "-c:a", "aac", "-b:a", audio_bitrate, "-shortest", out])
    return out


def probe_duration(media_path: str | Path) -> float:
    """ffprobe 로 미디어 길이(초)."""
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)],
        capture_output=True, text=True, check=True)
    return float(res.stdout.strip())
