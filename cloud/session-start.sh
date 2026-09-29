#!/usr/bin/env bash
# The SessionStart hook of cloud sessions, installed by cloud/setup.sh in
# /etc/claude-code/managed-settings.json so it runs whatever the working
# directory: the project repo in a single-repo session, /home/user when
# several repos are attached (each then sits in /home/user/<repo>).
#
# cloud/setup.sh runs once per cached environment (up to ~7 days old), so this
# refreshes what must be current or can't survive the snapshot:
#   - links the agents from the freshest dev_team: the session's own clone
#     when dev_team is attached (it carries the session branch), else
#     /opt/dev_team, refreshed from main;
#   - reports any install that failed in the setup script;
#   - runs .claude/cloud-project.sh of the project directory and of each repo
#     beneath it, for per-project steps (npm ci, ...).
# Everything it prints lands in Claude's context, so it stays short.
set -uo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

OPT_DEV_TEAM=/opt/dev_team
STATUS_DIR=/opt/dev_team-status
RUN_DIR=/tmp/dev_team-cloud
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
mkdir -p "$RUN_DIR"

if [ ! -f "$OPT_DEV_TEAM/scripts/setup.sh" ]; then
	echo "dev_team: not provisioned; see /var/log/dev_team-bootstrap.log and the environment's setup script (dev_team cloud/README.md)."
	exit 0
fi
# shellcheck source=cloud/fetch.sh
. "$OPT_DEV_TEAM/cloud/fetch.sh"

# is_dev_team <dir>: the dir is a dev_team checkout.
is_dev_team() { [ -f "$1/scripts/hookup.sh" ] && [ -d "$1/claude-agents" ]; }

dev_team_dir=""
for d in "$PROJECT_DIR" "$PROJECT_DIR"/*/; do
	d="${d%/}"
	is_dev_team "$d" && { dev_team_dir="$d"; break; }
done

if [ -n "$dev_team_dir" ]; then
	dev_team_source="attached clone $dev_team_dir"
else
	dev_team_dir="$OPT_DEV_TEAM"
	dev_team_source="$OPT_DEV_TEAM"
	if [ -d "$OPT_DEV_TEAM/.git" ]; then
		timeout 30 git -C "$OPT_DEV_TEAM" pull --ff-only --quiet >"$RUN_DIR/refresh.log" 2>&1 \
			|| echo "dev_team: pull failed, using the cached copy ($(repo_version "$OPT_DEV_TEAM"))."
	else
		# A tarball copy: fetch main again and swap the contents in place, so the
		# ~/.claude links into it stay valid. Files are unlinked, not
		# overwritten, so this script (read by bash from its open file) is safe.
		if timeout 60 bash -c ". '$OPT_DEV_TEAM/cloud/fetch.sh' && fetch_repo ecumeurs/dev_team '$RUN_DIR/dev_team.new'" \
			>"$RUN_DIR/refresh.log" 2>&1; then
			find "$OPT_DEV_TEAM" -mindepth 1 -delete && cp -a "$RUN_DIR/dev_team.new/." "$OPT_DEV_TEAM/"
			rm -rf "$RUN_DIR/dev_team.new"
		else
			echo "dev_team: refresh failed, using the cached copy ($(repo_version "$OPT_DEV_TEAM")); see $RUN_DIR/refresh.log."
		fi
	fi
fi
"$dev_team_dir/scripts/setup.sh" >"$RUN_DIR/hookup.log" 2>&1 \
	|| echo "dev_team: linking agents failed, see $RUN_DIR/hookup.log."

for f in "$STATUS_DIR"/*; do
	[ -f "$f" ] && [ "$(cat "$f")" = failed ] \
		&& echo "dev_team: setup step '$(basename "$f")' failed; see /var/log/dev_team-setup.log and /var/log/dev_team-bootstrap.log."
done

echo "dev_team: agents from $dev_team_source ($(repo_version "$dev_team_dir")), atd $(cat /usr/local/lib/atd/VERSION 2>/dev/null || echo missing)."
# No Ollama is reachable from a cloud VM.
echo "dev_team: atd runs without an LLM here: semantic search and indexing fail, and map, trace --summary, audit, congruence and fix hand their prompts back to you. Follow \"Without an LLM provider\" in ~/.local/share/dev_team/references/atd-atoms.md."

# Per-project steps. Each script runs from its own repo root.
for d in "$PROJECT_DIR" "$PROJECT_DIR"/*/; do
	d="${d%/}"
	[ -f "$d/.claude/cloud-project.sh" ] || continue
	(cd "$d" && bash .claude/cloud-project.sh)
done
exit 0
