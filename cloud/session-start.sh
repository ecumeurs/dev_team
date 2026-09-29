#!/usr/bin/env bash
# Per-session half of the cloud setup, called by a project's SessionStart hook
# (cloud/project-template/.claude/cloud-session-start.sh) in cloud sessions only.
#
# cloud/setup.sh runs once per cached environment (up to ~7 days old), so this
# refreshes what must be current or can't survive the snapshot:
#   - pulls dev_team, so agent and skill edits pushed since the cache was built
#     reach new sessions, and relinks them for the user Claude runs as;
#   - brings the tailnet up when TS_AUTHKEY is set (a running tailscaled is a
#     process, which the snapshot doesn't keep);
#   - reports any install that failed in the setup script.
# Everything it prints lands in Claude's context, so it stays short.
set -uo pipefail

DEV_TEAM_DIR=/opt/dev_team
STATUS_DIR=/opt/dev_team-status
RUN_DIR=/tmp/dev_team-cloud
mkdir -p "$RUN_DIR"

if [ ! -d "$DEV_TEAM_DIR/.git" ]; then
	echo "dev_team: not provisioned. Set the environment's setup script (dev_team cloud/README.md)."
	exit 0
fi

timeout 30 git -C "$DEV_TEAM_DIR" pull --ff-only --quiet >/dev/null 2>&1 \
	|| echo "dev_team: pull failed, using the cached copy ($(git -C "$DEV_TEAM_DIR" log -1 --format=%h))."
"$DEV_TEAM_DIR/scripts/setup.sh" >"$RUN_DIR/hookup.log" 2>&1 \
	|| echo "dev_team: linking agents failed, see $RUN_DIR/hookup.log."

for f in "$STATUS_DIR"/*; do
	[ -f "$f" ] && [ "$(cat "$f")" = failed ] \
		&& echo "dev_team: setup step '$(basename "$f")' failed; see /var/log/dev_team-setup.log."
done

# Tailnet, for atd's Ollama-backed commands (map, audit, search, trace, ...).
if [ -n "${TS_AUTHKEY:-}" ] && command -v tailscaled >/dev/null 2>&1; then
	sock="$RUN_DIR/tailscaled.sock"
	socks=127.0.0.1:1055
	if ! tailscale --socket="$sock" status >/dev/null 2>&1; then
		# Userspace networking: no TUN device needed. tailscaled inherits the
		# VM's HTTPS_PROXY, which carries its control and DERP traffic.
		setsid nohup tailscaled --tun=userspace-networking --socks5-server="$socks" \
			--state=mem: --socket="$sock" --statedir="$RUN_DIR/ts" --no-logs-no-support \
			>"$RUN_DIR/tailscaled.log" 2>&1 &
		sleep 1
		host="claude-cloud-${CLAUDE_CODE_REMOTE_SESSION_ID:-session}"
		timeout 45 tailscale --socket="$sock" up --authkey="$TS_AUTHKEY" \
			--hostname="${host:0:60}" --timeout=40s >"$RUN_DIR/tailscale-up.log" 2>&1
	fi
	if tailscale --socket="$sock" status >/dev/null 2>&1; then
		echo "socks5://$socks" >"$RUN_DIR/tailnet-proxy"
		echo "dev_team: tailnet up; atd reaches Ollama through it."
	else
		rm -f "$RUN_DIR/tailnet-proxy"
		echo "dev_team: tailnet failed ($RUN_DIR/tailscale-up.log); atd LLM commands (map, audit, search, trace) won't work."
	fi
fi

echo "dev_team: agents at $(git -C "$DEV_TEAM_DIR" log -1 --format=%h), atd $(cat /usr/local/lib/atd/VERSION 2>/dev/null || echo missing)."
exit 0
