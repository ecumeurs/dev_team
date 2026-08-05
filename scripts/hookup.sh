#!/usr/bin/env bash
# Turn the dev_team agent set ON: symlink ~/.config/opencode/agents to this
# repo's agents/ dir so OpenCode loads coding-leader & co. Idempotent.
#
# Also publishes references/ to ~/.local/share/dev_team/references, the stable
# path the personas cite for shared reference docs (software-quality
# principles, the access-model layout). That link is harness-independent —
# the Claude Code agent set reads the same files — so it is established here
# but deliberately NOT removed by hookoff.sh, which only governs OpenCode
# team presence.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_SRC="$REPO_DIR/agents"
AGENTS_LINK="$HOME/.config/opencode/agents"
REFS_SRC="$REPO_DIR/references"
REFS_LINK="$HOME/.local/share/dev_team/references"

# --- shared reference docs (both harnesses) --------------------------------
link_refs() {
  if [ ! -d "$REFS_SRC" ]; then
    echo "Warning: $REFS_SRC does not exist; skipping reference publish." >&2
    return 0
  fi
  mkdir -p "$(dirname "$REFS_LINK")"
  if [ -L "$REFS_LINK" ]; then
    if [ "$(readlink -f "$REFS_LINK")" = "$(readlink -f "$REFS_SRC")" ]; then
      echo "References already published: $REFS_LINK -> $REFS_SRC"
      return 0
    fi
    echo "Reference symlink points elsewhere ($(readlink -f "$REFS_LINK")); replacing."
    rm "$REFS_LINK"
  elif [ -e "$REFS_LINK" ]; then
    echo "Refusing to touch $REFS_LINK: it exists and is not a symlink." >&2
    echo "Move it aside manually if you want the dev_team references published." >&2
    return 1
  fi
  ln -s "$REFS_SRC" "$REFS_LINK"
  echo "References published: $REFS_LINK -> $REFS_SRC"
}

# --- OpenCode agent set ----------------------------------------------------
link_agents() {
  if [ -L "$AGENTS_LINK" ]; then
    if [ "$(readlink -f "$AGENTS_LINK")" = "$(readlink -f "$AGENTS_SRC")" ]; then
      echo "Already hooked up: $AGENTS_LINK -> $AGENTS_SRC"
      return 0
    fi
    echo "Existing symlink points elsewhere ($(readlink -f "$AGENTS_LINK")); replacing."
    rm "$AGENTS_LINK"
  elif [ -e "$AGENTS_LINK" ]; then
    echo "Refusing to touch $AGENTS_LINK: it exists and is not a symlink." >&2
    echo "Move it aside manually first if you want to hook up the dev_team agents." >&2
    return 1
  fi

  ln -s "$AGENTS_SRC" "$AGENTS_LINK"
  echo "Hooked up: $AGENTS_LINK -> $AGENTS_SRC"
  echo "dev_team agents are now live for OpenCode:"
  local names=() f n
  for f in "$AGENTS_SRC"/*.md; do
    [ -e "$f" ] || continue
    n="${f##*/}"
    names+=("${n%.md}")
  done
  printf '%s\n' "${names[@]}" | paste -sd, - | sed 's/,/, /g' | fold -sw 74 | sed 's/^/  /'
}

link_refs
link_agents
