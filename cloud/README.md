# Running the dev_team agents in Claude Code cloud sessions

A cloud session (claude.ai/code, `claude --cloud`, the mobile app) runs on a
fresh Ubuntu 24.04 VM with a clone of the project repo. It never sees this
machine, so `~/.claude/agents`, `~/.claude/skills`,
`~/.local/share/dev_team/references` and `~/.local/bin/atd` are all missing.
This directory rebuilds that layout on the VM.

It relies on **dev_team and atd being public GitHub repos**: the VM clones them
anonymously. It only sees what is pushed to `main`, never local edits.

## How it fits together

| Piece | Where it lives | When it runs |
| --- | --- | --- |
| `cloud/bootstrap.sh` → `cloud/setup.sh` | the environment's **Setup script** field (claude.ai) | once per cached environment (rebuilt every ~7 days, or when the script or network list changes), as root, before Claude starts |
| `cloud/session-start.sh` | dev_team, called by the project hook | every session start and resume |
| `.claude/settings.json` + `.claude/cloud-session-start.sh` | committed in the project repo (templates in `cloud/projects/<name>/`) | every session start and resume; does nothing locally |
| `cloud/atd-wrapper.sh` | installed as `/usr/local/bin/atd` | on every `atd` call; routes it through the tailnet when that is up |

`bootstrap.sh` fetches dev_team to `/opt/dev_team` and hands over to
`setup.sh`, which runs `scripts/setup.sh`, builds
atd from source, and optionally installs Playwright's Chromium, Godot and
Tailscale. The VM's GitHub proxy refuses to `git clone` repos not attached
to the session, even public ones, so each fetch falls back to a
`codeload.github.com` tarball of `main` (`cloud/fetch.sh`); the bootstrap
itself comes from `raw.githubusercontent.com`, which bypasses that proxy.
Nothing here can fail the session start: failures land in
`/var/log/dev_team-bootstrap.log` and `/var/log/dev_team-setup.log`, and the
session hook reports them. `session-start.sh` pulls dev_team (so agent edits reach sessions
without waiting for a cache rebuild), relinks, brings the tailnet up, and
reports failed steps into Claude's context.

atd is built when the cache is built. To pick up a newer atd sooner, edit the
setup script (any change, even a comment) to force a rebuild.

## One cloud environment per project

Create them at claude.ai/code (environment selector > add environment). They
are personal, so only you can read their variables.

### infinite_flow

- **Setup script**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/ecumeurs/dev_team/main/cloud/bootstrap.sh \
    | bash -s -- --playwright 1.63.0 --tailscale
  ```
  Keep `--playwright` in step with `@playwright/test` in `package-lock.json`
  (the session hook also runs `npx playwright install chromium`, so a stale
  pin only costs a download).
- **Network access**: Custom, with *Also include default list* checked, plus:
  ```text
  cdn.playwright.dev
  playwright.download.prss.microsoft.com
  playwright.azureedge.net
  archive.ubuntu.com
  security.ubuntu.com
  *.tailscale.com
  tailscale.com
  ```
- **Environment variables**: `TS_AUTHKEY=<key>` (see Tailscale below); leave
  it out to run without Ollama.
- **Repo files**: copy `cloud/projects/infinite_flow/.claude/*` into the repo's
  `.claude/`, add the `tailnet` provider to `.atd` (Tailscale section), and push.
- **Out of reach in the cloud**: the dev container itself (the VM replaces it)
  and the Docker socket from the host. `docker compose up --build` still works,
  since the VM has its own Docker.

### slime_train

- **Setup script**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/ecumeurs/dev_team/main/cloud/bootstrap.sh \
    | bash -s -- --godot 4.7.2 --godot-mirror kluthen/slime_train --tailscale
  ```
- **Network access**: Custom, defaults included, plus `*.tailscale.com` and
  `tailscale.com`.
- **Environment variables**: `TS_AUTHKEY=<key>`, optional.
- **Godot mirror**: the VM's GitHub proxy may refuse release assets from repos
  not attached to the session, which would block the official
  `godotengine/godot-builds` download. The fallback is a copy attached to a
  release of slime_train itself (Godot is MIT, so redistributing it is fine):
  ```bash
  cd ~/work && zip Godot_v4.7.2-stable_linux.x86_64.zip Godot_v4.7.2-stable_linux.x86_64
  gh release create godot-4.7.2 Godot_v4.7.2-stable_linux.x86_64.zip -R kluthen/slime_train \
    --title "Godot 4.7.2 (cloud session toolchain)" --notes "Headless Linux build for cloud sessions." --prerelease
  ```
  Only needed if the setup log shows the official download failing.
- **Repo files**: copy `cloud/projects/slime_train/.claude/*` into the repo's
  `.claude/`, add the `tailnet` provider to `.atd` (Tailscale section), and push.
- **Out of reach in the cloud**: `make apk` and `make install` (no Android SDK,
  no phone). The native GDExtension is not built; it is outside the test
  suite anyway (`docs/dev/native.md`).

## Tailscale, so atd reaches the desktop's Ollama

`atd lint`, `check` and `query` run offline. `map`, `audit`, `search`,
`trace`, `congruence`, `fix` and `index` call Ollama, which runs on the
desktop `bastienbureau` (tailnet address `100.77.105.99`). The session joins
the tailnet as an ephemeral node and atd reaches Ollama at that address.

1. **Add a provider to the project's `.atd`**, after `remote` so the LAN
   address still wins at home. Its longer timeout allows for the relayed
   path from the cloud; away from home it also serves a laptop on the tailnet.
   ```bash
   jq '.llm.providers |= (.[:1] + [{"name": "tailnet", "base_url": "http://100.77.105.99:11434", "timeout_ms": 5000}] + .[1:])' .atd > .atd.new && mv .atd.new .atd
   ```
2. **Restrict the cloud nodes to Ollama only.** In the Tailscale policy file:
   ```json
   "tagOwners": { "tag:claude-cloud": ["autogroup:admin"] },
   "hosts": { "bastienbureau": "100.77.105.99" },
   "acls": [
     { "action": "accept", "src": ["tag:claude-cloud"], "dst": ["bastienbureau:11434"] }
   ]
   ```
   Merge this with your existing rules. Any rule that lets `*` reach everything
   also lets the cloud VM reach your whole tailnet, so scope those to users or
   tags first.
3. **Generate an auth key** (Settings > Keys): **reusable**, **ephemeral**,
   **pre-approved**, tag `tag:claude-cloud`. Put it in each environment as
   `TS_AUTHKEY`.

Nothing changes on the desktop: Ollama already answers on its tailnet address.

In the VM, tailscaled runs in userspace mode (no TUN device needed) and
reaches the control plane through the VM's HTTPS proxy, so traffic is
relayed over DERP. Expect slower responses than on your LAN.

## Check the first session

Ask Claude in the first session of each environment:

> List your available agent types and skills, then run `atd --version`,
> `cat /opt/dev_team-status/*` and `atd search "test"`.

- If the dev_team agents (coding-leader, documentalist, ...) are missing but
  the hook said "agents at <sha>", Claude Code read the agent directory before
  the hook linked it. Start a second session: the setup script links it for
  root before Claude starts, which covers the cached case.
- If `atd search` fails, read `/tmp/dev_team-cloud/tailscale-up.log`.

## Status

Written 2026-09-29, not yet run in a cloud session. The parts that rely on
unverified behavior are: user-level `~/.claude/agents` on the VM being loaded
like local ones, `git clone` of public repos not attached to the session
through the GitHub proxy, the Godot download path, and Tailscale over the VM's
HTTPS proxy.
