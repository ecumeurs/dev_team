#!/usr/bin/env bash
# Turn the dev_team agent set OFF for all supported harnesses: remove the
# ~/.config/opencode/agents, ~/.claude/agents, and ~/.codex/agents symlinks so
# each falls back to its own stock agents. Idempotent, and only ever removes
# symlinks — real content in any location is left untouched.
#
# Deliberately does NOT remove ~/.local/share/dev_team/references, which
# hookup.sh publishes: those are inert reference docs when nothing reads them,
# and keeping them means re-running hookup.sh is the only step needed to come
# back up. Remove that link by hand if you really want it gone.
#
# DOES remove each skills/<name> symlink hookup.sh placed in ~/.claude/skills
# — unlike references, skills are active automation an agent can invoke, so
# turning the team off should turn its skills off too. Only ever removes a
# symlink pointing back into this repo's skills/ directory; any other skill
# living in ~/.claude/skills (hand-installed, unrelated) is left untouched.
#
# Deliberately does NOT touch opencode.jsonc / the llmward provider lock —
# that's a separate, permanent DLP-routing boundary, not "team presence".
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
remove_link "$HOME/.codex/agents"           "Codex"       || failed=1

if [ -d "$REPO_DIR/skills" ]; then
  for skill_dir in "$REPO_DIR/skills"/*/; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    remove_link "$HOME/.claude/skills/$name" "Skill:$name" || failed=1
  done
fi

# Also remove links to skills this repo no longer has (renamed or deleted),
# which the loop above can't name. Only links pointing into this repo's
# skills/ directory are touched.
for link in "$HOME/.claude/skills"/*; do
  [ -L "$link" ] || continue
  target="$(readlink "$link")"
  case "$target" in
    "$REPO_DIR/skills/"*)
      rm "$link"
      echo "Skill:$(basename "$link"): removed stale link (was -> $target)"
      ;;
  esac
done

if [ "$failed" -ne 0 ]; then
  echo >&2
  echo "One or more links could not be removed; see above." >&2
  exit 1
fi

echo
echo "All supported harnesses now fall back to their stock built-in agents only."
echo "Re-run scripts/hookup.sh to bring the dev_team set back."
