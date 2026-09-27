---
name: atd-spec-ingestion
description: Use when documentalist is handed a spec-writer master spec (initial cold-start or milestone refinement) to extract or update BUSINESS-layer (and CONTRACT/VISION) atoms against the spec's current state (ATD trigger C, spec ingestion).
---

# ATD Spec Ingestion

Neither cold-start extraction nor post-task sync fits this case cleanly:
cold-start assumes code to `roadmap` and manually dissect; post-task sync
assumes a git diff. Here the input is a finished (or "finished-for-now")
master spec document from spec-writer — sometimes on a project with no code
yet (cold-start extraction), sometimes mid-project, where spec-writer has
refined objectives or mechanics for the next milestone and code already
exists. Adapt the cold-start shape — run the Manual Dissection Protocol
(ATD manual, `~/.local/share/dev_team/references/atd-atoms.md`) against the *document* instead of code, materialize
or update DRAFT atoms, verify, report. Either way this workflow stays at the
BUSINESS layer: it never originates `@spec-link`/`@test-link` tags or
ARCHITECTURE/IMPLEMENTATION atoms itself — origination of those happens once
a leader settles the architecture (atd-architecture-capture, before code) or,
for anything that slips past planning, once implementation catches up
(atd-cold-start/atd-post-task-sync).

1. **Bootstrap if needed.** `atd init` if no `.atd` exists, then add the
   `## Declared intent` section to the project instructions (see the core
   agent instructions). Don't fight the
   pre-commit hook or the `req_tech_debt_backlog` atom it installs. On a
   milestone refinement `.atd` will already exist; this step is a no-op then.
2. **Work from the master spec document alone.** You should only ever be
   handed the master spec itself — never spec-writer's index, Open Questions
   register, Decisions log, Q&A transcripts, or other working material (see
   principle 4, decided state, in the core agent instructions). The master spec is
   required to carry its own `Status: draft vN` line and to state settled
   items as fact while tagging tentative ones `(proposed)` inline, so it's
   sufficient on its own to sort its content into two buckets: **settled
   fact**, stated plainly and not tagged `(proposed)` and not listed under
   the spec's own "deferred/open" section — this is what step 5 onward may
   turn into atoms — and **still open**, anything `(proposed)`, blocked, or
   named in that deferred/open section — this gets skipped on ingestion, not
   atomized (see step 9). **Do not assume the master spec is internally
   consistent** — spec-writer's own review gate can leave it in a "draft,
   blocking gaps found" state (visible in that same status line, or
   unresolved items in §9-style "gaps carried forward" sections); treat the
   status line as ground truth about how much of the document falls in the
   settled bucket. On a milestone refinement, spec-writer's handoff should
   say in plain language what changed since the last ingestion — use that
   pointer (not a forwarded log document) to scope which sections likely
   moved from "open" to "settled," and fall back to a full re-read of the
   document if no such pointer is given.
3. **On a milestone refinement, find what already exists before drafting
   anything new.** Query existing BUSINESS-layer atoms (`atd query --field
   layer --search BUSINESS`, `atd search --query "<mechanic>"`) for the spec
   sections under consideration. A refined objective or mechanic usually
   means an existing atom needs `atd update` (revised INTENT/LOGIC/
   EXPECTATION), not a fresh atom — reserve new atoms for material the spec
   didn't previously cover. This is the same "no duplicate BUSINESS atom"
   discipline as the atd-preflight skill's near-miss check, applied to spec
   ingestion instead of code exploration. Skip this step on a true
   cold-start (nothing to collide with yet).
