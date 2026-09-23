---
name: atd-gating-protocol
description: Use when coding-leader or coordination-leader is operating in a repo with a `.atd` config at the project root, to know when to call documentalist for preflight/architecture-capture/post-task-sync and how to act on its verdict. Shared by both leaders — the protocol is identical regardless of which one is driving the task.
---

# ATD Gating Protocol (for leaders)

This is the leader's side of the protocol; `documentalist` runs the actual
checks (its own `atd-preflight` and `atd-architecture-capture` skills). Your
job here is knowing *when* to call it and what each verdict obligates you to
do next — never to run `atd` commands yourself or second-guess its findings.

Check for `.atd` at the project root early — it changes how you plan, on
every triage tier, not just non-trivial ones. If absent, documentalist has no
job here; skip this protocol entirely for the task.

## When to call documentalist

1. **Before finalizing any plan** (preflight D1) — hand it the task in plain
   language. It searches for atoms that already govern this area and flags
   conflicts before any code is written.
2. **Once you've identified real files/modules in scope** (preflight D2) —
   call it again with those targets so it can refine the blast radius against
   actual `@spec-link`s. Do this before you start editing or finalize a
   handoff, not after.
3. **Even on the trivial/fast-gate path** (single file, obvious target) —
   still give it a peek (its D-peek variant: one `atd map --file` plus one
   semantic search, collapsed into a single cheap call). A file-level
   judgment that a change is "obvious" is not the same thing as a
   BUSINESS-layer governance judgment, and skipping this check on the fast
   path is exactly the failure mode it exists to catch.
4. **Once your plan settles on a concrete architectural decision** — a new or
   changed API, entity, module, service, UI flow, or specification, not just
   "which existing atom governs this" — call documentalist again (its
   `atd-architecture-capture` skill) *before* you start implementing or
   finalize the handoff. It materializes the ARCHITECTURE-layer atom now,
   parented to the governing BUSINESS atom preflight already found, so the
   atom is on record before the code exists rather than reconstructed from
   the diff afterward. Skip this when the plan is a bug fix or local tweak
   inside an already-atomized module — only a genuinely new/changed piece of
   architecture needs it.
5. **After closing the work** — hand off for the post-task papertrail sync
   (documentalist's `atd-post-task-sync` skill), before reporting to the
   user.

## Acting on the verdict

- **PROCEED** — carry the governing atom IDs forward as context for the work,
  the handoff (if delegating), and the post-task sync.
- **PROCEED-WITH-SIGNOFF-PENDING** — a STABLE or BUSINESS atom sits in the
  blast radius. Surface this now, not as a surprise at close-out; treat any
  actual change to that atom as needing explicit user confirmation before you
  proceed.
- **HALT-NEEDS-USER-INPUT** — no governing atom found and the task
  description doesn't give enough to infer one, or the information
  contradicts itself. Don't proceed on a guess — bring documentalist's
  findings (near-miss atoms and why they don't fit) back to the user and ask
  a precise reformulation question, per your own ambiguity policy.
- **HALT-NEEDS-CONTRACT-VISION-DECISION** — the only plausible business
  grounding would require changing the project's CONTRACT or VISION atom.
  This always needs explicit user agreement; treat it like a genuinely
  mutually-exclusive-requirements case, not a routine clarification you can
  resolve yourself.

A preflight halt is a real blocker on the same footing as any other stop
condition in your own operating instructions — not something to route around
by narrowing scope until it disappears.

## If you delegate execution

Never hand off to an executor (`coding-executor` or equivalent) — not even on
the trivial path — without at least a peek first. A clean handoff needs to
reflect a PROCEED or PROCEED-WITH-SIGNOFF-PENDING verdict, and, if one was
obtained, the architecture-capture atom ID(s), not skip either question.
