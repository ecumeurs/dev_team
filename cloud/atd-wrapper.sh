#!/bin/sh
# Installed as /usr/local/bin/atd in cloud sessions by cloud/setup.sh.
#
# atd reaches Ollama over plain HTTP. When cloud/session-start.sh has brought
# the tailnet up, it leaves the SOCKS5 address of the userspace tailscaled in
# $PROXY_FILE; atd's HTTP calls then go through it and reach the .atd
# "tailnet" provider (the desktop's Tailscale address, see cloud/README.md).
# localhost is never proxied by Go, so the "local" provider is unaffected.
# Without the file, atd runs as-is and only its offline commands (lint,
# check, query, ...) work.
PROXY_FILE=/tmp/dev_team-cloud/tailnet-proxy

if [ -s "$PROXY_FILE" ]; then
	proxy="$(cat "$PROXY_FILE")"
	export HTTP_PROXY="$proxy" http_proxy="$proxy" NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1
fi
exec /usr/local/lib/atd/atd "$@"
