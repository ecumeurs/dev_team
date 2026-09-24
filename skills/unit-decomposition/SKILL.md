---
name: unit-decomposition
description: Use when coding-leader or coordination-leader is turning a settled implementation plan into coding-executor handoffs, to size the work into independently-dispatchable units and sequence them into parallel/sequential waves instead of one oversized brief. Shared by both leaders — the decomposition method is identical regardless of which one is driving the task.
---

# Unit Decomposition (for leaders)

Use this once a plan is settled and it's time to turn it into `coding-executor`
handoffs — not during exploration, and not as a substitute for having a real
plan first. It exists to stop two failure modes at once: a single
`coding-executor` absorbing a task big enough to blow its own context and
compact mid-work, and a leader re-reading or re-verifying so much of the diff
itself between dispatches that its own context bloats instead.

## What counts as a unit

A unit is one `coding-executor` assignment. Before dispatching it, check all
five:

1. **File-disjoint within its wave** — no two units running at the same time
   touch the same file. This is what makes parallel dispatch safe; if two
   candidate units share a file, they're one unit, or need re-splitting along
   a different seam.
2. **Independently verifiable** — it has its own pass/fail gate: a test, a
   build step, a type-check, a runnable check against a stub or interface. It
   must not require a sibling unit's actual code to exist to be checked — at
   most a contract (an interface, schema, or type) already agreed in the
   brief.
3. **Boundedly sized** — an enumerable, small file set decided before
   dispatch. Rule of thumb: one architectural layer or one feature slice —
   "add the migration," "implement `TokenService.refresh()`," "wire the new
   route," "update the call site" — not "refactor auth."
4. **Self-contained brief** — goal, exact files, the relevant existing
   patterns/snippets, the contract it must conform to (a function signature,
   a schema shape, an API contract), and acceptance criteria. The executor
   should never need to re-explore the whole repo; the leader already paid
   that cost during grounding and hands down only the relevant slice.
5. **One done-signal** — a single pass/fail check, not an open-ended goal.

If a candidate can't be stated as one pass/fail check, would need more than
~5 files, or straddles more than one architectural layer, it's actually two
units — split it before dispatch, don't discover the size problem
mid-execution.

## Building the plan into units

1. From the grounding pass and the settled plan, list every file/module that
   needs to change.
2. Mark the real dependencies: which changes need another to exist first (an
   interface before its implementer, a migration before the query that needs
   it, a producer before its consumer). Most listed changes have no such
   dependency on each other — don't invent one just to feel thorough.
3. Partition the change-set along natural seams — architectural layers,
   feature/module boundaries, disjoint file groups. Never split a single
   cohesive change (one function, one file, one tightly-coupled edit) across
   two units just to have more units.
4. Arrange units into **waves**: a topological layering of the dependency
   graph. Wave 1 has no unresolved dependencies; wave 2 depends only on units
   in wave 1; and so on.

## Dispatching a wave

Within a wave, dispatch one `coding-executor` per unit in the same batch —
they're file-disjoint by construction, so there's no coordination cost to
running them in parallel. Across waves, dispatch sequentially: don't start
wave N+1 until wave N's units have reported their own completion.

## Crossing wave boundaries: trust the unit's own gate, verify only on failure

Each unit's `coding-executor` already runs its own completion gate
(diagnostics/build/tests scoped to what it touched) before reporting done —
that already checks it against its own contract. Don't duplicate that by
re-running a full diagnostic or test pass over the whole wave yourself before
starting the next one; that's exactly the kind of leader-side bloat this
skill exists to avoid.

Move to the next wave once every unit in the current one reports its own
gate passed. Step in yourself only when a failure actually surfaces:

- **A unit in the current wave fails its own gate**: that's this unit's
  problem — feed the failure back into the same dispatch (a fresh
  `coding-executor` call carrying the failure evidence), don't widen scope
  to fix it yourself.
- **A downstream wave's unit fails because an upstream contract wasn't
  actually honored** (the type doesn't match, the endpoint isn't there, the
  migration didn't run): that's new evidence a unit's own gate couldn't have
  caught, since it can't see the future. Trace it to the offending unit,
  dispatch a bounded fix against that unit specifically, then re-run the unit
  that surfaced the failure.

The leader's own end-of-task completion gate — the full diagnostics/tests/
build pass already required by your own operating instructions — still runs
once, at the very end, across the whole change. That's the real integration
check; per-wave gating stays reactive, not exhaustive.

## When not to fan out

Fan out only when real seams exist and there are enough of them to be worth
the coordination overhead. Don't manufacture seams in a genuinely single
cohesive change — a mechanical, repetitive edit across many files (a rename,
a systematic signature update) is still better as one bounded brief with a
repeated pattern than as N units, since no independent judgment is actually
being split across them. Trivial and explicit tasks under your own triage
never reach this skill in the first place; it's for the non-trivial tier,
once a plan is real.

## How this fits your delegation identity

You still hold the plan and the final verification. Dispatching a
wave-ordered set of `coding-executor` calls instead of one oversized brief is
the same "delegate bounded leaf work" pattern you already use — applied
deliberately to several bounded pieces from one plan, instead of assumed to
be exactly one. It is not a license to become a pure dispatcher: you still
own forming the units, sequencing the waves, and running the final
integration gate yourself.
