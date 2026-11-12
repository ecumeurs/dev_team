#!/usr/bin/env bash
# Turn the dev_team agent set ON for all supported harnesses:
#   ~/.config/opencode/agents -> repo agents/        (OpenCode dialect)
#   ~/.claude/agents          -> repo claude-agents/ (Claude Code dialect)
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
# Also installs cve-watch, the mechanical side of security-advisor's
# dependency-security guardrail: ~/.local/bin/cve-watch -> scripts/cve-watch.py
# and the user timer systemd/cve-watch.{service,timer}, linked into
# ~/.config/systemd/user and enabled. Like references, hookoff.sh leaves it in
# place: it is a daily scan, not team presence. It needs osv-scanner (see the
# README); without it setup still links everything and says so.
#
# Also installs doc-ids, the numbering of the spec and UI/UX trees' registers
# (next free ID, duplicate lint, cross-branch compare, renumber):
# ~/.local/bin/doc-ids -> scripts/doc-ids.py. hookoff.sh leaves it in place.
#
# Also installs doc-get, the reading side of the same trees (one chunk, spec
# section, register entry, atom or design item, or a chunk's pack):
# ~/.local/bin/doc-get -> scripts/doc-get.py. hookoff.sh leaves it in place.
#
# Also installs agent-stats, a chunk's or a wave's figures from the session
# transcripts (tool calls, tokens, largest context, cost, split by role, chunk
# and activity): ~/.local/bin/agent-stats -> scripts/agent-stats.py.
# hookoff.sh leaves it in place.
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

  if [ ! -e "$src" ]; then
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

# Codex support was dropped. Remove the ~/.codex/agents link an earlier setup
# placed, but only if it still points into this repo.
if [ -L "$HOME/.codex/agents" ]; then
  case "$(readlink "$HOME/.codex/agents")" in
    "$REPO_DIR/codex-agents"*)
      rm "$HOME/.codex/agents"
      echo "Codex: removed legacy link $HOME/.codex/agents (Codex is no longer supported)"
      ;;
  esac
fi

# doc-ids: the command the writers take register IDs from.
ensure_link "$REPO_DIR/scripts/doc-ids.py"       "$HOME/.local/bin/doc-ids"                     "doc-ids"         || failed=1

# doc-get: the command every agent reads the trees' targeted pieces with.
ensure_link "$REPO_DIR/scripts/doc-get.py"       "$HOME/.local/bin/doc-get"                     "doc-get"         || failed=1

# agent-stats: the wave driver's figures for each chunk and wave.
ensure_link "$REPO_DIR/scripts/agent-stats.py"   "$HOME/.local/bin/agent-stats"                 "agent-stats"     || failed=1

# cve-watch: the command the advisor's skills call, and the daily timer.
ensure_link "$REPO_DIR/scripts/cve-watch.py"     "$HOME/.local/bin/cve-watch"                   "cve-watch"       || failed=1
ensure_link "$REPO_DIR/systemd/cve-watch.service" "$HOME/.config/systemd/user/cve-watch.service" "cve-watch:unit"  || failed=1
ensure_link "$REPO_DIR/systemd/cve-watch.timer"   "$HOME/.config/systemd/user/cve-watch.timer"   "cve-watch:timer" || failed=1
if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  systemctl --user daemon-reload
  if systemctl --user enable --now cve-watch.timer >/dev/null 2>&1; then
    echo "cve-watch:timer: enabled ($(systemctl --user show cve-watch.timer -p NextElapseUSecRealtime --value | sed 's/^$/next run pending/'))"
  else
    echo "cve-watch:timer: could not enable cve-watch.timer; run: systemctl --user enable --now cve-watch.timer" >&2
    failed=1
  fi
else
  echo "cve-watch:timer: no systemd user session; enable it later with: systemctl --user enable --now cve-watch.timer" >&2
fi
if ! command -v osv-scanner >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/osv-scanner" ]; then
  echo "cve-watch: osv-scanner is missing; install it with:" >&2
  echo "  GOBIN=\$HOME/.local/bin go install github.com/google/osv-scanner/v2/cmd/osv-scanner@latest" >&2
fi

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
  echo "dev_team agents are now live for OpenCode and Claude Code:"
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
