#!/usr/bin/env bash
# Turn the dev_team agent set ON: symlink ~/.config/opencode/agents to this
# repo's agents/ dir so OpenCode loads coding-leader & co. Idempotent.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_SRC="$REPO_DIR/agents"
AGENTS_LINK="$HOME/.config/opencode/agents"

if [ -L "$AGENTS_LINK" ]; then
  if [ "$(readlink -f "$AGENTS_LINK")" = "$(readlink -f "$AGENTS_SRC")" ]; then
    echo "Already hooked up: $AGENTS_LINK -> $AGENTS_SRC"
    exit 0
  fi
  echo "Existing symlink points elsewhere ($(readlink -f "$AGENTS_LINK")); replacing."
  rm "$AGENTS_LINK"
elif [ -e "$AGENTS_LINK" ]; then
  echo "Refusing to touch $AGENTS_LINK: it exists and is not a symlink." >&2
  echo "Move it aside manually first if you want to hook up the dev_team agents." >&2
  exit 1
fi

ln -s "$AGENTS_SRC" "$AGENTS_LINK"
echo "Hooked up: $AGENTS_LINK -> $AGENTS_SRC"
echo "dev_team agents (coding-leader, coding-executor, codebase-explorer, web-researcher,"
echo "reviewer, principal-advisor, multimodal-looker, coordination-leader, documentalist)"
echo "are now live for OpenCode."
