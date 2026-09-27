---
name: intent-gating-protocol
description: Use when coding-leader or coordination-leader is operating in a repo with declared intent — a `.atd` config (ATD) or an `intent/README.md` register at the project root — to know which agent owns that intent, when to call it for preflight/architecture-capture/post-task-sync, and how to act on its verdict. Shared by both leaders and both backends — the protocol is identical regardless of which leader is driving the task or where the intent lives.
---

# Intent Gating Protocol (for leaders)

This is the leader's side of the protocol; the **intent owner** runs the
actual checks with its own skills. Your job here is knowing *which* owner
applies, *when* to call it, and what each verdict obligates you to do next —
never to run the checks yourself or second-guess its findings.

## Which owner, if any

Check the project root early — it changes how you plan, on every triage
tier, not just non-trivial ones.

| At the project root | Intent owner | Where intent lives | Code links |
|---|---|---|---|
| `.atd` | `documentalist` | ATD atoms, `docs/*.atom.md` | `@spec-link` / `@test-link` |
| `intent/README.md` | `intent-keeper` | the intent register, `intent/*.md` | `@intent <id>` |
| both | `documentalist` — ATD wins. Tell the user the repo carries two intent records and gate against ATD only. | | |
| neither | none — skip this protocol for the task. | | |

With neither marker, don't create a register on your own initiative. On
non-trivial work, say in your final report that the repo has no declared
intent and that `intent-keeper` can cold-start one; starting it is the
user's call. A `spec-writer` handoff to `intent-keeper` also starts one;
that is part of the spec work the user asked for, not your initiative.

Everything below applies to both owners. They share the same five triggers
and the same verdict scale; only their storage differs. "Governing entries"
below means atom IDs in an ATD repo and register entry IDs in an `intent/`
repo.

## When to call the intent owner

1. **Before finalizing any plan** (preflight D1) — hand it the task in plain
   language. It searches for intent that already governs this area and flags
   conflicts before any code is written.
2. **Once you've identified real files/modules in scope** (preflight D2) —
   call it again with those targets so it can refine the blast radius against
   the code links actually present in them. Do this before you start editing
   or finalize a handoff, not after.
3. **Even on the trivial/fast-gate path** (single file, obvious target) —
   still give it a peek (its D-peek variant: the one file's code links plus
   one search, collapsed into a single cheap call). A file-level judgment
   that a change is "obvious" is not the same thing as a business-intent
   governance judgment, and skipping this check on the fast path is exactly
   the failure mode it exists to catch.
4. **Once your plan settles on a concrete architectural decision** — a new or
   changed API, entity, module, service, UI flow, or specification, not just
   "which existing entry governs this" — call the owner again for
   architecture capture *before* you start implementing or finalize the
   handoff. It records the decision now (an ARCHITECTURE-layer atom, or an
   `intent/architecture.md` entry), tied to the governing business intent
   preflight already found, so the decision is on record before the code
   exists rather than reconstructed from the diff afterward. Skip this when
   the plan is a bug fix or local tweak inside an area whose architecture is
   already recorded — only a genuinely new/changed piece of architecture
   needs it.
5. **After closing the work** — hand off for the post-task sync before
   reporting to the user. Give it the changed files (or the base commit to
   diff from), the governing entry IDs, and anything the user confirmed or
   rejected along the way.

| Call | `documentalist` skill | `intent-keeper` skill |
|---|---|---|
| Preflight D1 / D2 / D-peek | `atd-preflight` | `intent-preflight` |
| Architecture capture | `atd-architecture-capture` | `intent-architecture-capture` |
| Post-task sync | `atd-post-task-sync` | `intent-post-task-sync` |

## Acting on the verdict

- **PROCEED** — carry the governing entry IDs forward as context for the
  work, the handoff (if delegating), and the post-task sync.
- **PROCEED-WITH-SIGNOFF-PENDING** — a confirmed/STABLE or business-level
  entry sits in the blast radius, or the owner drafted a new business entry
  inferred from the task. Surface this now, not as a surprise at close-out;
  treat any actual change to that entry as needing explicit user
  confirmation before you proceed, and put a drafted entry in front of the
  user to confirm or reject. If the user rejects it and the task stops
  there, still ask the owner to remove the rejected draft.
- **HALT-NEEDS-USER-INPUT** — no governing entry found and the task
  description doesn't give enough to infer one, or the information
  contradicts itself. Don't proceed on a guess — bring the owner's findings
  (near misses and why they don't fit) back to the user and ask a precise
  reformulation question, per your own ambiguity policy.
- **HALT-NEEDS-CONTRACT-VISION-DECISION** — the only plausible business
  grounding would require changing the project's Contract or Vision (the
  CONTRACT/VISION atoms, or those sections of `intent/README.md`). This
  always needs explicit user agreement; treat it like a genuinely
  mutually-exclusive-requirements case, not a routine clarification you can
  resolve yourself.

A preflight halt is a real blocker on the same footing as any other stop
condition in your own operating instructions — not something to route around
by narrowing scope until it disappears.

Drift the post-task sync reports is yours or the user's to resolve, never
the owner's: decide which side is right (the recorded intent or the code),
or put the question to the user, and say which in your final report. If the
record is the side that's wrong, ask the owner to revise it, with the user's
sign-off when the entry is confirmed/STABLE. Never ask it to make the record
match the code just to clear the finding.

## If you delegate execution

Never hand off to an executor (`coding-executor` or equivalent) — not even on
the trivial path — without at least a peek first. A clean handoff needs to
reflect a PROCEED or PROCEED-WITH-SIGNOFF-PENDING verdict, and, if one was
obtained, the architecture-capture entry ID(s), not skip either question. In
an `intent/` repo, the handoff also tells the executor to put an
`@intent <id>` comment tag directly above each function, class, route
handler or test it writes or changes for one of those entries.
