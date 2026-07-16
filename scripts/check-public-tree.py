#!/usr/bin/env python3
"""공개 Git tree가 fresh clone에서 약속한 자산·예제·문서를 갖췄는지 검사한다."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ASSET_PROJECTS = {
    "examples/cosmic-random-brush/project.yaml",
    "examples/cosmic-random-brush-v02/project.yaml",
    "examples/cosmic-random-brush-v03/project.yaml",
    "examples/cosmic-random-brush-v05-ink/project.yaml",
    "examples/deepsea-light-v01/project.yaml",
    "examples/tts-qwen/project.yaml",
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def tracked_files() -> set[str]:
    output = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
    )
    return {item.decode("utf-8") for item in output.split(b"\0") if item}


def repo_relative(base: Path, raw: str) -> str | None:
    resolved = (base / raw).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return None


def project_inputs(project_path: Path) -> list[str]:
    payload = yaml.safe_load(project_path.read_text(encoding="utf-8")) or {}
    refs: list[str] = []
    input_block = payload.get("input") or {}
    for key in ("srt", "audio", "script"):
        value = input_block.get(key)
        if isinstance(value, str) and value:
            refs.append(value)
    background = payload.get("background") or {}
    images = background.get("images") or []
    refs.extend(value for value in images if isinstance(value, str) and value)
    tts = input_block.get("tts") or {}
    reference = tts.get("reference") if isinstance(tts, dict) else None
    if isinstance(reference, dict):
        refs.extend(
            value for value in (reference.get("audio"), reference.get("transcript"))
            if isinstance(value, str) and value
        )
    return refs


def check_voice_previews(tracked: set[str], errors: list[str]) -> int:
    catalog = json.loads((ROOT / "assets/voices/catalog.json").read_text(encoding="utf-8"))
    count = 0
    for voice in catalog["voices"]:
        preview = voice["preview"]
        relative = preview["path"]
        path = ROOT / relative
        count += 1
        if relative not in tracked:
            errors.append(f"voice preview가 Git에 없음: {relative}")
            continue
        if not path.is_file():
            errors.append(f"voice preview 파일 없음: {relative}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != preview["sha256"]:
            errors.append(f"voice preview SHA-256 불일치: {relative}")
    return count


def check_examples(tracked: set[str], errors: list[str]) -> tuple[int, int]:
    projects = sorted(path for path in tracked if path.startswith("examples/") and path.endswith("project.yaml"))
    local_only_seen: set[str] = set()
    for relative in projects:
        path = ROOT / relative
        missing_tracked: list[str] = []
        for raw in project_inputs(path):
            target = repo_relative(path.parent, raw)
            if target is None:
                errors.append(f"저장소 밖 입력 경로: {relative}: {raw}")
            elif target not in tracked:
                missing_tracked.append(target)
        if missing_tracked:
            if relative not in LOCAL_ASSET_PROJECTS:
                errors.append(
                    f"self-contained 예제가 미추적 입력을 참조: {relative}: "
                    + ", ".join(missing_tracked[:3])
                )
            else:
                local_only_seen.add(relative)
        elif relative in LOCAL_ASSET_PROJECTS:
            errors.append(f"로컬 전용 허용 목록이 더 이상 필요 없음: {relative}")
    stale = LOCAL_ASSET_PROJECTS - set(projects)
    for relative in sorted(stale):
        errors.append(f"존재하지 않는 로컬 전용 예제 허용값: {relative}")
    if local_only_seen != LOCAL_ASSET_PROJECTS:
        missing = sorted(LOCAL_ASSET_PROJECTS - local_only_seen)
        if missing:
            errors.append("로컬 전용 계약이 확인되지 않음: " + ", ".join(missing))
    return len(projects), len(local_only_seen)


def check_markdown(tracked: set[str], errors: list[str]) -> tuple[int, int]:
    files = sorted(path for path in tracked if path.endswith(".md"))
    relative_links = 0
    for relative in files:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8", errors="ignore")
        for raw in MARKDOWN_LINK.findall(text):
            raw = raw.strip().split()[0].strip("<>")
            if raw.startswith("file://"):
                errors.append(f"공개 문서의 로컬 file URL: {relative}: {raw}")
                continue
            if not raw or raw.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_links += 1
            target = urllib.parse.unquote(raw.split("#", 1)[0].split("?", 1)[0])
            resolved = (path.parent / target).resolve()
            try:
                repo_target = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                errors.append(f"저장소 밖 Markdown 링크: {relative}: {raw}")
                continue
            is_tracked_file = repo_target in tracked
            prefix = repo_target.rstrip("/") + "/"
            is_tracked_directory = any(item.startswith(prefix) for item in tracked)
            if not is_tracked_file and not is_tracked_directory:
                errors.append(f"Git tree에 없는 Markdown 링크: {relative}: {raw}")
    return len(files), relative_links


def main() -> int:
    tracked = tracked_files()
    errors: list[str] = []
    voices = check_voice_previews(tracked, errors)
    projects, local_projects = check_examples(tracked, errors)
    markdown_files, markdown_links = check_markdown(tracked, errors)
    if errors:
        print("PUBLIC TREE FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "PUBLIC TREE PASS "
        f"voices={voices} projects={projects} localOnly={local_projects} "
        f"markdown={markdown_files}/{markdown_links}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
