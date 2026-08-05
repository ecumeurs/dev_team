#!/usr/bin/env bash
# Turn the dev_team agent set OFF for both harnesses: remove the
# ~/.config/opencode/agents and ~/.claude/agents symlinks so each falls back
# to its own stock agents. Idempotent, and only ever removes a symlink it
# recognizes — real content in either location is left untouched.
#
# Deliberately does NOT remove ~/.local/share/dev_team/references, which
# hookup.sh publishes: those are inert reference docs when nothing reads them,
# and keeping them means re-running hookup.sh is the only step needed to come
# back up. Remove that link by hand if you really want it gone.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

failed=0

# remove_link <dst> <label>
remove_link() {
  local dst="$1" label="$2"

  if [ -L "$dst" ]; then
    local target
    target="$(readlink -f "$dst")"
    rm "$dst"
    echo "$label: removed $dst (was -> $target)"
  elif [ -e "$dst" ]; then
    echo "$label: refusing to touch $dst — it exists and is not a symlink (real content present)." >&2
    return 1
  else
    echo "$label: already off ($dst does not exist)"
  fi
}

remove_link "$HOME/.config/opencode/agents" "OpenCode"    || failed=1
remove_link "$HOME/.claude/agents"          "Claude Code" || failed=1

if [ "$failed" -ne 0 ]; then
  echo >&2
  echo "One or more links could not be removed; see above." >&2
  exit 1
fi

echo
echo "Both harnesses now fall back to their stock built-in agents only."
echo "Re-run scripts/hookup.sh to bring the dev_team set back."
