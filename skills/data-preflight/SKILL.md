---
name: data-preflight
description: Use when data-steward, in a repo with a data register (`data-register/README.md`), is called by a leader (coding-leader or coordination-leader) before a plan is finalized because the plan adds or changes data — a new entity, field, store, log or analytics event carrying user data, a new third party, a new purpose, or a new access path — to say what the register will require of it and whether a human must decide something first (trigger B, data preflight — full pass or peek).
---

# Data Preflight

The leader is about to commit to a plan and calls you before code is
written. You answer three questions: what new or changed data, flows,
purposes, processors or access paths the plan creates; what the register
requires of them; and whether anything needs a human decision before it is
built. **You write nothing to the register here.** What you propose is
recorded by the post-task sync once it exists in code.

Read `data-register/README.md` and `classification.md`, then the format
sections for the entry kinds the plan touches and the baseline
(`~/.local/share/dev_team/references/data-register.md`,
`~/.local/share/dev_team/references/data-security-baseline.md`).

## Full pass

1. **List what the plan touches.** From the leader's description (and file
   paths, if it has them): new or changed entities and fields, new stores
   or copies (cache, index, log, analytics event, export file), new or
   changed flows, new third parties, new uses of existing data, new
   principals or credentials, new end-user operations on sensitive data.
2. **Find the governing entries.** Search the register for each noun and
   its synonyms: `grep -rn -i -E '<term>|<synonym>' data-register/`. Where
   the leader names files, read their `@data` tags. Read each candidate
   entry in full, with the purposes and flows it links to.
3. **Ask minimization first.** For each new field, copy or flow: does the
   plan's purpose need it, all of it, for as long as it would be kept?
   A field that can be dropped or narrowed is the first proposal, before
   any protection.
4. **Classify the new data.** Propose a class and flags for each new item
   from `classification.md`'s definitions. Where an existing item gains a
   new use, check it fits an existing purpose; a new use of personal data
   is a new purpose.
5. **Derive the requirements.** For each new or changed item, its class's
   and flags' `Required` measures. For each new flow crossing a zone, the
   baseline's flow questions. For each new principal or grant, the
   separation-of-duties rules in `responsibilities.md`: does the plan give
   one principal both sides of a rule?
6. **Write the proposals.** Each one argued in the baseline's terms: risk,
   measure ID, what it must achieve in this plan, cost, cheaper
   alternative. Only what the plan needs; don't append the register's
   existing gaps unless the plan makes one worse.
7. **Find the human questions.** `special` data; personal data for a new
   purpose (lawful basis); a new third party, or a transfer outside the
   EU/EEA; a change to a `confirmed` entry's class, purpose, retention,
   owner or grants; a separation rule that can only be met by a staffing
   or process decision.
8. **Draft entry skeletons** for each new item, flow, purpose and
   processor, in the format's shape, `Status: draft`, `Applied: none yet`,
   and the IDs the leader's handoff should carry for `@data` tags.
9. **Issue the verdict.**
   - `CLEAR`: existing entries already cover what the plan touches, and
     the plan meets their requirements. Give the IDs to carry forward.
   - `MEASURES-PROPOSED`: the plan should include the listed measures or
     separations. The leader builds them in, or tells the user which it is
     leaving out and why.
   - `NEEDS-HUMAN-DECISION`: at least one question from step 7. The leader
     puts the questions to the user before building the part they affect;
     the rest of the plan may proceed.

   When both measures and questions apply, the verdict is
   `NEEDS-HUMAN-DECISION` and the report lists both.

## Peek

For a small change (one field, one call, one log line), collapse the pass:
read the entries for the items touched, run one search for the new names,
ask the minimization question, and give a one-paragraph verdict with any
measure or question it raises. Escalate to a full pass if the peek finds
`restricted` or `special` data, a third party, or a new purpose.

## Report

The agent's report format, mode `preflight` or `preflight-peek`: verdict,
data touched, proposed measures, separation rules checked, the skeletons,
the pending human decisions, and `Entries written: none`.
