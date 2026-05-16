#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

link_skill() {
  target_root="$1"
  mkdir -p "$target_root"
  ln -sfn "$SKILL_DIR" "$target_root/ohara-review"
  printf 'Linked %s -> %s\n' "$target_root/ohara-review" "$SKILL_DIR"
}

link_skill "$HOME/.claude/skills"
link_skill "${CODEX_HOME:-$HOME/.codex}/skills"

if [ -d "$HOME/.agents" ]; then
  link_skill "$HOME/.agents/skills"
fi
