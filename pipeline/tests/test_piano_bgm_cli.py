from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "bin" / "piano-bgm.py"


def test_cli_validate_and_compose_without_renderer(tmp_path: Path):
    request = tmp_path / "request.yaml"
    request.write_text("""projectId: cli-fantasy\nkind: piano-bgm\ndurationSec: 30\npreset: fantasy-piano\nkey: D-lydian\nseed: 12\n""", encoding="utf-8")
    projects, output = tmp_path / "projects", tmp_path / "output"
    command = [sys.executable, str(CLI), "--projects-root", str(projects), "--output-root", str(output)]
    checked = subprocess.run(command + ["validate", "--request", str(request)], check=True, capture_output=True, text=True)
    assert json.loads(checked.stdout)["request"]["key"] == "D-lydian"
    composed = subprocess.run(command + ["compose", "--request", str(request)], check=True, capture_output=True, text=True)
    data = json.loads(composed.stdout)
    assert data["lint"]["status"] == "PASS"
    assert (projects / "cli-fantasy" / "score.json").is_file()
