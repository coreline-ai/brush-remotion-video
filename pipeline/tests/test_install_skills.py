from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "bin" / "install-skills.sh"
SKILL_IDS = {
    "brush-director",
    "brush-video",
    "pen-video",
    "pen-brush-video",
    "shorts-brush",
    "dark-random-brush-video",
    "storybook-full-touch-video",
    "brush-qa-review",
    "video-auditor",
}


def _run(home: Path, *args: str, check: bool = True):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("CODEX_HOME", None)
    return subprocess.run(
        ["bash", str(INSTALLER), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


def _links(path: Path):
    return {entry.name for entry in path.iterdir() if entry.is_symlink()}


def test_no_arg_preserves_claude_default_and_migrates_broken_legacy(tmp_path: Path):
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    (claude / "cosmic-random-brush-video").symlink_to("/missing/legacy-target")
    _run(tmp_path)
    assert _links(claude) == SKILL_IDS
    assert not (claude / "cosmic-random-brush-video").is_symlink()
    assert not (tmp_path / ".codex").exists()
    _run(tmp_path, "--check")


def test_target_all_installs_nine_to_both_and_is_idempotent(tmp_path: Path):
    first = _run(tmp_path, "--target", "all")
    second = _run(tmp_path, "--target", "all")
    assert "설치:" in first.stdout
    assert "유지:" in second.stdout
    for path in (tmp_path / ".claude" / "skills", tmp_path / ".codex" / "skills"):
        assert _links(path) == SKILL_IDS
    _run(tmp_path, "--target", "all", "--check")


def test_dry_run_does_not_write(tmp_path: Path):
    result = _run(tmp_path, "--target", "all", "--dry-run")
    assert "[dry-run]" in result.stdout
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".codex").exists()


def test_real_user_directory_is_preserved_and_check_fails(tmp_path: Path):
    destination = tmp_path / ".claude" / "skills" / "brush-video"
    destination.mkdir(parents=True)
    marker = destination / "user-owned.txt"
    marker.write_text("keep", encoding="utf-8")
    install = _run(tmp_path)
    assert marker.read_text(encoding="utf-8") == "keep"
    assert "symlink가 아닌 실체" in install.stderr
    check_result = _run(tmp_path, "--check", check=False)
    assert check_result.returncode == 1
    assert marker.read_text(encoding="utf-8") == "keep"


def test_invalid_target_and_conflicting_modes_fail_without_writing(tmp_path: Path):
    invalid = _run(tmp_path, "--target", "unknown", check=False)
    conflict = _run(tmp_path, "--dry-run", "--check", check=False)
    assert invalid.returncode == 2
    assert conflict.returncode == 2
    assert not (tmp_path / ".claude").exists()
