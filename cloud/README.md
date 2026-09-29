# Running the dev_team agents in Claude Code cloud sessions

A cloud session (claude.ai/code, `claude --cloud`, the mobile app) runs on a
fresh Ubuntu 24.04 VM with clones of the repos attached to it. It never sees
this machine, so `~/.claude/agents`, `~/.claude/skills`,
`~/.local/share/dev_team/references` and `~/.local/bin/atd` are all missing.
This directory rebuilds that layout on the VM.

It relies on **dev_team and atd being public GitHub repos**: the setup script
fetches them from `main` even when they aren't attached to the session.

## How it fits together

| Piece | Where it lives | When it runs |
| --- | --- | --- |
| `cloud/bootstrap.sh` → `cloud/setup.sh` | the environment's **Setup script** field (claude.ai) | once per cached environment (rebuilt every ~7 days, or when the script or network list changes), as root, before Claude starts |
| `cloud/session-start.sh` | installed by `setup.sh` as a SessionStart hook in `/etc/claude-code/managed-settings.json` | every session start and resume |
| `.claude/cloud-project.sh` | committed in each project repo (templates in `cloud/projects/<name>/`) | run by `session-start.sh`, from the repo root |

`bootstrap.sh` fetches dev_team to `/opt/dev_team` and hands over to
`setup.sh`. That script links the agents and skills for every home on the
VM, builds atd from source into `/usr/local/bin/atd`, installs the session
hook, and optionally installs Playwright's Chromium and Godot. The VM's
GitHub proxy only lets `git clone` reach repos attached to the session, so
each fetch falls back to a `codeload.github.com` tarball of `main`
(`cloud/fetch.sh`). The bootstrap itself comes from
`raw.githubusercontent.com`, which bypasses that proxy. Nothing here can fail
the session start: failures land in `/var/log/dev_team-bootstrap.log` and
`/var/log/dev_team-setup.log`, and the session hook reports them.

The hook sits in the managed settings, not in the project, because of
multi-repo sessions. With several repos attached, Claude starts in
`/home/user` with each repo at `/home/user/<repo>`, added with `--add-dir`.
Those repos' `CLAUDE.md` and skills load, but their `.claude/settings.json`
hooks don't. `session-start.sh` therefore looks for work in the project
directory and in each directory beneath it:

- It links the agents from dev_team's session clone when dev_team is
  attached, so edits on the session branch apply. Otherwise it uses
  `/opt/dev_team`, refreshed from `main`, so agent edits reach sessions
  without waiting for a cache rebuild.
- It reports failed setup steps and atd's mode (below) into Claude's context.
- It runs each `.claude/cloud-project.sh` it finds.

atd is built from `main` when the cache is built. To pick up a newer atd
sooner, edit the setup script (any change, even a comment) to force a
rebuild.

## atd without Ollama

A cloud VM can't reach the desktop's Ollama, so atd runs without an LLM. Its
offline commands (`lint`, `query`, `check`, `crawl`, `weave`, `trace`,
`update`, `search --grep`) work as usual. `index` and `search --query` need
embeddings and fail. `map`, `trace --summary`, `audit`'s bloat check,
`congruence`, `compare`, `reconcile`, `check --semantic` and `fix` fall back
to atd's `ide_agent` passthrough: they write the prompt they would have sent
to `pipeline_output/` and Claude answers it itself. The agents' rules for
this mode are in `references/atd-atoms.md` ("Without an LLM provider").
Projects keep `pipeline_output/` in `.gitignore`.

## One cloud environment per project

Create them at claude.ai/code (environment selector > add environment). They
are personal, so only you can read their variables.

### infinite_flow

- **Setup script**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/ecumeurs/dev_team/main/cloud/bootstrap.sh \
    | bash -s -- --playwright 1.63.0
  ```
  Keep `--playwright` in step with `@playwright/test` in `package-lock.json`
  (`cloud-project.sh` also runs `npx playwright install chromium`, so a
  stale pin only costs a download).
- **Network access**: Custom, with *Also include default list* checked, plus:
  ```text
  cdn.playwright.dev
  playwright.download.prss.microsoft.com
  playwright.azureedge.net
  archive.ubuntu.com
  security.ubuntu.com
  ```
- **Repos to attach**: infinite-flow. Attaching dev_team too makes the
  session use its clone for the agents; Claude can then also edit and push
  it, so tell it to stay in infinite_flow.
- **Repo files**: `.claude/cloud-project.sh` (from
  `cloud/projects/infinite_flow/`) and `pipeline_output/` in `.gitignore`.
- **Out of reach in the cloud**: the dev container itself (the VM replaces it)
  and the Docker socket from the host. `docker compose up --build` still works,
  since the VM has its own Docker.

### slime_train

Stays local for now. The template in `cloud/projects/slime_train/` is ready
if that changes:

- **Setup script**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/ecumeurs/dev_team/main/cloud/bootstrap.sh \
    | bash -s -- --godot 4.7.2 --godot-mirror kluthen/slime_train
  ```
- **Network access**: Trusted.
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
- **Repo files**: `.claude/cloud-project.sh` and `pipeline_output/` in
  `.gitignore`.
- **Out of reach in the cloud**: `make apk` and `make install` (no Android SDK,
  no phone). The native GDExtension is not built; it is outside the test
  suite anyway (`docs/dev/native.md`).

## Check the first session

The session's first context should carry the hook's `dev_team: …` lines and
`infinite_flow: ready in …`. Then ask Claude:

> Print `pwd`. List your agent types and skills. Run `atd --version`,
> `cat /opt/dev_team-status/*`, `tail -30 /var/log/dev_team-setup.log`,
> `ls /tmp/dev_team-cloud/` and `atd lint`.

- No `dev_team:` lines and no `/tmp/dev_team-cloud/`: the hook didn't run.
  Check that `/etc/claude-code/managed-settings.json` holds it.
- The hook ran but the dev_team agents (coding-leader, documentalist, ...)
  are missing: Claude Code read the agent directory before any link
  existed for its user. Start a second session; the setup script links every
  home before Claude starts, which covers the cached case.

## Status

Revised 2026-09-29 after the first real session, which showed the
multi-repo layout and that the VM can't reach the desktop's Ollama. Still unverified in
the cloud: the managed-settings hook, which user Claude runs as, and the
codeload fallback for repos not attached to the session.
