#!/usr/bin/env bash
# Cloud sessions only (claude.ai/code): wire the dev_team agent set and check
# the Godot toolchain. Local sessions exit at once. The environment's setup
# script is described in dev_team's cloud/README.md.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

[ -f /opt/dev_team/cloud/session-start.sh ] && bash /opt/dev_team/cloud/session-start.sh

if command -v godot >/dev/null 2>&1; then
	echo "slime_train: $(godot --headless --version 2>/dev/null | tail -n 1) on PATH; run tests with tools/test.sh. No Android SDK or phone here: make apk/install won't work."
else
	echo "slime_train: Godot is not installed, so tools/test.sh can't run. Check the environment's setup script."
fi
exit 0
