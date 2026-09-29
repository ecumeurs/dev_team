#!/usr/bin/env bash
# Provision a claude.ai/code cloud environment for the dev_team agent set.
#
# Called by cloud/bootstrap.sh, the environment's "Setup script" (see
# cloud/README.md), once dev_team is at /opt/dev_team:
#
#   cloud/setup.sh [--playwright VER] [--godot VER] [--godot-mirror REPO]
#
# Runs as root on Ubuntu 24.04, before Claude Code starts. Its filesystem is
# snapshotted and reused for about 7 days when it finishes in under ~5 minutes,
# so the slow installs run in parallel. It always exits 0: a failed optional
# install must not stop the session from starting; each failure is logged to
# /var/log/dev_team-setup.log and reported again by cloud/session-start.sh.
set -uo pipefail

DEV_TEAM_DIR=/opt/dev_team
ATD_DIR=/opt/atd
LOG=/var/log/dev_team-setup.log
STATUS_DIR=/opt/dev_team-status

playwright_version=""
godot_version=""
godot_mirror=""
while [ $# -gt 0 ]; do
	case "$1" in
	--playwright) playwright_version="$2"; shift ;;
	--godot) godot_version="$2"; shift ;;
	--godot-mirror) godot_mirror="$2"; shift ;;
	*) echo "cloud/setup.sh: unknown option $1" >&2 ;;
	esac
	shift
done

mkdir -p "$STATUS_DIR"
: >"$LOG"
# shellcheck source=cloud/fetch.sh
. "$DEV_TEAM_DIR/cloud/fetch.sh"

# step <name> <function>: run one install, record ok/failed in $STATUS_DIR.
step() {
	local name="$1"; shift
	if "$@" >>"$LOG" 2>&1; then
		echo ok >"$STATUS_DIR/$name"
	else
		echo failed >"$STATUS_DIR/$name"
		echo "cloud/setup.sh: $name failed, see $LOG" >&2
	fi
}

link_dev_team() {
	# The session hook refreshes it as whatever user Claude runs as.
	chmod -R a+rwX "$DEV_TEAM_DIR"
	git config --system --add safe.directory "$DEV_TEAM_DIR"
	# Claude may run as root or as a user under /home, and the agents have to
	# be linked before it starts; the session hook relinks for the real user.
	local home
	for home in /root /home/*; do
		[ -d "$home" ] || continue
		HOME="$home" "$DEV_TEAM_DIR/scripts/setup.sh" || return 1
		[ "$home" = /root ] || chown -hR --reference="$home" "$home/.claude" "$home/.config" "$home/.codex" "$home/.local" || true
	done
}

# The session hook goes in the managed settings, which Claude Code reads
# whatever the working directory and user. A project's own
# .claude/settings.json isn't enough: with several repos attached, Claude
# starts in /home/user and only reaches them through --add-dir, which loads
# their CLAUDE.md and skills but not their hooks.
install_session_hook() {
	local file=/etc/claude-code/managed-settings.json
	local cmd="bash $DEV_TEAM_DIR/cloud/session-start.sh"
	local hook
	hook="$(jq -n --arg cmd "$cmd" '[{matcher: "startup|resume", hooks: [{type: "command", command: $cmd}]}]')"
	mkdir -p "$(dirname "$file")"
	[ -s "$file" ] || echo '{}' >"$file"
	# Merge, keeping any settings already there, and replace an earlier copy.
	jq --arg cmd "$cmd" --argjson hook "$hook" \
		'.hooks.SessionStart = ([(.hooks.SessionStart // [])[] | select(all(.hooks[]?; .command != $cmd))] + $hook)' \
		"$file" >"$file.new" && mv "$file.new" "$file"
	chmod 0644 "$file"
}

build_atd() {
	fetch_repo ecumeurs/atd "$ATD_DIR"
	# cgo stays on: atd's store uses go-sqlite3.
	mkdir -p /usr/local/lib/atd
	(cd "$ATD_DIR/atd" && CGO_ENABLED=1 go build -trimpath -o /usr/local/lib/atd/atd ./cmd/atd)
	repo_version "$ATD_DIR" >/usr/local/lib/atd/VERSION
	ln -sf /usr/local/lib/atd/atd /usr/local/bin/atd
}

install_playwright() {
	export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
	npx -y "playwright@$playwright_version" install --with-deps chromium \
		|| npx -y "playwright@$playwright_version" install chromium
	chmod -R a+rX /ms-playwright
}

install_godot() {
	local zip="Godot_v${godot_version}-stable_linux.x86_64.zip"
	local tmp
	tmp="$(mktemp -d)"
	# The GitHub proxy only serves release assets of repos attached to the
	# session, so the official build may 403. The fallback is a copy uploaded
	# as a release asset of the project repo itself (cloud/README.md).
	curl -fsSL -o "$tmp/$zip" \
		"https://github.com/godotengine/godot-builds/releases/download/${godot_version}-stable/$zip" \
		|| { [ -n "$godot_mirror" ] && gh release download "godot-$godot_version" -R "$godot_mirror" -p "$zip" -D "$tmp"; } \
		|| return 1
	unzip -o -q "$tmp/$zip" -d "$tmp"
	install -m 0755 "$tmp/Godot_v${godot_version}-stable_linux.x86_64" /usr/local/bin/godot
	rm -rf "$tmp"
	godot --headless --version
}

step dev_team link_dev_team
step hook install_session_hook
step atd build_atd &
[ -n "$playwright_version" ] && { step playwright install_playwright & }
[ -n "$godot_version" ] && { step godot install_godot & }
wait

echo "cloud/setup.sh: done ($(cd "$STATUS_DIR" && grep -H . * | tr '\n' ' '))"
exit 0
