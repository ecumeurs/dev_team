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
| `intent-keeper` | subagent | `gpt-5.6-terra` | Keeps the ATD-less intent register (`intent/`) and runs the same intent gates in repos without `.atd`. |
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

## Intent guardrail: ATD or the intent register

The leaders check every change against declared business intent. There is a
preflight before a plan is final, architecture capture before code, and a
sync after the task that confirms the declared intent still matches the
code. The team can hold that intent in one of two backends. Each repository
picks one with a marker at its project root. The ATD-less backend, the
**intent register**, needs nothing beyond plain files, `grep` and `git`.

| Marker at the project root | Backend | Intent owner | Owner's skills |
|---|---|---|---|
| `.atd` | ATD atoms (`docs/*.atom.md`, `@spec-link`/`@test-link`, the `atd` CLI or MCP server) | `documentalist` | `atd-*` |
| `intent/README.md` | intent register (`intent/*.md`, `@intent` tags) | `intent-keeper` | `intent-preflight`, `intent-architecture-capture`, `intent-post-task-sync`, `intent-cold-start`, `intent-spec-ingestion` |
| both | ATD wins, and the register is reported to the user as a conflict | `documentalist` | `atd-*` |
| neither | no declared intent, so no gate runs | none | none |

The leaders' side of the protocol (when to call the owner, how to act on its
verdict) is one shared skill, `intent-gating-protocol`, for both backends.
The verdict scale is the same in both: `PROCEED`,
`PROCEED-WITH-SIGNOFF-PENDING`, `HALT-NEEDS-USER-INPUT` and
`HALT-NEEDS-CONTRACT-VISION-DECISION`.

### Where intent lives without atoms

The spec tree (`specs/`, see `references/doc-tree-conventions.md`) is where
intent is worked out and published per milestone. It can't be the record the
gates check against on its own:

- The master spec carries no tracking IDs, by convention, so a plan, a
  handoff or a line of code can't point at one rule in it.
- It is scoped to a milestone and gets archived when the milestone closes.
  The gates need the standing, current record.
- It has no home for architectural decisions made while planning a task.
- A codebase that never went through `spec-writer` has no spec tree at all.

So the spec tree stays as it is, and a small dedicated register sits beside
it:

```
intent/
  README.md        the marker; Vision (in and out of scope), Contract
                   (guarantees that change only with the user's agreement)
  business.md      one entry per business rule the product must keep
  architecture.md  one entry per architectural decision, each naming the
                   business entries it serves
```

An entry has a kebab-case ID (`guest-checkout`), a status (`draft`, then
`confirmed` once a human confirms it, then `retired`), and fields that state
the rule in full. It never cites a spec section or a register ID to complete
its meaning. The register is filled from the settled master spec (spec
ingestion), from existing code (cold start), or from preflight proposals.
Slug IDs never collide with the trees' `D`/`O`/`Q` numbers. The format is in
`references/intent-register.md`.

### How code links to it

A comment tag, `@intent <id>`, sits directly above the function, class,
route handler or test that implements or tests an entry. It survives file
moves and `git grep -n '@intent'` finds every tag. The implementer places
tags, because the leader's handoff carries the entry IDs. The post-task sync
adds any tag that is missing (a comment line only) and reports tags that
point at unknown or retired entries.

### Who owns it

A new agent, `intent-keeper`, is the register's only writer. It mirrors
`documentalist`: the same five triggers, the same verdicts, and the same
rules. It never edits application logic, and it never resolves drift by
rewriting the entry or the code. The alternatives were weaker:

- **Redistributing the job to existing agents.** The gate needs a checker
  that is independent of the leader whose plan it checks, and the record
  needs a single writer to stay consistent.
- **Extending `documentalist`.** Its prompt is mostly `atd` ground truth
  (CLI, atom anatomy, lifecycle). Loading that in an ATD-less repo wastes
  context and invites `atd` calls.

A separate owner keeps each backend's text in exactly one place.
`spec-writer`, `ux-writer`, the leaders and `codebase-explorer` refer to
"the intent owner" and pick it by marker.

### The gates, register backend

- **Preflight** (`intent-preflight`). D1 runs before code exploration and
  searches the register for the task. D2 runs after exploration and reads
  the `@intent` tags in the files in scope. The trivial path gets a single
  peek. When no entry governs the change but one can be inferred, it is
  written as `draft` and the verdict asks for sign-off. When nothing can be
  inferred, or the only grounding would change Vision or Contract, the
  verdict halts.
- **Architecture capture** (`intent-architecture-capture`). Once a plan
  settles a new or changed API, entity, module, service, UI flow or
  specification, the decision goes into `architecture.md` as `draft`,
  serving its business entries, before the handoff.
- **Post-task sync** (`intent-post-task-sync`). It reads the diff and the
  tags, then sorts each entry involved: aligned, missing tag, no entry, or
  drift. Drift stops the sync. The entry gets a `Drift:` line naming both
  sides, and a human or a leader resolves it. Neither the entry's rule nor
  the code is rewritten. Moving an entry to `confirmed` needs a human.
- **Cold start** (`intent-cold-start`). It drafts the register from an
  existing codebase: every entry is `draft` and describes current behavior,
  Vision is drafted, and Contract is proposed only.
- **Spec ingestion** (`intent-spec-ingestion`). `spec-writer` hands over the
  finished master spec (and its access model). Only settled content becomes
  entries, and it creates `intent/` if the repo has no marker yet.

### Packaging

It is one team with two backends, selected per repository at runtime. There
is no second agent set and no install-time variant:

- **Hand sync stays flat.** Backend-specific text lives only in each owner
  and its skills. Every shared agent carries one backend-neutral pointer, so
  editing a leader updates both modes. A duplicated set would double the
  work on top of the three ports.
- **ATD mode is unchanged.** The `documentalist` and `atd-*` bodies are
  untouched. The only ATD-side edit is renaming the leaders' skill
  `atd-gating-protocol` to `intent-gating-protocol`, with the same rules.
- **An install-time variant costs more than it saves.** The agent
  directories are linked as whole directories. A variant would need
  per-file links, and Codex inlines skills, so each variant would need full
  TOML copies.
- **No ATD tooling is needed.** Without `.atd`, no agent calls `atd`. A
  machine without `atd` runs the register backend as is, apart from the
  `mcp.atd` entry in `opencode/opencode.jsonc`, which the scripts don't
  manage.

To use the register in a repository: for a new product, let `spec-writer`
hand its master spec over (spec ingestion creates `intent/`). For an
existing codebase, ask `intent-keeper` for a cold start. After that, the
leaders gate every task on their own.

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
symlink. Setup also removes any link in `~/.claude/skills` that points into
this repo's `skills/` at a skill that no longer exists, such as
`atd-gating-protocol` after its rename to `intent-gating-protocol`.

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
into this repo's `skills/` directory, including links to skills since renamed
or removed (any other skill living there is left
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
