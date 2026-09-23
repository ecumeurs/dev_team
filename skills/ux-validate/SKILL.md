---
name: ux-validate
description: Use when ux-critic is invoked as validator — by ux-writer when a section of the ui_ux/ document tree is declared complete, or by a user asking whether a design set is ready to build — to check Tier 1 ↔ Tier 3 coherence, alignment against settled product behavior, and token/ID discipline, returning ALIGNED / DRIFT / BLOCKED.
---

# UX Validator Mode

Read the relevant tier documents and check three things.

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

**Token discipline.** No raw values in any Tier 3 document — no pixel sizes,
hex colors, or millisecond durations where a token name belongs. Every
component and class a handoff references exists in `ui_common.css` (or the
project's token source). Every component state the design uses is defined in
the state matrix, including `:focus-visible`. Every responsive behavior cites
a named breakpoint rather than a number.

**Also check the ID discipline**: no question or decision ID (`Q4`, `D7`, or
equivalent) appears in any tier document. Those belong only in `qna.md` and
`decisions.md`, which point into the tier docs and never the reverse.

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
