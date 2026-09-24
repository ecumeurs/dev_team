# dev_team on native Windows Claude Code (no RTK)

This folder is a **Windows-native port** of this repo's Claude Code agent
team. It deliberately drops everything RTK-related (the `rtk hook claude`
PreToolUse hook, `RTK.md`, the `rtk` binary) — RTK is a Linux binary with no
Windows build, and this port is not going to chase one. Everything else
(the 12 subagents + the skills they invoke + the shared reference docs) is
fully portable: they're plain Markdown/JSON, no OS-specific content.

This is **Claude Code only** — not OpenCode, not Codex. If you later want
those on the Windows box too, treat this folder as a starting template and
extend it; nothing here assumes only Claude Code exists.

## What you get vs. what you lose vs. the Linux box

| Piece | Ported here? | Notes |
|---|---|---|
| 12 agent personas (`claude-agents/*.md`) | ✅ yes, unchanged | Plain Markdown + YAML frontmatter, zero OS-specific content |
| Skills (`skills/*/SKILL.md`) | ✅ yes, unchanged | Same reasoning |
| `references/` (shared docs the personas cite) | ✅ yes, unchanged | `spec-writer` and `ux-writer` read from here |
| `CLAUDE.md` (global) | ✅ yes, rewritten | RTK section removed |
| `settings.json` (global) | ✅ yes, rewritten | RTK hook removed; LiteLLM proxy routing removed (see below) |
| `RTK.md` | ❌ dropped | No Windows `rtk` binary; nothing references it once the hook and `CLAUDE.md` include are gone |
| `rtk hook claude` PreToolUse hook | ❌ dropped | Was RTK's own mechanism for rewriting bash commands; meaningless without the binary |
| `guard-secrets.sh` hook | ❌ not wired | It's a bash script (`#!/usr/bin/env bash`); Windows Claude Code hooks need a `.ps1`/`.cmd`/`.exe` command, or WSL/Git-Bash on PATH. Left out here — see "Optional: secret-guard hook" below if you want it back |
| LiteLLM proxy routing (`ANTHROPIC_BASE_URL` → `localhost:4000`) | ❌ removed | That's a proxy running *on the Linux box*. Talk to Anthropic directly on Windows unless you stand up (or point at) an equivalent proxy there — see note below |

## Layout of this folder

```
windows/
  README.md          this file
  CLAUDE.md           global CLAUDE.md for the Windows machine (no RTK include)
  settings.json       global settings.json for the Windows machine (no RTK hook)
  setup.ps1           installs the agents/skills/references as directory junctions
  teardown.ps1        removes them again (mirrors scripts/hookoff.sh)
```

It does **not** duplicate `claude-agents/`, `skills/`, or `references/` —
`setup.ps1` links straight back into this same repo checkout, exactly like
`scripts/hookup.sh` does on Linux. Clone/copy this whole repo onto the
Windows machine; don't cherry-pick just the `windows/` folder.

## Prerequisites

1. **Node.js** (LTS) and **git** for Windows — Claude Code's native Windows
   install needs both.
2. **Claude Code for Windows**, installed per Anthropic's docs:
   ```powershell
   npm install -g @anthropic-ai/claude-code
   ```
   (or the native Windows installer if you're using that instead — either
   way `claude` should resolve on PATH afterward; check with `claude
   --version`.)
3. **This repo, cloned onto the Windows machine**, e.g.:
   ```powershell
   git clone <your-remote-or-copy-path> C:\Users\<you>\work\dev_team
   ```
4. Directory **junctions need no admin rights** on Windows (unlike symlinks),
   so `setup.ps1` uses junctions (`New-Item -ItemType Junction`) rather than
   `mklink /D` + elevation. This only works because agents/skills are
   directories on the same machine/volume as the repo — if `C:\Users\<you>`
   and the repo are on different volumes, junctions won't cross volumes;
   move the repo onto the same drive as your user profile, or fall back to
   plain copies (see `setup.ps1 -Copy`).

## Install

From an ordinary (non-admin) PowerShell prompt, in the repo root:

```powershell
cd C:\Users\<you>\work\dev_team
powershell -ExecutionPolicy Bypass -File windows\setup.ps1
```

This will:

