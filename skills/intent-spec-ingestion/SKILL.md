---
name: intent-spec-ingestion
description: Use when documentalist, in a repo with an intent register (`intent/README.md`, no `.atd`), is handed a spec-writer master spec (initial, or a milestone refinement) to create or update the intent register's business entries, Vision and Contract against the spec's current state (trigger C, spec ingestion).
---

# Intent Spec Ingestion

The input is a finished (or "finished-for-now") master spec from
`spec-writer`, and its access model when the product has more than one kind
of user. Sometimes the project has no code yet; sometimes it's mid-project
and spec-writer has refined objectives or mechanics for the next milestone.
This workflow stays at the business level: it never writes architecture
entries or `@intent` tags. Those come from a leader's architecture capture
before code, or from the post-task sync once code lands.

1. **Check the markers.** If `.atd` exists, this is an ATD repo: stop and
   use skill `atd-spec-ingestion` instead. If `intent/README.md` is absent,
   bootstrap the register from the layout in the format reference
   (`~/.local/share/dev_team/references/intent-register.md`) and add the
   `## Declared intent` section to the project instructions (see the core
   agent instructions). On a
   milestone refinement it already exists.
2. **Work from the master spec and its access model alone.** You should
   only ever be handed those — never spec-writer's index, open-questions
   register, decisions log, Q&A transcripts, personas document or other
   working material. If any of that reaches you anyway, don't read it for
   ingestion. The master spec carries its own `Status:` line, states settled
   items as fact, and tags tentative ones `(proposed)` inline. Sort its
   content into two buckets: **settled** — stated plainly, not tagged
   `(proposed)`, not listed in the spec's own deferred/open section — which
   becomes entries; and **still open** — anything `(proposed)`, blocked, or
   named in that section — which gets skipped (step 7). Treat the status
   line as ground truth about how much of the document is settled: a spec
   marked as having blocking gaps is not all settled. On a milestone
   refinement, spec-writer's handoff should say in plain language what
   changed since the last ingestion; use that pointer to scope your pass,
   and fall back to a full re-read if there is none.
3. **On a milestone refinement, find what already exists before drafting.**
   Search `business.md` for every spec section under consideration. A
   refined objective or mechanic usually means revising an existing entry,
   not adding a new one. Revising a `draft` entry is yours to do. Revising
   the meaning of a `confirmed` entry needs the user's sign-off: write the
   revision into your report as a proposal and leave the entry unchanged.
4. **Establish or reconcile Vision and Contract** in `intent/README.md`:
   - **Vision** (scope): draft it from the spec's core concept and its
     in-scope/out-of-scope framing. It can be complete at cold start, with
     zero code.
   - **Contract** (guarantees): only `confirmed` entries back a Contract
     line, and nothing you write here is `confirmed`, so Contract stays
     **thin** — not a list of every feature the spec describes. The one
     exception: a genuinely non-negotiable "never X" invariant the spec
     states as absolute from day one (security, safety, data integrity —
     not a feature). Propose it as a business entry and a Contract line, and
     mark that entry `confirmed` only with the user's explicit confirmation,
     relayed through whoever invoked you, that it is settled now and not
     aspirational.

   On a refinement where both already exist, propose a change only if this
   milestone alters the core objective (Vision) or removes or narrows a
   guarantee (Contract). Most refinements sharpen mechanics without touching
   either, so "no change needed" is the expected default. Either way, a
   Vision or Contract change is a proposal for the user, flagged as such in
   your report, never a settled edit.
5. **Split the settled content into entries.** Read each section whole,
   then list proposed entries (ID, one-line intent, spec section) in your
   working notes and check the list for overlap and gaps before writing.
   One state-changing rule per entry: a paragraph stating three rules is
   three entries. A workflow a user walks through can be one entry when its
   steps are one rule; an invariant is always its own entry. Each access
   model rule (who may do what, and what happens when they may not) is an
   entry of its own.
6. **Write the entries.** `Status: draft`, `Source: master spec vN` (and
   `access model` for its rules), each field a self-sufficient statement of
   the rule — never "see §4" or a spec `D`/`O` ID. Quote the spec inline if
   its wording matters. A milestone revision reopens confidence: a revised
   `draft` entry stays `draft`.
7. **Skip what isn't settled.** Don't write an entry for a `(proposed)`
   section or one in the spec's deferred/open list, and don't fold it into
   another entry as an incidental detail. An entry is a claim about decided
   state. Note each skipped section in your report (its heading, plus one
   line in your own words on what's unresolved). If two sections contradict
   each other, that is an open question by definition: skip both, and flag
   the contradiction for spec-writer or the user. When only part of a
   section is settled, write the settled part alone.
8. **Flag downstream drift, don't chase it.** If an entry you revised has
   architecture entries serving it, or `@intent` tags in code
   (`git grep -l '@intent <id>'`), list them in your report as needing a
   post-task-sync-style drift check. Don't assume they still match, and
   don't edit them here.
9. **Run the consistency checks** from the format reference. On a pre-code
   project expect zero `@intent` tags; that's correct, not a defect.
10. **Report** what was created versus revised, the Vision/Contract proposal
    or reconciliation (flagged for sign-off), every skipped section with its
    reason, every downstream item flagged per step 8, and the check results
    (see Output format in the core agent instructions).