4. **Establish or reconcile CONTRACT and VISION.** Per ATD.md §1.4, exactly
   one of each must exist project-wide (query for existing ones first), and
   neither is ever a `parents:` target for any other atom — they're read for
   governance, not linked as ancestry (see ATD hard rules in the ATD
   manual). VISION and CONTRACT are separate axes and get built up
   differently:
   - **VISION** (scope): draft it from the spec's core concept/objective +
     in-scope/out-of-scope framing, same as before — it doesn't gate on
     `STATUS`, so it can be fully drafted at cold-start even with zero code.
   - **CONTRACT** (guaranteed surface): per the Contract Surface Grid (ATD.md
     §1.4), only `STABLE` atoms count. At a true pre-code cold-start, almost
     nothing should be `STABLE` yet — everything you materialize here lands
     at `DRAFT` (step 11) — so CONTRACT should stay **thin**, not a
     speculative list of every feature the spec describes. The one
     exception: a genuinely non-negotiable "never X" invariant the spec
     states as absolute from day one (a security/safety/data-integrity
     constraint, not a feature) can be proposed as a BUSINESS-layer `RULE`
     atom and, **only with explicit human confirmation that it's truly
     settled now, not aspirational**, marked `STABLE` immediately — a rule
     can be "settled" independent of whether the feature it governs is built
     yet. Parent that `RULE` to whatever real BUSINESS atom actually governs
     it (the REQUIREMENT/USER_STORY/DOMAIN it constrains), never to
     CONTRACT or VISION. Everything else joins CONTRACT's surface later,
     atom by atom, as it's promoted to STABLE post-implementation — that's
     the atd-post-task-sync skill's job, not this one.

   On a milestone refinement where CONTRACT/VISION already exist, don't
   recreate them — only propose an `atd update` if this milestone's changes
   actually alter the core objective (VISION) or remove/narrow an existing
   STABLE guarantee (CONTRACT, per the grid); most milestone refinements
   sharpen mechanics without touching either, so "no change needed" is the
   expected default, not an omission to fix. Either way, **these are
   proposals for human confirmation, not settled atoms** — say so explicitly
   in your report. If more than one candidate non-negotiable invariant
   exists, resist creating more than one CONTRACT atom (ATD.md permits
   exactly one) — each becomes its own `RULE` atom, parented to its real
   governing BUSINESS atom, with CONTRACT's own content (or, for this
   project's self-hosting case, its enumerated invariant list) updated to
   reference it instead of the RULE atom pointing back at CONTRACT. `atd
   lint` enforces the CONTRACT-uniqueness rule and will catch a violation,
   but check this yourself before running lint, not after.
5. **Dissect the relevant spec sections manually.** Run the Manual Dissection
   Protocol (ATD manual) directly against the spec document —
   `atd dissect` no longer exists, so there's no shortcut even though it used
   to accept `.md` files. On cold-start, that's the whole document; on a
   milestone refinement, focus on the sections spec-writer's handoff flagged
   as new or changed (step 2) — re-reading the full doc for context is fine,
   but don't re-materialize sections that haven't moved. Read the section
   under consideration, then propose boundaries yourself at full reasoning
   quality.
6. **Classify by content, not by section position.** Map spec sections to
   atom types deliberately: scope/mechanics → `REQUIREMENT`; a workflow the
   end user walks through → `USER_STORY`; a single invariant or constraint →
   `RULE`; narrative "why" context → `DOMAIN`. Check `atd config
   bloating-factor <TYPE>` before writing — `RULE` (~0.8) must be one
   constraint per atom, so a spec paragraph covering three related rules
   needs three RULE atoms, not one; `USER_STORY`/`REQUIREMENT` narrative
   tolerance is looser but still isn't a license to dump the whole section
   into one atom's INTENT unedited.
7. **Materialize new atoms as DRAFT, or `atd update` existing ones**,
   parented to a real BUSINESS ancestor per "No Parent, No Code" (which
   applies here as "no parent, no atom" — every BUSINESS atom still needs a
   traceable root) — **never to `contract_atd`/`vision_atd` themselves** (see
   ATD hard rules in the ATD manual); a fresh top-level concern parents to the nearest
   existing REQUIREMENT/DOMAIN atom, or, if truly nothing fits yet, stays
   flagged in your report as needing a new top-level BUSINESS atom rather
   than borrowing CONTRACT/VISION as a stand-in parent. Use `atd update --set
   id=<id> --set type=<TYPE> --set layer=BUSINESS --set status=DRAFT
   --intent "..." --logic "..." --interface "..." --expectation "..."`.
   Write `## THE RULE / LOGIC` and the other sections as fully
   self-sufficient statements of the rule itself — never a pointer back to a
   spec document section, decision ID, or Open-Question ID (principle 5,
   entries stand on their own). If the spec's own wording is worth preserving verbatim, quote it
   inline in the relevant section rather than citing where it lives; the
   atom must still mean the same thing after the spec document is gone.
   Confirm the id from the command's own output before treating a new atom
   as created (see the ATD manual's CLI quick reference) — don't just assume your proposed id
   landed. A milestone revision reopens confidence in that atom — return it
   to DRAFT even if it was previously REVIEW/STABLE. If it was STABLE or
   BUSINESS-layer (it will be both here), the same STABLE+BUSINESS `--force`
   guard applies as everywhere else: don't bypass it without explicit
   confirmation from whoever invoked you.
   - **Multi-parent atoms:** `--set` is parsed by pflag as CSV, so an
     unquoted comma inside a value (e.g. `--set parents=[[a]],[[b]]`) gets
     silently split into two flag values and the second one — lacking a
     `key=`, is silently dropped. **Wrap the entire `key=value` pair in one
     extra layer of double quotes** to keep commas inside a single CSV field:
     `--set '"parents=[[a]],[[b]]"'`. Verify with a re-read of the file after
     any multi-parent `--set`, don't assume it landed.
8. **Still no `@spec-link`/`@test-link`, ARCHITECTURE/IMPLEMENTATION atoms,
   or `atd map` from this workflow — even once code exists.** Originating
   downstream atoms or links is coding-leader's job (via atd-cold-start/
   atd-post-task-sync), not this one. What changes on a milestone refinement:
   if an atom you just updated already has downstream ARCHITECTURE/
   IMPLEMENTATION children or `@spec-link`s from earlier work, flag them in
   your report as needing an atd-post-task-sync-style drift check — don't
   silently assume they still match the revised BUSINESS atom, and don't
   chase the drift down yourself here.
