---
name: data-post-task-sync
description: Use when data-steward, in a repo with a data register (`data-register/README.md`), is called after coding-leader (or any other agent) closes a task that touched data, to record the new or changed items, flows, purposes and processors, update required vs applied protection, complete missing `@data` tags, and report gaps and drift (trigger C, post-task sync).
---

# Data Post-Task Sync

Bring the register up to date with what a just-closed task actually built.
Record what's new, update what's applied, complete tags, and report drift
without resolving it.

Read the format sections for every entry kind you will write
(`~/.local/share/dev_team/references/data-register.md`) and the baseline's
class requirements (`~/.local/share/dev_team/references/data-security-baseline.md`).

1. **Scope the change.** Use the base commit or file list from the
   handoff, or `git diff --name-only <base>`. Read the diff itself, not
   just names. Look in particular at:
   - migrations, schema and model files;
   - new external calls and SDK usage;
   - new log, trace, error-report or analytics fields;
   - new caches, queues, indexes, exports;
   - credential and config changes (by key name only);
   - `@data` tags added or removed: `git diff <base> | grep '@data'`.
2. **Collect the entries involved.** Tags in the changed code (including
   removed lines), the IDs and skeletons the preflight handed the leader,
   and entries the diff plainly touches but nothing names: search the
   register for the diff's table, field, client and job names.
3. **Classify each item, flow and tag:**
   - **New, matching a preflight skeleton**: write the entry from the
     skeleton, corrected to what was actually built, `Status: draft`.
   - **New, no skeleton**: data appeared that preflight never saw. Write
     it as `draft` all the same (the register records what exists), and
     flag it in the report: it may have skipped decisions preflight would
     have raised.
   - **Changed**: update `Location`, `Fields`, `Data`, `Recipients` and
     the like to what the code now does. A change to a `confirmed` entry's
     `Class`, `Purposes`, `Retention`, `Owner` or grants is not yours to
     apply: record it as drift.
   - **Missing tag**: code defines or moves a recorded item or flow and
     carries no `@data` tag. Add one comment line above the symbol, in the
     file's comment syntax, and change nothing else.
   - **Dangling tag**: names an unknown or retired ID. Report it with file
     and line; don't retarget it.
   - **Drift**: the entry and the code disagree about a fact (a recipient,
     a field, a retention, a copy). Add one `Drift:` line naming both
     sides and the task, and stop on that entry. Don't edit its meaning or
     the code.
   - **Removed**: data, a flow or a processor the code no longer has. Set
     it `retired` with a `Retired:` line. Report any tag still pointing at
     it.
4. **Update protection.** For every entry touched, recompute `Required`
   from its class and flags, then `Applied` from the code with evidence.
   Remove a `Gap:` line the task closed (with the evidence in the report);
   open one where the task left a requirement unmet. Keep an `Accepted by
   the user` gap as it is unless the risk changed.
5. **Check responsibilities.** For new principals, credentials or grants,
   update the principals and grants tables, and re-check each
   separation-of-duties rule's `Holds:`.
6. **Update *Pending human decisions*** with anything newly `undecided` or
   `unassigned`, and remove lines the handoff says the user settled
   (applying the settled value to the entry).
7. **Check and report.** Run the format's consistency checks on the whole
   register, since a retired ID can dangle anywhere. Report with mode
   `post-task`: entries written and their status changes, tags added, gaps
   opened and closed, drift flagged, data that bypassed preflight, and the
   pending decisions.
