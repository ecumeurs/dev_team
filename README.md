# dev_team

Git-tracked source of truth for this machine's coding-agent personas: a small
"Coding Team" ported across OpenCode, Claude Code, and Codex, plus the
OpenCode provider config.

## Why this exists

This used to run on [crewbee](https://crewbeelab.github.io), a third-party
OpenCode plugin providing a prebuilt multi-agent "Coding Team". It was dropped
in favor of this repo because:

- crewbee's built-in personas are written in Chinese — unusable as-is for an
  English-speaking user.
- crewbee is a large (~26k-line) third-party plugin running as arbitrary JS
  with full user privileges — an ongoing audit burden for not much upside.
- OpenCode already natively supports everything crewbee needed: named agents
  with `mode: primary | subagent | all`, per-agent `model`/`permission`/`tools`,
  and a built-in `task` delegation tool. crewbee was a schema + content layer
  on top of native OpenCode capabilities, not a capability OpenCode lacked.
- crewbee's plugin injected a stray top-level `crewbee` key into every chat
  request, which Anthropic's strict schema rejected — this repo's removal
  also let us drop the LiteLLM `request_sanitizer.py` workaround that existed
  only to strip that key.

The 8 crewbee "Coding Team" personas were extracted from crewbee's embedded
source (`dist/src/agent-teams/embedded/coding-team/agents/*.js`), understood
in depth, and rewritten from scratch in English — not machine-translated —
preserving the load-bearing behavioral rules (completion gates, guardrails,
delegation triggers) while dropping crewbee-internal plumbing that has no
native OpenCode equivalent. Two agents beyond those 8 are new, designed from
scratch rather than translated from crewbee: `documentalist`, which maintains
this machine's [ATD](../atd/) papertrail (`docs/*.atom.md`,
`@spec-link`/`@test-link` congruence); and `spec-writer`, an ideation/
specification partner for turning an unscoped project idea into a spec
`coding-leader` can build from — see
`references/software-quality-principles.md` for the project-agnostic quality
checklist it draws on.

## Layout

```
agents/            OpenCode native agent definitions (symlinked from
                    ~/.config/opencode/agents/)
claude-agents/      Claude Code subagent definitions, ported from agents/
                    (symlinked from ~/.claude/agents/ — user-scoped, all
                    projects on this machine)
codex-agents/       Codex custom-agent definitions, ported from claude-agents/
                    (symlinked from ~/.codex/agents/ — user-scoped, all
                    projects on this machine)
opencode/
  opencode.jsonc    the live OpenCode config (symlinked from
                    ~/.config/opencode/opencode.jsonc)
references/         Project-agnostic reference material agents consult
                    (not symlinked/live-loaded — read on demand via path)
skills/             Agent Skills (SKILL.md per subdirectory) holding a single
                    workflow's step-by-step procedure, invoked on demand by
                    the agent whose core file names it (each skills/<name>/
                    is symlinked individually into ~/.claude/skills/<name>/,
                    which OpenCode also discovers natively)
```

## The Claude Code fork (`claude-agents/`)

