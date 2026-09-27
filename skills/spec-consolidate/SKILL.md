---
name: spec-consolidate
description: Use when spec-writer's user has confirmed the project (or a specific feature) is ready to move to coding-leader, to consolidate the current draft documents into the single master spec deliverable.
---

# The Master Spec Document

Draft documents are your working set. The **master spec** is a separate,
single deliverable you produce only when the user confirms the project (or
the specific feature) is ready to move to `coding-leader`. It lives at
`specs/versions/<version>/master-spec.md`, or at `specs/master-spec.md` in a
project without versions. It consolidates
the current state of the drafts into one execution-ready document:

- Core concept/objective, stated plainly.
- Scope: what's in, what's explicitly out.
- Personas and goals served, when the spec has a personas document: the
  primary and secondary personas, one line each with their IDs; each goal
  this spec serves, stated in full with its ID and whether it is served
  fully or partially (and how); goals knowingly deferred; and the persona
  tensions settled for this scope. Enough to read on its own — the personas
  document stays the full reference `ux-writer` designs from.
- Mechanics/behavior, precisely enough to build without further design
  decisions hiding inside the spec.
- Definition of done / acceptance criteria.
- For features on an existing codebase: the relevant existing modules,
  patterns, and constraints identified during grounding, and any part of the
  system flagged as at-risk of disruption.
- Architectural decisions that were made, with the reasoning, not just the
  conclusion.
- Explicitly deferred items and remaining open questions that were
  consciously left for `coding-leader` to resolve during implementation
  (never silently drop a still-open question by omitting it here).

**The master spec must be free of internal tracking IDs.** Draft documents
reference open questions and decisions by their register/log ID (`O4`, `D7`)
as shorthand — that's fine for your own working set. The master spec is a
different kind of document: state each deferred item, open question, and
architectural decision's reasoning in full plain language instead, with no
`O#`/`D#` (or equivalent) citation standing in for the content. The master
spec, with its access model, is all the intent owner (`documentalist`, or
`intent-keeper` without ATD) ever ingests (never the register or log
themselves), and per its own self-sufficiency requirement an atom or intent
entry can't mean anything by reference to an ID from a document it will never
see — so nothing upstream of it may either. Persona and goal IDs (`P1`,
`P1.G2`) are the exception: they are content identifiers, defined in the
personas document and restated in full in the master spec's personas section,
not pointers into a register — cite them freely.

Don't consolidate early to "show progress." A half-settled master spec hides
its own gaps behind a look of completeness; the split drafts plus open-Q
register are the honest state of an unfinished spec.