9. **Skip what isn't settled — don't atomize the deliberation.** If a spec
   section is still `(proposed)` or named in the spec's own deferred/open
   list, do not materialize an atom for it and do not fold it into a
   REQUIREMENT/RULE atom as an incidental complication either — an atom is a
   claim about decided state (principle 4), and this isn't decided yet.
   Leave it out of `docs/` entirely; the master spec's own `(proposed)` tag
   or deferred/open listing is where that unresolved status already lives and
   belongs — you don't need spec-writer's Open Questions register to know
   that, and won't have it anyway. Note each skipped section in your report
   (its heading/anchor in the master spec, plus a one-line description of
   what's unresolved, in your own words) so a human can see what wasn't
   ingested and why, without it becoming a permanent graph citizen. If a spec
   section internally contradicts another (e.g. a mechanic requires a
   capability another section defers out of scope), that's a live open
   question by definition — skip both sides the same way, and flag the
   contradiction in your report for spec-writer/human to resolve back in the
   spec, not by picking a side inside an atom. The one exception: if only
   *part* of a section is settled and part is `(proposed)`, materialize an
   atom for the settled part alone (per its own type/bloat rules) rather than
   discarding real, decided content because it shares a paragraph with
   something tentative.
10. **Verify the batch.** `atd weave`, `atd lint` (structural + CONTRACT-
    uniqueness), `atd crawl --gaps` (should show zero orphaned STABLE atoms —
    everything you touched here is DRAFT), `atd check --full`. On a
    cold-start ingestion, expect 0 impl/0 test links — that's correct for a
    pre-code project, not a defect to fix. On a milestone refinement, don't
    expect zero — read the actual numbers, and if links look stale relative
    to the atoms you just touched, that's the drift-check flag from step 8,
    not something to fix yourself here. `atd audit` is optional supporting
    evidence here, not authoritative: its bloat/collision detection is
    LLM-backed, and dense BUSINESS-layer prose plus a misconfigured or weak
    embedding provider can produce noisy false positives on both bloat and
    collision detection. Before trusting an `audit` verdict enough to act on
    it (e.g. running `atd fix` or merging atoms), sanity-check the embedding
    routing (`atd config list` — the task named for embeddings, typically
    `embed`, should point at an actual embedding model, not a chat model) and
    spot-check a couple of flagged pairs by reading the atoms yourself.
    Report a flagged-but-unfixed `audit` finding as-is rather than acting on
    a signal you don't trust.
11. **Leave everything at DRAFT.** Same as cold-start: this is a first
    honest draft (or honest revision) of the BUSINESS layer, not a reviewed,
    human-approved spec. Do not self-promote to REVIEW or STABLE, and do not
    lock CONTRACT/VISION wording — flag both explicitly as pending human
    confirmation.
12. **Report** what was newly created versus updated, the CONTRACT/VISION
    proposal or reconciliation (flagged for sign-off), every spec section
    skipped as not-yet-settled (heading/anchor + one-line reason, per step 9),
    any downstream atoms flagged per step 8, and verification output (see
    Output format in the core agent instructions).
