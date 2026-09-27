---
name: intent-preflight
description: Use when documentalist, in a repo with an intent register (`intent/README.md`, no `.atd`), is called by a leader (coding-leader or coordination-leader) before a plan is finalized, to find which intent-register entries govern the area about to change and surface conflicts or missing business coverage (trigger D, preflight business-alignment check — full D1/D2 pass or fast-path D-peek).
---

# Intent Preflight Business-Alignment Check

This is the only trigger that runs *before* a plan is finalized rather than
after code changes. A leader calls you twice around its own exploration step
— once before it, once after — except on the fast/trivial path, where a
single collapsed **peek** replaces both. You never implement or edit
application code in this workflow; your output is a verdict the calling
leader must act on before proceeding.

Read `intent/README.md` first on every call: Vision and Contract frame every
classification below.

## D1 — Natural-language preflight (called before code exploration)

The leader hands you the task in its own words — no file paths yet, because
none have been identified. Your job is to find what, if anything, already
governs this area of the business.

1. **Search by meaning, not by guessing IDs.** Pull the task's nouns, verbs
   and synonyms, and search the register for each:
   `grep -rn -i -E '<term1>|<term2>|…' intent/`. Search
   `Intent:`, `Rule:`, `Decision:` and `Expectation:` lines, not only
   headings. Widen the terms once if the first pass finds nothing; an empty
   result on one phrasing is not evidence of no coverage.
2. **Read, don't just list, the top candidates.** For every plausible
   candidate, read the whole entry and every architecture entry whose
   `Serves:` names it. Compare its `Rule`/`Decision` and `Expectation`
   against what the leader described wanting to do.
3. **Classify the result:**
   - **Grounded, no conflict** — one or more entries already cover this area
     and the described change doesn't contradict them. Report the governing
     entry IDs and clear the leader to proceed to code exploration.
   - **Grounded, but touches a `confirmed` business entry or a Contract
     line** — flag this now, before any code is written, so the leader knows
     a sign-off step is coming, not a surprise at close-out.
   - **Grounded, but contradicts an entry** — the task would change what an
     entry says the product does. That is a change to declared intent, not an
     implementation detail: report the entry and the contradiction. A `draft`
     entry can be revised once the user agrees; a `confirmed` one needs the
     user's explicit agreement first. Either way the verdict is
     PROCEED-WITH-SIGNOFF-PENDING at best, never a plain PROCEED.
   - **No governing entry found, but the task description gives enough to
     infer one** — draft a business entry (ID, `Intent`, `Rule`,
     `Expectation`, `Source: preflight, task "<task>"`, `Status: draft`).
     Check it against Vision and Contract first. If it fits both as they
     stand, write it to `business.md` as `draft`, run the consistency checks,
     and report it with verdict PROCEED-WITH-SIGNOFF-PENDING so the leader
     puts it in front of the user. **If it doesn't fit — it would expand past
     Vision's scope, or remove or weaken a Contract line — write nothing.**
     Propose the entry *and* the Vision/Contract change it would require side
     by side, and hand back HALT-NEEDS-CONTRACT-VISION-DECISION: changing
     scope or guarantees is never your call to make alone.
   - **No governing entry, and the task description doesn't give enough to
     infer one (or gives contradictory information)** — do not invent
     anything. Hand back HALT-NEEDS-USER-INPUT with exactly what you found
     (near-miss entries, if any, and why they don't fit) so the leader can
     put a precise reformulation question to the user instead of guessing.
4. **Report per Output format** (core agent instructions), with a one-line
   verdict the leader can act on: PROCEED / PROCEED-WITH-SIGNOFF-PENDING /
   HALT-NEEDS-USER-INPUT / HALT-NEEDS-CONTRACT-VISION-DECISION.

## D2 — Refinement (called after code exploration)

The leader now has real file/module targets (where new code will live, or
what existing code will be modified/removed). Re-run the check against
reality, not just the task description.

1. **Read the code links in the actual targets.** For every in-scope file,
   `grep -n '@intent' <file>`. For a file that will be deleted or heavily
   rewritten, also find the tests that cover the same IDs:
   `git grep -n '@intent <id>'`.
2. **Trace the blast radius of every ID found.** Read each tagged entry;
   for a business entry, read every architecture entry that `Serves` it;
   for an architecture entry, read the business entries it `Serves` and the
   other architecture entries serving the same ones. Note every other file
   that carries the same tag (`git grep -l '@intent <id>'`): that is code the
   leader's change can break without touching it.
3. **Reconcile D1 candidates against D2 findings.** The natural-language
   pass in D1 and the file-driven pass here should mostly agree; when they
   don't (D1 found a candidate that no in-scope file is tagged with, or D2
   turns up a tag on an in-scope file that D1's search never surfaced), that
   mismatch is itself worth reporting — it usually means the task touches
   more (or less) of the business surface than the task description implied.
   Untagged in-scope files are not evidence of no governance: code from
   before the register, or from a cold start, may be untagged. Fall back to
   the D1 search for them.
4. **Same classification and verdict scale as D1**, now grounded in real
   code: PROCEED / PROCEED-WITH-SIGNOFF-PENDING (a `confirmed` business
   entry or a Contract line in the blast radius) / HALT-NEEDS-USER-INPUT /
   HALT-NEEDS-CONTRACT-VISION-DECISION. A change that looked grounded in D1
   can still surface a confirmed-entry collision here once real files are
   known — don't treat D1's verdict as final.
5. **Report per Output format** (core agent instructions).

## D-peek — Fast/trivial-path variant

For a single-file, obvious-target change, the leader is not expected to run
the full D1/D2 pair, but it must still give you a peek before proceeding —
skipping the check entirely on the fast path is exactly the kind of
unchecked blast radius your role exists to catch. Collapse D1+D2 into one
lightweight call:

1. `grep -n '@intent' <file>` (the file is already known — the leader's
   whole premise on this path is that the target is obvious), plus one
   register search for the task's main term as a cheap cross-check, plus
   the Contract lines in `intent/README.md`.
2. If any of that turns up a `confirmed` business entry or a Contract line
   in the blast radius, or no entry at all with the description also giving
   too little to infer one — escalate to a full D1/D2 pass rather than
   guessing on a shortened procedure. A "trivial" file-level judgment does
   not override a business-intent governance question.
3. Otherwise, a one-line PROCEED with the matched entry ID(s) (or an
   explicit "no governing entry, none plausible, nothing to infer,
   low-risk mechanical change" note) is sufficient — this is meant to be
   cheap, not a rerun of the full workflow.
