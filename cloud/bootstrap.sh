#!/usr/bin/env bash
# Entry point for a cloud environment's "Setup script" field (cloud/README.md):
#
#   curl -fsSL https://raw.githubusercontent.com/ecumeurs/dev_team/main/cloud/bootstrap.sh \
#     | bash -s -- [cloud/setup.sh options]
#
# Fetches dev_team to /opt/dev_team, then runs cloud/setup.sh with the same
# options. The VM's GitHub proxy may refuse to clone repos that aren't
# attached to the session, even public ones, so fetch_repo falls back to a
# tarball from codeload.github.com. Always exits 0: a failure here must not
# stop the session from starting. It is logged, and cloud/session-start.sh
# reports it inside the session.
set -uo pipefail

LOG=/var/log/dev_team-bootstrap.log
STATUS_DIR=/opt/dev_team-status
mkdir -p "$STATUS_DIR"

# fetch_repo <owner/name> <dest>: git clone, else the main branch tarball.
fetch_repo() {
	local repo="$1" dest="$2"
	rm -rf "$dest"
	if git clone --depth 1 "https://github.com/$repo" "$dest"; then
		return 0
	fi
	echo "fetch_repo: git clone of $repo failed; trying the codeload tarball."
	rm -rf "$dest" && mkdir -p "$dest"
	curl -fsSL "https://codeload.github.com/$repo/tar.gz/refs/heads/main" \
		| tar -xz -C "$dest" --strip-components=1
}

if fetch_repo ecumeurs/dev_team /opt/dev_team >"$LOG" 2>&1; then
	echo ok >"$STATUS_DIR/fetch-dev_team"
	bash /opt/dev_team/cloud/setup.sh "$@"
else
	echo failed >"$STATUS_DIR/fetch-dev_team"
	echo "cloud/bootstrap.sh: could not fetch dev_team, see $LOG" >&2
	cat "$LOG" >&2
fi
exit 0
