#!/usr/bin/env bash
# Cloud sessions only (claude.ai/code): this project's own session steps. The
# dev_team session hook (dev_team cloud/session-start.sh, installed by the
# environment's setup script) runs it from the repo root at every start and
# resume, whether the session opened this repo or several side by side.
[ "${CLAUDE_CODE_REMOTE:-}" = true ] || exit 0

# Same browser location as the dev container; the setup script pre-installs there.
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
[ -n "${CLAUDE_ENV_FILE:-}" ] && echo 'export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright' >>"$CLAUDE_ENV_FILE"

if [ ! -d node_modules ]; then
	npm ci --no-audit --no-fund >/tmp/npm-ci.log 2>&1 || echo "infinite_flow: npm ci failed, see /tmp/npm-ci.log."
fi
# A no-op when the cached browser matches the locked @playwright/test version;
# downloads it otherwise (the cache may predate a Playwright bump).
npx playwright install chromium >/tmp/playwright-install.log 2>&1 \
	|| echo "infinite_flow: Playwright browser install failed, see /tmp/playwright-install.log."
echo "infinite_flow: ready in $PWD."
exit 0
