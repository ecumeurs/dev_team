---
name: intent-architecture-capture
description: Use when documentalist, in a repo with an intent register (`intent/README.md`, no `.atd`), is called once a leader has settled a concrete architectural decision during planning, before any code is written, to record that decision as an intent-register architecture entry (trigger E, pre-code architecture capture).
---

# Intent Pre-Code Architecture Capture

Trigger: a leader has finished planning — the intent-preflight skill already
ran, governing business entries are known — and the plan itself now
includes a concrete architectural decision: a new or changed API, entity,
module, service, UI flow, or specification. Your job is to put that decision
on record in `intent/architecture.md` before the leader hands off to
`coding-executor`, so the entry reflects what was *decided*, not what
implementation happened to produce.

This workflow never touches code or `@intent` tags — the code doesn't exist
yet. Tags go on as the implementer writes the code, and the
intent-post-task-sync skill checks them once it lands.

`ux-writer` can also call you with a settled flow set from its `ui_ux/`
tree. Treat each flow as a UI-flow decision. Work only from the tier
documents it forwards (strategy, flow `intent.md`/`handoff.md`, screen
documents) — never from `open-questions.md`, `decisions.md` or `todo.md`,
which hold unsettled and superseded material you must not record.

1. **Reuse the preflight, don't redo it.** The governing business entries
   should already be known from the intent-preflight skill's D1/D2 pass for
   this task. Only search again if the decision has moved outside the area
   D1/D2 originally checked.
2. **Check for a near miss first.** Search `architecture.md` for the
   decision's subject (`grep -n -i -E '<terms>' intent/architecture.md`, or
   across `intent/architecture/` once split). A refined or extended version
   of an existing API/entity/module usually means revising that entry, not
   adding a fresh one. Reserve a new entry for architecture the project
   genuinely didn't have before.
3. **Check the parents.** Every entry you write needs `Serves:` with at
   least one existing business entry that isn't `retired`. If the business
   entry the decision serves doesn't exist, stop and report it as missing —
   it should have come out of preflight. Don't invent one here.
4. **Write or revise the entry.** Fields: `Status: draft`, `Serves:`,
   `Decision:` (what the API/entity/module/service/flow is and does, and its
   shape — not how it will be coded), `Why:` (the reasoning and the
   alternatives the leader rejected), `Expectation:` (a checkable property
   the code must satisfy), `Source: planning decision, task "<task>"`. One
   decision per entry. Restate the decision in full; never lean on the
   leader's plan text or a `ux D`/`spec D` ID to complete its meaning. If
   the entry you'd revise is `confirmed`, don't edit it: report the revision
   you'd make and ask for the user's sign-off through the leader.
5. **Run the consistency checks** (format reference,
   `~/.local/share/dev_team/references/intent-register.md`).
6. **Report the entry ID(s) back to the leader** so they carry into the
   `coding-executor` handoff, where they become the `@intent` tags on the
   code that implements them. That's what lets the post-task sync check the
   code against a decision that already exists instead of inventing one from
   the diff.
