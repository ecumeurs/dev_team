# Software Quality Principles (project-agnostic baseline)

A starting checklist for reasoning about architecture and mechanics on a
project that has **no established conventions of its own yet** — early
ideation, a greenfield repo, or a spec being drafted before any code exists.

These are deliberately generic — stack-agnostic, framework-agnostic, and not
tied to any one project's specific tooling (no mandatory doc-traceability
system, no mandatory tracing stack, no fixed response envelope or script
names). Treat additions to this file the same way: keep it usable by a
project this team has never seen before.

## Precedence rule

**A target project's own documented conventions always win.** If the repo has
a `CLAUDE.md`, `AGENTS.md`, a coding-standard doc, or decisions already
recorded in its own spec docs (e.g. "crash early" settled independently in a
project's own `docs/README.md`), that is the authority — these principles are
only a fallback for filling gaps the project hasn't decided yet, and a
sanity-check list for spotting when a proposed mechanic quietly violates a
principle nobody thought to write down.

## The principles

1. **Crash early, fail loud.** No silent defaulting or catch-all fallback
   values in core logic to "keep things running." A clear rejection at the
   boundary beats undefined behavior three modules downstream. Errors are
   values to handle or propagate — never swallowed in an empty catch.

2. **Honor contracts exactly — no rescuing them with a guessed default.**
   Once an interface, schema, or API shape is decided, code on both sides of
   it either satisfies it or fails per the contract. Don't coerce types or
   invent missing fields to make a call "work." Changing a contract is a
   deliberate, visible decision — not a side effect of one caller's
   convenience.

3. **Determinism and testability are seams, not afterthoughts.** Anything
   that depends on wall-clock time, randomness, or external scheduling should
   go through an injectable/fakeable seam rather than being called directly
   inline, if the project cares about reproducible state or automated testing
   (it usually does once real users exist). Decide this explicitly during
   spec work, not retroactively during debugging.

4. **Test-first when fixing a bug.** Reproduce the defect as a failing test
   before changing behavior to fix it — the test is the proof the bug
   existed and the guard that it stays dead. Tests exercise real production
   code paths; avoid test-only branches in production files.

5. **Code health has a shape, not just a pass/fail.** Sensible defaults
   (adjust per project/language): file size warns well before it becomes
   unreadable, nesting depth rarely needs to exceed 3-4 levels, and every
   non-trivial exported function explains its intent. Split along domain
   seams before trimming for length's sake.

6. **Docs move with code.** A behavior change updates its own documentation
   in the same change that makes the change — not as a follow-up someone
   forgets. If the project tracks structured docs/specs (its own equivalent
   of atoms, ADRs, or a living spec doc), those are part of "done," not
   optional polish.

7. **Instrument early if observability will matter.** Retrofitting logging/
   tracing into mature code is expensive; building it in from the first
   service/module is nearly free. This is a judgment call scaled to the
   project — a solo game prototype doesn't need OpenTelemetry, but "how will
   anyone debug this in production" is worth deciding on purpose rather than
   never asking.

## How to use this during spec work

- Read it once while shaping a project's architecture doc, to catch
  principles worth pinning down as explicit early decisions (e.g. "state is
  `fold(seed, action_log)`" is principle 3 made concrete for a specific
  project — mancala's own docs already do exactly this).
- Don't force all seven into every spec. Only the ones that matter for the
  system being designed are worth a decision; the rest can stay silent
  defaults for a game prototype and hard requirements for a paid service.
- Never treat this file as a gate that blocks a spec from proceeding — it is
  a prompt for questions worth asking out loud, not a checklist to satisfy
  before "done."
