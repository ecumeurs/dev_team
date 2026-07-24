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
native OpenCode equivalent. A 9th agent, `documentalist`, is new: it maintains
this machine's [ATD](../atd/) papertrail (`docs/*.atom.md`,
`@spec-link`/`@test-link` congruence) and was designed from scratch against
the real ATD docs, not translated from anything.

## Layout

```
agents/            OpenCode native agent definitions (symlinked from
                    ~/.config/opencode/agents/)
opencode/
  opencode.jsonc    the live OpenCode config (symlinked from
                    ~/.config/opencode/opencode.jsonc)
```

## The team

| Agent | Mode | Model | Role |
|---|---|---|---|
| `coding-leader` | primary | `llmward/claude-opus` | Default owner for most coding work; holds context end-to-end. |
| `coordination-leader` | all | `llmward/claude-opus` | Alternate opening owner for highly ambiguous / multi-task requests that need scoping before implementation starts. |
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