- Junction `%USERPROFILE%\.claude\agents` → `<repo>\claude-agents`
- Junction `%USERPROFILE%\.claude\skills\<name>` → `<repo>\skills\<name>`,
  one skill at a time (never the whole `skills\` folder at once — mirrors
  the Linux `hookup.sh` behavior so it won't clobber any skill you install
  by hand later)
- Junction `%USERPROFILE%\.local\share\dev_team\references` →
  `<repo>\references`
- Copy `windows\CLAUDE.md` → `%USERPROFILE%\.claude\CLAUDE.md` (only if that
  file doesn't already exist, or with `-Force` to overwrite)
- Copy `windows\settings.json` → `%USERPROFILE%\.claude\settings.json`
  (same existence check)

It is idempotent — safe to re-run after `git pull`.

If a target already exists as a **real file/folder** (not a junction), the
script refuses to touch it and tells you what to move aside — same
conservative behavior as `hookup.sh`.

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File windows\teardown.ps1
```

Removes the agent/skill junctions (not the `CLAUDE.md`/`settings.json`
copies, and not the `references` junction — same rationale as the Linux
`hookoff.sh`: references are inert docs, not "team presence").

## What else got dropped from `settings.json` (and why)

Beyond the RTK hook and the LiteLLM env vars, `windows/settings.json` also
leaves out the Linux box's `autoMode` block (the `soft_deny` rules and the
long `environment` fact-sheet about the `upsilonumbrella` repo, AWS account,
protected scripts, etc.). That block describes *that specific project's*
trust boundary, not a Claude Code default — it doesn't transfer to a
different machine unless you're working in the exact same repo there too.
If you are, copy the `autoMode` block over verbatim; if you're working on
something else on Windows, write a fresh one for that project instead of
inheriting stale rules.

## About the LiteLLM routing you're leaving behind

The Linux box's `ANTHROPIC_BASE_URL=http://localhost:4000` points Claude
Code at a local LiteLLM proxy for provider routing / DLP. That proxy is not
something this port can bring along — it's a service running on the Linux
machine, not a Claude Code setting. Your options on Windows:

- **Do nothing** (what `windows/settings.json` does): Claude Code talks to
  Anthropic directly using your normal subscription auth. Simplest, no DLP
  layer.
- **Point at the same LiteLLM instance over the network**, if the Linux box
  exposes it beyond `localhost` (it currently doesn't — `localhost:4000` is
  loopback-only). You'd need to change LiteLLM's bind address and add auth/
  TLS in front of it before exposing it to another machine — don't just open
  the port.
- **Run a second LiteLLM instance on Windows** — more setup, but keeps DLP
  and routing consistent across both machines. Out of scope for this port;
  ask if you want that scaffolded separately.

## Optional: secret-guard hook, ported to PowerShell

`~/.claude/hooks/guard-secrets.sh` (the `PreToolUse` guard on `Read|Grep|Bash`
that blocks casual reads of `.env`/private keys/`.tfstate`/etc.) is **not**
included here because it's a bash script and native Windows Claude Code
hooks run as PowerShell/cmd by default. Two ways to get it back if you want
it:
- Port the logic to a `.ps1` script and wire it as the hook `command` in
  `settings.json` (I can write this if you want it — it's a bounded, well-
  contained script).
- Or, if you're going to use Git Bash / WSL anyway for other tooling, just
  point the hook `command` at `bash.exe ~/.claude/hooks/guard-secrets.sh`
  and keep the original script verbatim.

Not done automatically here since the two "no RTK" and "no secret-guard"
decisions are independent — ask if you want the guard added back.

## After install: sanity check

```powershell
claude --version
# In a fresh Claude Code session, ask: "list your available subagents"
# You should see: coding-leader, coordination-leader, spec-writer,
# coding-executor, codebase-explorer, web-researcher, reviewer,
# principal-advisor, multimodal-looker, documentalist, ux-writer, ux-critic
```

## Keeping the two machines in sync

Same discipline as the Linux↔Linux-dialect story in the main `README.md`:
there is no automated sync. If you edit a persona or skill, `git pull` on
the Windows box picks it up automatically (junctions point straight into
the repo checkout) — no re-run of `setup.ps1` needed unless you added a
*new* skill directory (then re-run it once to link the new one).
