#!/bin/bash
# 스킬 2종을 ~/.claude/skills/ 에 symlink로 설치한다.
# 사본이 아니라 symlink — 리포가 유일한 소스 (드리프트 방지 제1원칙).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
mkdir -p "$SKILLS_DIR"

install_link() {
  local src="$1" name="$2" dst="$SKILLS_DIR/$2"
  if [ -L "$dst" ]; then rm "$dst"
  elif [ -e "$dst" ]; then echo "경고: $dst 가 symlink가 아닌 실체로 존재 — 건너뜀 (수동 확인 필요)"; return
  fi
  ln -s "$src" "$dst"
  echo "설치: $dst -> $src"
}

install_link "$REPO/skill/brush-video" "brush-video"
install_link "$REPO/skill/qa-review" "brush-qa-review"
install_link "$REPO/skill/director" "brush-director"
install_link "$REPO/skill/pen-video" "pen-video"
