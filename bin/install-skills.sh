#!/bin/bash
# 리포의 얇은 스킬을 Claude/Codex에 symlink로 설치한다.
# 사본이 아니라 symlink — 리포와 skill/catalog.json이 유일한 소스다.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CATALOG_CLI="$REPO/bin/skill-catalog.py"
# 로컬 venv symlink 대상이 삭제된 경우(-x는 true지만 실행은 실패)에도
# catalog 설치가 막히지 않도록 실제 실행 가능 여부까지 확인한다.
if [ -x "$REPO/pipeline/.venv/bin/python" ] \
  && "$REPO/pipeline/.venv/bin/python" -c 'import sys' >/dev/null 2>&1; then
  PYTHON_BIN="$REPO/pipeline/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi
TARGET="claude"
DRY_RUN=false
CHECK_ONLY=false

usage() {
  cat <<'EOF'
사용법: bin/install-skills.sh [--target claude|codex|all] [--dry-run|--check]

옵션:
  --target TARGET  설치 대상. 기본값은 하위 호환을 위해 claude.
  --dry-run        파일을 변경하지 않고 예정 작업만 출력.
  --check          파일을 변경하지 않고 catalog 스킬 설치 상태를 검사.
  -h, --help       도움말.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      [ "$#" -ge 2 ] || { echo "오류: --target 값이 필요함" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --target=*)
      TARGET="${1#*=}"
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --check)
      CHECK_ONLY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "오류: 알 수 없는 옵션: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  claude|codex|all) ;;
  *) echo "오류: target은 claude|codex|all 중 하나여야 함: $TARGET" >&2; exit 2 ;;
esac

if $DRY_RUN && $CHECK_ONLY; then
  echo "오류: --dry-run과 --check는 함께 사용할 수 없음" >&2
  exit 2
fi

"$PYTHON_BIN" "$CATALOG_CLI" validate >/dev/null

target_dir() {
  case "$1" in
    claude) printf '%s\n' "$HOME/.claude/skills" ;;
    codex) printf '%s\n' "${CODEX_HOME:-$HOME/.codex}/skills" ;;
  esac
}

targets() {
  if [ "$TARGET" = "all" ]; then
    printf '%s\n' claude codex
  else
    printf '%s\n' "$TARGET"
  fi
}

legacy_aliases() {
  "$PYTHON_BIN" - "$REPO/skill/catalog.json" <<'PY'
import json, sys
catalog = json.load(open(sys.argv[1], encoding="utf-8"))
for alias in catalog["legacyInstallAliases"]:
    print(f"{alias['id']}\t{alias['replacement']}")
PY
}

remove_legacy_links() {
  local skills_dir="$1" legacy_id replacement legacy_path
  while IFS=$'\t' read -r legacy_id replacement; do
    [ -n "$legacy_id" ] || continue
    legacy_path="$skills_dir/$legacy_id"
    if [ -L "$legacy_path" ]; then
      if $DRY_RUN; then
        echo "[dry-run] 이전 symlink 제거: $legacy_path (대체: $replacement)"
      else
        rm "$legacy_path"
        echo "이전 symlink 제거: $legacy_path (대체: $replacement)"
      fi
    elif [ -e "$legacy_path" ]; then
      echo "경고: $legacy_path 가 symlink가 아닌 실체로 존재 — 유지함" >&2
    fi
  done < <(legacy_aliases)
}

install_link() {
  local source="$1" skill_id="$2" skills_dir="$3" destination="$skills_dir/$skill_id" current
  if [ -L "$destination" ]; then
    current="$(readlink "$destination")"
    if [ "$current" = "$source" ]; then
      echo "유지: $destination -> $source"
      return
    fi
    if $DRY_RUN; then
      echo "[dry-run] symlink 교체: $destination ($current -> $source)"
      return
    fi
    rm "$destination"
  elif [ -e "$destination" ]; then
    echo "경고: $destination 가 symlink가 아닌 실체로 존재 — 건너뜀" >&2
    return
  fi

  if $DRY_RUN; then
    echo "[dry-run] 설치: $destination -> $source"
  else
    ln -s "$source" "$destination"
    echo "설치: $destination -> $source"
  fi
}

check_target() {
  local label="$1" skills_dir="$2" failures=0 skill_id source destination current legacy_id replacement legacy_path
  if [ ! -d "$skills_dir" ]; then
    echo "FAIL [$label] 설치 디렉터리 없음: $skills_dir" >&2
    return 1
  fi
  while IFS=$'\t' read -r skill_id source; do
    [ -n "$skill_id" ] || continue
    destination="$skills_dir/$skill_id"
    if [ ! -L "$destination" ]; then
      echo "FAIL [$label] symlink 누락: $destination" >&2
      failures=$((failures + 1))
      continue
    fi
    current="$(readlink "$destination")"
    if [ "$current" != "$source" ]; then
      echo "FAIL [$label] 대상 불일치: $destination -> $current (기대: $source)" >&2
      failures=$((failures + 1))
      continue
    fi
    if [ ! -e "$destination" ]; then
      echo "FAIL [$label] broken symlink: $destination -> $current" >&2
      failures=$((failures + 1))
      continue
    fi
    echo "PASS [$label] $skill_id"
  done < <("$PYTHON_BIN" "$CATALOG_CLI" emit-install)

  while IFS=$'\t' read -r legacy_id replacement; do
    [ -n "$legacy_id" ] || continue
    legacy_path="$skills_dir/$legacy_id"
    if [ -L "$legacy_path" ] || [ -e "$legacy_path" ]; then
      echo "FAIL [$label] legacy 경로 잔존: $legacy_path (대체: $replacement)" >&2
      failures=$((failures + 1))
    fi
  done < <(legacy_aliases)

  [ "$failures" -eq 0 ] || return 1
  skill_count="$("$PYTHON_BIN" -c "import json; from pathlib import Path; print(len(json.loads(Path(r'$REPO/skill/catalog.json').read_text())['skills']))")"
  echo "PASS [$label] catalog skills ${skill_count}/${skill_count}"
}

if $CHECK_ONLY; then
  result=0
  while IFS= read -r label; do
    skills_dir="$(target_dir "$label")"
    check_target "$label" "$skills_dir" || result=1
  done < <(targets)
  exit "$result"
fi

while IFS= read -r label; do
  skills_dir="$(target_dir "$label")"
  if $DRY_RUN; then
    echo "[dry-run] 대상: $label ($skills_dir)"
  else
    mkdir -p "$skills_dir"
    echo "대상: $label ($skills_dir)"
  fi
  remove_legacy_links "$skills_dir"
  while IFS=$'\t' read -r skill_id source; do
    [ -n "$skill_id" ] || continue
    install_link "$source" "$skill_id" "$skills_dir"
  done < <("$PYTHON_BIN" "$CATALOG_CLI" emit-install)
done < <(targets)
