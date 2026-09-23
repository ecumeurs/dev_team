---
name: spec-access-model
description: Use when spec-writer's product has more than one kind of user, to produce the access model companion document stating who exists, what each may do, and what happens when they try something they may not — required by ux-writer, coding-leader, and documentalist.
---

# The Access Model Document

Whenever the product has more than one kind of user, the master spec ships
with a companion: an **access model** document stating who exists, what each
may do, and what happens when they try something they may not. Follow the
layout in `~/.local/share/dev_team/references/access-model-template.md`.

This is a real deliverable, not an appendix, because three downstream agents
are barred from inventing this material and stall without it: `ux-writer`
(which screens each role reaches, and what a denial looks like on screen),
`coding-leader` (enforceable rules rather than intent), and `documentalist`
(atomizes it into BUSINESS-layer atoms, which needs each rule self-sufficient).

Start it as an ordinary draft topic doc during inception — partial matrix,
`(proposed)` entries, `?` cells, open-question IDs inline are all fine and
normal there. It graduates to a final companion under the same rule as the
master spec itself: complete, no `?` cells, and **free of internal tracking
IDs**, with anything still unresolved restated in plain language under
*Known gaps*.

Two failure modes are worth naming because they look finished and aren't. A
blank matrix cell is indistinguishable from an operation nobody thought
about — mark it `?` and resolve it rather than leaving it empty. And "deny"
alone is not an answer: whether a forbidden resource is *hidden* (filtered
from lists, 404 on direct access) or *visible-but-blocked* (shown, with a
request-access path) is a product decision that changes what `ux-writer`
designs, so decide it per operation class rather than leaving it to
implementation.

Run the template's completeness check before treating the document as final.
