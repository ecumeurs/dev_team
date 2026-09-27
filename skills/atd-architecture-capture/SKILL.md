---
name: atd-architecture-capture
description: Use when documentalist is called once a leader has settled a concrete architectural decision during planning, before any code is written, to materialize the ARCHITECTURE-layer atom for that decision (ATD trigger E, pre-code architecture capture).
---

# ATD Pre-Code Architecture Capture

Trigger: a leader has finished planning — the atd-preflight skill already
ran, governing BUSINESS atom(s) are known — and the plan itself now includes
a concrete architectural decision: a new or changed API, entity, module,
service, UI flow, or specification. Your job is to put that decision on
record as an ARCHITECTURE-layer atom before the leader hands off to
`coding-executor`, so the atom reflects what was *decided*, not what
implementation happened to produce.

This workflow does not touch IMPLEMENTATION-layer atoms or `@spec-link`
tags — implementation details aren't decided yet at this point, only the
architecture is. Those stay the atd-post-task-sync skill's job, once code
exists.

1. **Reuse the preflight, don't redo it.** The governing BUSINESS atom(s)
   should already be known from the atd-preflight skill's D1/D2 pass for
   this task. Only re-run a search (`atd search --query "..."`) if the
   leader's decision has moved outside the area D1/D2 originally checked.
2. **Check for a near-miss first.** `atd query --field layer --search
   ARCHITECTURE` plus `atd search --query "<the decision, in plain
   language>"` — a refined or extended version of an existing API/entity/
   module usually means `atd update` on that atom, not a fresh one. Reserve a
   new atom for architecture the project genuinely didn't have before.
3. **Classify by ATD type**: API, ENTITY, MODULE, SERVICE, UI, or
   SPECIFICATION, per Atom anatomy in the ATD manual
   (`~/.local/share/dev_team/references/atd-atoms.md`). Check `atd config bloating-factor <TYPE>` before drafting
   content, same as everywhere else.
4. **Materialize or update the atom**: `atd update --set id=<id> --set
   type=<TYPE> --set layer=ARCHITECTURE --set status=DRAFT --set
   parents=[[<business_atom_id>]] --intent "..." --logic "..." --interface
   "..." --expectation "..."`. `## THE RULE / LOGIC` should state the
   decision itself (what the API/entity/module/service/flow does and why),
   not implementation mechanics — those don't exist yet. If it was
   previously STABLE (a revised architectural decision), the same
   STABLE+BUSINESS `--force` guard applies; don't bypass it without explicit
   confirmation. Confirm the id from the command's own output before treating
   a new atom as created (see the ATD manual's CLI quick reference) — the leader will carry
   whatever id you report straight into the `coding-executor` handoff, so an
   unconfirmed or wrong id here propagates directly into `@spec-link` tags on
   real code.
5. **Weave and lint.** `atd weave`, `atd lint` — same close-the-loop
   discipline as every other workflow.
6. **Report the atom ID(s) back to the leader** so they carry into the
   `coding-executor` handoff as context — this is what lets the
   atd-post-task-sync skill, once code lands, add `@spec-link` to an atom
   that already exists instead of inventing one from the diff.
