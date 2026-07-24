#!/usr/bin/env bash
# Turn the dev_team agent set OFF: remove the ~/.config/opencode/agents
# symlink so OpenCode falls back to its own stock agents (build/plan/explore/
# general) only. Idempotent, and only ever removes a symlink it recognizes.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

AGENTS_LINK="$HOME/.config/opencode/agents"

if [ -L "$AGENTS_LINK" ]; then
  target="$(readlink -f "$AGENTS_LINK")"
  rm "$AGENTS_LINK"
  echo "Hooked off: removed symlink $AGENTS_LINK (was -> $target)"
  echo "OpenCode now falls back to its stock built-in agents (build/plan/explore/general) only."
elif [ -e "$AGENTS_LINK" ]; then
  echo "Refusing to touch $AGENTS_LINK: it exists and is not a symlink (real content present)." >&2
  exit 1
else
  echo "Already hooked off: $AGENTS_LINK does not exist."
fi
