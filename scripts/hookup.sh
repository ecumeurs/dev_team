#!/usr/bin/env bash
# Turn the dev_team agent set ON for both harnesses:
#   ~/.config/opencode/agents -> repo agents/        (OpenCode dialect)
#   ~/.claude/agents          -> repo claude-agents/ (Claude Code dialect)
# Idempotent. hookoff.sh removes both again.
#
# Also publishes references/ to ~/.local/share/dev_team/references, the stable
# path the personas cite for shared reference docs (software-quality
# principles, the access-model layout). Both agent sets read those same files,
# so that link is deliberately NOT removed by hookoff.sh — see the note there.
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
else
  echo >&2
  echo "One or more links could not be established; see above." >&2
  exit 1
fi
