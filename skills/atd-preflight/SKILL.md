---
name: atd-preflight
description: Use when documentalist is called by a leader (coding-leader or coordination-leader) before a plan is finalized, to find which atoms govern the area about to change and surface conflicts or missing business coverage (ATD trigger D, preflight business-alignment check — full D1/D2 pass or fast-path D-peek).
---

# ATD Preflight Business-Alignment Check

This is the only trigger that runs *before* a plan is finalized rather than
after code changes. A leader calls you twice around its own exploration step
— once before it, once after — except on the fast/trivial path, where a
single collapsed **peek** replaces both. You never implement or edit
application code in this workflow; your output is a verdict the calling
leader must act on before proceeding.

## D1 — Natural-language preflight (called before code exploration)

The leader hands you the task in its own words — no file paths yet, because
none have been identified. Your job is to find what, if anything, already
governs this area of the business.

1. **Query by meaning, not by guessing IDs.** `atd search --query "<task in
   plain language>"` (semantic search over atoms) is the primary tool here —
   this is exactly the "find existing atoms before creating new ones" use
   case. Follow up with `atd query --field <field> --search <value>` for any
   keyword/type/tag lead the semantic search surfaces (e.g. narrowing to
   `type=RULE` or a suspected `tags` value).
2. **Read, don't just list, the top candidates.** For every plausible
   candidate atom, read the file (not just the frontmatter snippet) — compare
   its `## INTENT` and `## THE RULE / LOGIC` against what the leader
   described wanting to do.
3. **Classify the result:**
   - **Grounded, no conflict** — one or more BUSINESS/ARCHITECTURE atoms
     already cover this area and the described change doesn't contradict
     them. Report the governing atom IDs and clear the leader to proceed to
     code exploration.
   - **Grounded, but touches a STABLE or BUSINESS atom** — flag this now,
     before any code is written, so the leader knows a sign-off step is
     coming, not a surprise at close-out.
   - **No governing atom found, but the task description gives enough to
     infer one** — draft a BUSINESS atom proposal (id, type, layer, intent)
     the same way the atd-spec-ingestion skill drafts BUSINESS atoms from a
     spec: as a DRAFT, clearly flagged pending confirmation. Before proposing
     it, read the project's CONTRACT and VISION atoms (`atd query --field
     type --search CONTRACT` / `... VISION`) per the governance gate. If the
     proposal fits within both as they stand, materialize it as DRAFT and
     report it alongside the verdict. **If it doesn't fit — it would remove a
     CONTRACT invariant or expand past VISION's scope — do not materialize
     anything.** Propose the BUSINESS atom *and* the CONTRACT/VISION change
     it would require side by side, and hand back a hard stop: this needs
     explicit user agreement before any of it is created, per ATD's own
     governance rule (ATD.md §1.4 — overriding CONTRACT/VISION always
     requires updating them to match, and that is never your call to make
     alone).
   - **No governing atom, and the task description doesn't give enough to
     infer one (or gives contradictory information)** — do not invent
     anything. Hard stop. Hand back exactly what you found (near-miss atoms,
     if any, and why they don't fit) so the leader can put a precise
     reformulation question to the user instead of guessing.
4. **Report per Output format** (core agent instructions), with a one-line
   verdict the leader can act on: PROCEED / PROCEED-WITH-SIGNOFF-PENDING /
   HALT-NEEDS-USER-INPUT / HALT-NEEDS-CONTRACT-VISION-DECISION.

## D2 — Refinement (called after code exploration)

The leader now has real file/module targets (where new code will live, or
what existing code will be modified/removed). Re-run the check against
reality, not just the task description.

1. **Map the actual targets.** For every file the leader identified as
   in-scope, `atd map --file <path>` (no `--atom`) to surface existing
   `@spec-link` candidates already tied to that file, and `atd map --file
   <path> --new` for files with no plausible existing match.
2. **Trace blast radius on anything that matched.** For every atom found
   linked to an in-scope file, `atd trace <atom_id> --summary` — this is
   ATD's own mandatory pre-change step, not optional diligence. Read the
   `graph_slice` (parents/dependents/code_links/test_links) to see who else
   depends on the atom the leader is about to touch, not just the atom
   itself.
3. **Reconcile D1 candidates against D2 findings.** The natural-language
   pass in D1 and the file-driven pass here should mostly agree; when they
   don't (D1 found a candidate atom that no in-scope file actually links to,
   or D2 turns up a `@spec-link` on an in-scope file that D1's query never
   surfaced), that mismatch is itself worth reporting — it usually means the
   task touches more (or less) of the business surface than the task
   description implied.
4. **Same classification and verdict scale as D1**, now grounded in real
   code: PROCEED / PROCEED-WITH-SIGNOFF-PENDING (STABLE/BUSINESS atom in the
   blast radius) / HALT-NEEDS-USER-INPUT / HALT-NEEDS-CONTRACT-VISION-DECISION.
   A change that looked grounded in D1 can still surface a STABLE-atom
   collision here once real files are known — don't treat D1's verdict as
   final.
5. **Report per Output format** (core agent instructions).

## D-peek — Fast/trivial-path variant

For a single-file, obvious-target change, the leader is not expected to run
the full D1/D2 pair, but it must still give you a peek before proceeding —
skipping ATD entirely on the fast path is exactly the kind of unchecked blast
radius your role exists to catch. Collapse D1+D2 into one lightweight call:

1. `atd map --file <path>` (the file is already known — the leader's whole
   premise on this path is that the target is obvious) plus one `atd search
   --query "<short task description>"` as a cheap cross-check.
2. If either turns up a STABLE/BUSINESS atom in the blast radius, or no atom
   at all with the description also giving too little to infer one —
   escalate to a full D1/D2 pass rather than guessing on a shortened
   procedure. A "trivial" file-level judgment does not override a
   BUSINESS-layer governance question.
3. Otherwise, a one-line PROCEED with the matched atom ID(s) (or an explicit
   "no governing atom, none plausible, nothing to infer, low-risk mechanical
   change" note) is sufficient — this is meant to be cheap, not a rerun of
   the full workflow.