`claude-agents/` is a parallel port of the same team for Claude Code's native
subagent system (`.claude/agents/*.md`), which uses a different frontmatter
schema than OpenCode's and has no direct equivalent for `mode:
primary|subagent|all`. Practical differences from `agents/`:

- **Frontmatter**: `name`/`description`/`model`/`tools` (flat allowlist)
  instead of OpenCode's `mode`/`model`/`permission` (nested per-tool
  allow/deny/ask object). The `tools:` lists here are a best-effort
  translation of each persona's OpenCode permission intent, not a byte-for-
  byte reproduction — Claude Code's allowlist is coarser (no per-bash-command
  patterns, no three-state ask/allow/deny).
- **Models**: every agent runs on a real Claude model (`opus`/`sonnet`/
  `haiku`) rather than the mixed GLM/Claude lineup `agents/` uses, per
  explicit instruction — GLM models burn through their coding-plan token
  budget fast and aren't meant to be the default here. Roughly: former
  `glm-5.2` roles (coding-leader, coordination-leader, principal-advisor,
  reviewer) → `opus`; former `glm-5` roles (coding-executor, documentalist,
  web-researcher, spec-writer) → `sonnet`; former `glm-4.7` roles
  (codebase-explorer, multimodal-looker) → `haiku`.
- **No `primary`/`all` mode**: `coding-leader`, `coordination-leader`, and
  `spec-writer` were OpenCode opening-owner agents (`mode: primary`/`all`) —
  usable as the whole session's persona, not just a delegate. Claude Code has
  no equivalent; all ten are reachable only as subagents via the `Agent`
  tool (or by asking the top-level session to invoke one by name). None of
  them can be "the persona you start `claude` as."
- **Routing**: like `agents/` → the LLMWard LiteLLM proxy via OpenCode's
  provider config, Claude Code itself is routed through the same proxy via
  `~/.claude/settings.json`'s `env.ANTHROPIC_BASE_URL` (see
  `~/deploy/llmward/scripts/claude-code-litellm-on.sh` and
  `docs/architecture/litellm-client-routing.md` in that repo, Mode 1 —
  subscription OAuth forwarded upstream). No extra setup needed on the
  Claude Code side; DLP still runs on every request.
- Any find/replace needed for OpenCode-tool-specific prose (`todowrite` →
  the task-tracking tools, the `task` tool → `Agent`, `read`/`glob`/`grep` →
  `Read`/`Bash`, dropped `lsp`) was applied by hand when porting — if you
  edit `agents/*.md` going forward, re-check whether the same substitutions
  are needed in the matching `claude-agents/*.md` file; there's no automated
  sync between the two.

## The Codex fork (`codex-agents/`)

`codex-agents/` is a Codex-native port of the same team for Codex custom
agents (`~/.codex/agents/*.toml`). The files are generated from the
Claude Code port because that dialect is already closest to Codex's custom
agent shape: each persona has a `name`, `description`, model choice, optional
`sandbox_mode`, and `developer_instructions`.

Practical differences from the other two dialects:

- **Schema**: Codex custom agents are standalone TOML config layers, not
  Markdown files with YAML frontmatter. The required fields are `name`,
  `description`, and `developer_instructions`; other Codex config keys such as
  `model`, `model_reasoning_effort`, and `sandbox_mode` can be added per
  persona.
- **No OpenCode `primary` / `all` mode**: all files in `codex-agents/` are
  custom agents that Codex can spawn or refer to. They do not replace the main
  session persona automatically. For main-thread behavior, put durable guidance
  in a repo or global `AGENTS.md`; for a one-off run, ask Codex in the prompt
  to work in a specific style.
- **Models**: the Claude model tiers are mapped to current OpenAI Codex models:
  `opus` roles use `gpt-5.6` with high reasoning, `sonnet` roles use
  `gpt-5.6-terra` with medium reasoning, and `haiku` roles use
  `gpt-5.6-luna` with low reasoning. Adjust the TOML files if your Codex
  account or environment exposes a different model catalog.
- **Permissions**: Codex subagents inherit the parent turn's available tools and
  approval policy. Read-only personas additionally set `sandbox_mode =
  "read-only"` where the original role was advisory, review-only, research-only,
  or visual-inspection-only.
- **Official basis**: this follows OpenAI Docs for Codex custom agents and
  `AGENTS.md`. The relevant public docs are "Subagents" and "Custom
  instructions with AGENTS.md" in the Codex manual.
- **No skill invocation**: unlike `agents/` and `claude-agents/`, personas here
  keep their workflow procedures fully inline in `developer_instructions`
  rather than pointing at `skills/` with "invoke skill `name`". Codex has no
  per-persona tool/skill allowlist to gate it (see Permissions above) and no
  confirmed mechanism for reading `~/.claude/skills` at all, so a skill
  pointer here would reference something the agent may have no way to load.
  Keep this port fully self-contained until Codex documents real skill
  support, then extract the same sections `agents/`/`claude-agents/` already
  did.

## The team

| Agent | OpenCode mode | Codex model | Role |
|---|---|---|---|
| `coding-leader` | primary | `gpt-5.6` | Default owner for most coding work; holds context end-to-end. |
| `coordination-leader` | all | `gpt-5.6` | Alternate opening owner for highly ambiguous / multi-task requests that need scoping before implementation starts. |
| `spec-writer` | all | `gpt-5.6-terra` | Ideation/specification partner for unscoped future work — turns a rough idea into a spec `coding-leader` can build from. |
| `coding-executor` | subagent | `gpt-5.6-terra` | Bounded leaf implementation once scope is clear. |
| `codebase-explorer` | subagent | `gpt-5.6-luna` | Read-only: locates code, call chains, existing patterns. |
| `web-researcher` | subagent | `gpt-5.6-terra` | Read-only: external docs, library/version behavior, OSS references. |
| `reviewer` | subagent | `gpt-5.6` | Independent OKAY/REJECT review gate before closing non-trivial work. |
| `principal-advisor` | subagent | `gpt-5.6` | High-stakes architecture/perf/security/complexity judgment calls. |
| `multimodal-looker` | subagent | `gpt-5.6-luna` | Reads screenshots, PDFs, diagrams, UI images. |
| `documentalist` | subagent | `gpt-5.6-terra` | Maintains the ATD papertrail after coding tasks close in ATD-managed repos. |
| `ux-writer` | subagent | `gpt-5.6-terra` | Designs UI/UX document trees and token guidance before implementation. |
| `ux-critic` | subagent | `gpt-5.6` | Read-only UI/UX validator and critique specialist. |

### multimodal-looker model note

z.ai's vision-capable model is `glm-5v-turbo`, not the base `glm-5`. As of
2026-07-24 it's not usable under this account: the coding-plan subscription
explicitly excludes it ("plan does not yet include access"), and the general
pay-per-token API path returns "insufficient balance / no resource package".
`multimodal-looker` runs on `llmward/claude-haiku` instead (already funded,
natively vision-capable). To switch: add a `glm-5v-turbo` model block to
`config/litellm/config.yaml` pointed at `https://api.z.ai/api/paas/v4` once
the z.ai plan/balance side is sorted, then flip this agent's `model:` field.

## Editing

Edit files here directly. `agents/`, `claude-agents/`, and `codex-agents/` are
live through user-scope symlinks after setup, so changes take effect on the
next OpenCode, Claude Code, or Codex invocation with no extra sync step. Commit
as usual.

When updating a persona, edit the source dialect intentionally and then port
the same behavioral change to the other dialects by hand. There is no
automated sync between `agents/`, `claude-agents/`, and `codex-agents/`.

A skill in `skills/` holds one workflow's full step-by-step procedure, kept
out of an agent's always-loaded core file and pulled in on demand instead —
invoking a skill *adds* to context, it doesn't replace the core prompt. Only
extract a section into a skill when it's a self-contained, workflow-specific
procedure; cross-cutting guidance used across several of an agent's workflows
stays in the core file. An agent needs `permission.skill: allow` (OpenCode)
to invoke any skill at all — `deny` blocks it outright and `ask` prompts every
time, which defeats the point for a workflow step a persona is expected to
run routinely.

## Installation

Run setup from the repo root:

```bash
scripts/setup.sh
```

This creates or refreshes these symlinks:

```text
~/.config/opencode/agents -> agents/
~/.claude/agents          -> claude-agents/
~/.codex/agents           -> codex-agents/
```

It also publishes shared reference docs here:

```text
~/.local/share/dev_team/references -> references/
```

And symlinks each skill individually — never the whole `skills/` directory
onto `~/.claude/skills` itself, which may already hold skills this repo
doesn't manage:

```text
~/.claude/skills/<name> -> skills/<name>/   (one per subdirectory in skills/)
```

OpenCode discovers `~/.claude/skills` natively, so this single location makes
every skill available to OpenCode, Claude Code, and (if it later reads that
path) Codex alike — no separate OpenCode-specific skills target is needed.

The installer is idempotent. If a target already exists as a real directory or
file, it refuses to touch it and tells you to move that content aside manually.
If a target exists as a symlink to a different location, setup replaces that
symlink.

The legacy name still works:

```bash
scripts/hookup.sh
```

## Teardown

To remove the agent symlinks:

```bash
scripts/teardown.sh
```

This removes the OpenCode, Claude Code, and Codex agent symlinks, and every
per-skill symlink teardown finds under `~/.claude/skills` that points back
into this repo's `skills/` directory (any other skill living there is left
untouched). It does not remove real directories or files, and it leaves
`~/.local/share/dev_team/references` in place because that path is inert when
no persona reads it — unlike references, skills are active automation an
agent can invoke, so turning the team off turns its skills off too.

The legacy name still works:

```bash
scripts/hookoff.sh
```

## Codex usage

After setup, start a fresh Codex session so it rescans `~/.codex/agents`.

To use a persona for a delegated task, name it directly:

```text
Use the reviewer agent to review this implementation claim.
```

```text
Spawn codebase-explorer to map where authentication is implemented, then report
the relevant files and call chain.
```

```text
Have spec-writer turn this feature idea into a buildable spec before any code
changes.
```

In the Codex CLI, use `/agent` while subagents are running to inspect or switch
between agent threads. A custom agent is still a spawned agent, not the
automatic top-level personality of the main thread. If you want the current
main thread to behave like a persona for one task, say so in the prompt:

```text
For this task, work in the coding-leader style: hold main context, delegate only
bounded research, and verify before reporting completion.
```

For durable main-thread guidance across a repository, add an `AGENTS.md` file
to that repository. For durable personal guidance across repositories, use
`~/.codex/AGENTS.md`.

## Toggling the team on/off

```
scripts/setup.sh      # symlink all supported harnesses to this repo (team ON)
scripts/teardown.sh   # remove those symlinks (team OFF)
```

Both are idempotent and only ever remove symlinks. If a target is a real
directory instead of a symlink, teardown refuses to touch it rather than guess.
Neither script touches `opencode.jsonc` / the `llmward`-only provider lock —
that's a separate, permanent DLP-routing boundary, not part of "team presence".
