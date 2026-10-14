---
name: data-review
description: Use when data-steward, in a repo with a data register (`data-register/README.md`), is asked for the state of the register — every open gap, drift and pending human decision ranked by risk with proposed measures — or for a record of processing activities (RoPA) export for an auditor or regulator (trigger E, review on request).
---

# Data Register Review and RoPA Export

Two requests on demand: a ranked review of what's open, or an export of
the Article 30 record. Neither changes what the register says, apart from
the stale entries the review finds and reports.

Read `~/.local/share/dev_team/references/data-register.md` and
`~/.local/share/dev_team/references/data-security-baseline.md`.

## Review

1. **Check first.** Run the format's consistency checks; failures go at
   the top of the report.
2. **Collect what's open.** `grep -rn -E '^(Gap|Drift):' data-register/`,
   the *Pending human decisions* list, every `unknown` in `Applied` and in
   grants tables, every separation rule with `Holds: no` or `unknown`.
3. **Spot-check freshness.** Sample the `restricted` and `personal` items
   and the third-party flows: does the code at `Location`, and the tagged
   code (`git grep -n '@data <id>'`), still match the entry? A mismatch is
   drift: record it as the post-task sync would.
4. **Rank by risk.** Order the open items by:
   - class and flags (`special` and `restricted` first);
   - exposure path (crosses to a third party or the public zone, reaches
     backups or non-production environments, sits in logs);
   - how many people's data is involved;
   - how long it has been open (`git log -S'Gap:' -- data-register/`).

   Accepted gaps go last, listed so the accepted risk stays visible.
5. **Propose for the top of the list.** For each high-ranked gap or broken
   separation, the measure argued in the baseline's terms: risk, measure,
   cost, cheaper alternative. Group items one measure would close
   together.
6. **Report** with mode `review`: check results, the ranked list, the
   proposals, pending decisions grouped by who should decide, and any
   drift found by the spot-check.

## RoPA export

The register keeps one record, `processing.md`; an export is generated on
request and never stored in the register.

1. **Check it's exportable.** Every purpose that would appear has a lawful
   basis and its fields filled. List the purposes still `undecided` and
   ask whether to export them marked as such or leave them out; an export
   with silent holes is worse than one with marked ones.
2. **Build the table.** One row per purpose that isn't `retired`, in the
   column order of the template the caller names (CNIL, ICO) or, if none,
   the Article 30(1) order:
   - controller, DPO and representative, from the README, in a header;
   - purpose and lawful basis;
   - categories of data subjects;
   - categories of personal data, read from each `Data` item's `Fields`
     and flags, described in categories (contact details, payment data),
     never field names;
   - categories of recipients, with processors by legal name;
   - transfers outside the EU/EEA and their safeguards;
   - retention, per purpose;
   - a general description of the security measures, from `Security`.
3. **Deliver it** in the format asked for (Markdown table, CSV), outside
   `data-register/`, and report with mode `ropa-export`: rows exported,
   purposes left out or marked, and the date of the register state it
   reflects (`git log -1 --format=%cs -- data-register/`).
