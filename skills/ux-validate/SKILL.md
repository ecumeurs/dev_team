---
name: ux-validate
description: Use when ux-critic is invoked as validator — by ux-writer when a section of the ui_ux/ document tree is declared complete, or by a user asking whether a design set is ready to build — to check Tier 1 ↔ Tier 3 coherence, alignment against settled product behavior and personas, and token/ID discipline, returning ALIGNED / DRIFT / BLOCKED.
---

# UX Validator Mode

Read the relevant tier documents and check four things.

**Tier 1 ↔ Tier 3 coherence.** The flow index in `strategy.md` lists exactly
the flows that exist in `flows/` — no phantom entries, no unlisted folders.
The edge-case policy in `strategy.md` (empty, loading, error, permission
denial, offline) is actually applied in each screen's `handoff.md`, not just
declared once at the top. No screen's design contradicts the strategy that
produced it. Every screen a flow's `handoff.md` names exists in `screens/`,
and every screen in `screens/` is reachable from some flow.

**Alignment against settled product behavior.** Read the master spec if one
exists; otherwise ATD BUSINESS atoms in a repo with a `.atd` config. Flows
must not contradict settled behavior, and must not quietly introduce business
rules — a screen that invents a permission check, a role distinction, or a
state transition the spec doesn't have is a BLOCKED finding regardless of how
sensible the design is. That decision belongs to `spec-writer`.

**Persona alignment.** When the spec has a personas document (usually in
`specs/`), read it. `strategy.md` designs for its personas, primary first, and
draws its context of use and mental models from them; each flow's `intent.md`
names the persona goals it serves; and every goal the master spec assigns to
the milestone that needs an interface is served by some flow or logged in
`open-questions.md`. A missing citation or an unserved goal is DRIFT. A
persona, or a persona trait — a goal, a context of use — that the personas
document doesn't have is BLOCKED, routed to `spec-writer`, exactly like an
invented business rule. With no personas document, don't manufacture a
finding; note its absence in one line only when the strategy's reasoning
visibly rests on unstated assumptions about who the user is.

**Token discipline.** No raw values in any Tier 3 document — no pixel sizes,
hex colors, or millisecond durations where a token name belongs. Every
component and class a handoff references exists in `ui_common.css` (or the
project's token source). Every component state the design uses is defined in
the state matrix, including `:focus-visible`. Every responsive behavior cites
a named breakpoint rather than a number.

**Also check the ID discipline**: no question or decision ID (`Q4`, `D7`, or
equivalent) appears in any tier document. Those belong only in
`open-questions.md` and `decisions.md`, which point into the tier docs and
never the reverse. Persona and goal IDs (`P1`, `P1.G2`) are not tracking IDs —
they are defined in the spec's personas document — and are allowed.

Return exactly one verdict:

- **ALIGNED** — the section is coherent, spec-aligned, and token-disciplined.
  Ship it. List nothing you'd merely have done differently.
- **DRIFT** — real inconsistencies exist that the writer can fix without a
  product decision. List them, each with the two locations that disagree and
  which one you believe is correct.
- **BLOCKED** — the section can't be validated as-is: it contradicts settled
  product behavior, introduces a business rule that isn't the writer's to
  make, or depends on something that doesn't exist. Say precisely what and
  who has to resolve it.

At most five findings. If there are more than five, the section isn't
finished and saying so plainly is more useful than an exhaustive list.
