# dev_team

Git-tracked source of truth for this machine's OpenCode agent configuration:
a small "Coding Team" of native OpenCode agents, plus `opencode.jsonc` itself.

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
opencode/
  opencode.jsonc    the live OpenCode config (symlinked from
                    ~/.config/opencode/opencode.jsonc)
references/         Project-agnostic reference material agents consult
                    (not symlinked/live-loaded — read on demand via path)
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

## The team

| Agent | Mode | Model | Role |
|---|---|---|---|
| `coding-leader` | primary | `llmward/claude-opus` | Default owner for most coding work; holds context end-to-end. |
| `coordination-leader` | all | `llmward/claude-opus` | Alternate opening owner for highly ambiguous / multi-task requests that need scoping before implementation starts. |
| `spec-writer` | all | `llmward/glm-5` | Ideation/specification partner for unscoped future work — turns a rough idea into a spec `coding-leader` can build from. |
| `coding-executor` | subagent | `llmward/glm-5` | Bounded leaf implementation once scope is clear. |
| `codebase-explorer` | subagent | `llmward/glm-4.7` | Read-only: locates code, call chains, existing patterns. |
| `web-researcher` | subagent | `llmward/glm-5` | Read-only: external docs, library/version behavior, OSS references. |
| `reviewer` | subagent | `llmward/glm-5.2` | Independent OKAY/REJECT review gate before closing non-trivial work. |
| `principal-advisor` | subagent | `llmward/claude-opus` | High-stakes architecture/perf/security/complexity judgment calls. |
| `multimodal-looker` | subagent | `llmward/claude-haiku` | Reads screenshots, PDFs, diagrams, UI images. |
| `documentalist` | subagent | `llmward/glm-5` | Maintains the ATD papertrail after coding tasks close in ATD-managed repos. |

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

Edit files here directly — both `agents/` and `opencode/opencode.jsonc` are
live via symlink from `~/.config/opencode/`, so changes take effect on the
next `opencode` invocation with no extra sync step. Commit as usual.

## Toggling the team on/off

```
scripts/hookup.sh    # symlink ~/.config/opencode/agents -> agents/ (team ON)
scripts/hookoff.sh   # remove that symlink (team OFF, stock build/plan/explore/general only)
```

Both are idempotent and only ever touch a symlink they recognize — if
`~/.config/opencode/agents` is ever a real directory instead of a symlink,
they refuse to touch it rather than guess. Neither script touches
`opencode.jsonc` / the `llmward`-only provider lock — that's a separate,
permanent DLP-routing boundary, not part of "team presence".
