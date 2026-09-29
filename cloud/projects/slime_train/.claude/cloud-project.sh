#!/usr/bin/env bash
# Cloud sessions only (claude.ai/code): this project's own session steps. The
# dev_team session hook (dev_team cloud/session-start.sh, installed by the
# environment's setup script) runs it from the repo root at every start and
# resume, whether the session opened this repo or several side by side.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

if command -v godot >/dev/null 2>&1; then
	echo "slime_train: $(godot --headless --version 2>/dev/null | tail -n 1) on PATH; run tests with tools/test.sh. No Android SDK or phone here: make apk/install won't work."
else
	echo "slime_train: Godot is not installed, so tools/test.sh can't run. Check the environment's setup script."
fi
exit 0
