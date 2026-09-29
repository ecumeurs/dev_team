# Sourced by cloud/setup.sh and cloud/session-start.sh (cloud/bootstrap.sh
# carries its own copy, since it runs before dev_team is on disk).
#
# The VM's GitHub proxy may refuse to clone repos that aren't attached to the
# session, even public ones, so a codeload.github.com tarball of main is the
# fallback. A tarball copy has no .git; repo_version reports it as such.

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

# repo_version <dir>: short commit, or "main (tarball, <date>)".
repo_version() {
	git -C "$1" rev-parse --short HEAD 2>/dev/null \
		|| echo "main (tarball, $(date -r "$1" +%F 2>/dev/null || echo '?'))"
}
