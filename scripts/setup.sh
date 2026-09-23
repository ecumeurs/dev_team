#!/usr/bin/env bash
# Friendly alias for installing the dev_team agent symlinks.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/hookup.sh" "$@"
