#!/usr/bin/env bash
# Turn the dev_team agent set ON for all supported harnesses:
#   ~/.config/opencode/agents -> repo agents/        (OpenCode dialect)
#   ~/.claude/agents          -> repo claude-agents/ (Claude Code dialect)
#   ~/.codex/agents           -> repo codex-agents/  (Codex custom agents)
# Idempotent. hookoff.sh removes them again.
#
# Also publishes references/ to ~/.local/share/dev_team/references, the stable
# path the personas cite for shared reference docs (software-quality
# principles, the access-model layout). Agent personas read those same files,
# so that link is deliberately NOT removed by hookoff.sh — see the note there.
#
# Also symlinks each skills/<name> subdirectory into ~/.claude/skills/<name>,
# one skill at a time (never the whole skills/ directory onto ~/.claude/skills
# itself, which may hold skills dev_team doesn't manage). OpenCode discovers
# ~/.claude/skills natively, so this single location covers both harnesses.
# Unlike references, hookoff.sh DOES remove these links again — skills are
# active automation an agent invokes, not inert reference docs.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
failed=0

# ensure_link <src> <dst> <label>
# Idempotent symlink. Refuses to clobber real (non-symlink) content.
ensure_link() {
  local src="$1" dst="$2" label="$3"

  if [ ! -d "$src" ]; then
    echo "Warning: $src does not exist; skipping $label." >&2
    return 0
  fi

  mkdir -p "$(dirname "$dst")"

  if [ -L "$dst" ]; then
    if [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ]; then
      echo "$label: already linked ($dst -> $src)"
      return 0
    fi
    echo "$label: symlink points elsewhere ($(readlink -f "$dst")); replacing."
    rm "$dst"
  elif [ -e "$dst" ]; then
    echo "$label: refusing to touch $dst — it exists and is not a symlink." >&2
    echo "  Move it aside manually if you want dev_team to manage it." >&2
    return 1
  fi

  ln -s "$src" "$dst"
  echo "$label: linked $dst -> $src"
}

ensure_link "$REPO_DIR/references"    "$HOME/.local/share/dev_team/references" "References"   || failed=1
ensure_link "$REPO_DIR/agents"        "$HOME/.config/opencode/agents"          "OpenCode"     || failed=1
ensure_link "$REPO_DIR/claude-agents" "$HOME/.claude/agents"                   "Claude Code"  || failed=1
ensure_link "$REPO_DIR/codex-agents"  "$HOME/.codex/agents"                    "Codex"        || failed=1

# Prune links left behind by a renamed or removed skill: a symlink in
# ~/.claude/skills that points into this repo's skills/ directory at a skill
# that no longer exists (e.g. atd-gating-protocol, renamed to
# intent-gating-protocol). Links pointing anywhere else are never touched.
for link in "$HOME/.claude/skills"/*; do
  [ -L "$link" ] || continue
  target="$(readlink "$link")"
  case "$target" in
    "$REPO_DIR/skills/"*) ;;
    *) continue ;;
  esac
  if [ ! -e "$link" ]; then
    rm "$link"
    echo "Skill:$(basename "$link"): removed stale link (was -> $target)"
  fi
done

# Skills are symlinked one subdirectory at a time into ~/.claude/skills, never
# as a whole-directory link onto ~/.claude/skills itself — that location can
# hold skills dev_team doesn't manage (e.g. hand-installed ones), and a
# parent-directory symlink would either clobber them or refuse to link at all.
# OpenCode natively discovers ~/.claude/skills too, so this one location covers
# both OpenCode and Claude Code without a separate OpenCode-specific target.
if [ -d "$REPO_DIR/skills" ]; then
  for skill_dir in "$REPO_DIR/skills"/*/; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    ensure_link "${skill_dir%/}" "$HOME/.claude/skills/$name" "Skill:$name" || failed=1
  done
fi

if [ "$failed" -eq 0 ]; then
  echo
  echo "dev_team agents are now live for OpenCode, Claude Code, and Codex:"
  names=()
  for f in "$REPO_DIR/agents"/*.md; do
    [ -e "$f" ] || continue
    n="${f##*/}"
    names+=("${n%.md}")
  done
  printf '%s\n' "${names[@]}" | paste -sd, - | sed 's/,/, /g' | fold -sw 74 | sed 's/^/  /'
  if [ -d "$REPO_DIR/skills" ]; then
    skill_names=()
    for d in "$REPO_DIR/skills"/*/; do
      [ -d "$d" ] || continue
      skill_names+=("$(basename "$d")")
    done
    if [ "${#skill_names[@]}" -gt 0 ]; then
      echo
      echo "Skills linked into ~/.claude/skills (also discovered by OpenCode):"
      printf '%s\n' "${skill_names[@]}" | paste -sd, - | sed 's/,/, /g' | fold -sw 74 | sed 's/^/  /'
    fi
  fi
else
  echo >&2
  echo "One or more links could not be established; see above." >&2
  exit 1
fi
