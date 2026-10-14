---
name: data-cold-start
description: Use when data-steward is asked to bootstrap a data register (`data-register/`) for an existing codebase that has none, to draft an honest first inventory, flows, purposes, processors and responsibilities from the code, and tag the definitions and flow points with `@data` (trigger A, cold start).
---

# Data Register Cold Start

Draft a register for a codebase that has none. Code is the source of truth
for what data exists and where it goes. It says nothing about purposes,
lawful bases, owners or retention periods: those start `undecided` or
`unassigned`. The goal is an honest first draft, not a complete one.

Read both references in full before writing anything:
`~/.local/share/dev_team/references/data-register.md` (every file's
format) and `~/.local/share/dev_team/references/data-security-baseline.md`
(classes, measures, flow questions, separation patterns).

Only start when asked. If `data-register/README.md` already exists, this
is not a cold start: report that and stop, or run `data-review` if that's
what the caller wants.

1. **Create the skeleton.** `data-register/README.md` following the
   format's template: controller, DPO and representative `unassigned`
   unless the caller told you, a *Scope* naming the repository and the
   environments you can see, the file list, an empty *Pending human
   decisions*, and *External records* all `none yet`.
2. **Adapt the classification.** Write `classification.md` from the
   baseline's default scale, every class and flag `draft`, with `Examples`
   drawn from this project's kinds of data (never values). Drop a class
   the project plainly has no data for only if the caller agrees; keeping
   an empty class is cheaper than re-adding one.
3. **Find the data.** Search every place data can live or pass, and keep a
   list as you go:
   - schema files, migrations, ORM models, seed and fixture definitions;
   - request and response types, form handlers, API clients;
   - file and object storage, uploads, generated documents;
   - caches, queues, search indexes, analytics events, error reporting;
   - logging of request or response bodies, traces;
   - third-party SDKs and HTTP clients (each one is a probable processor);
   - backup and export jobs;
   - secret names in config and `.env.example`, by key name only:
     `grep -o '^[A-Z_][A-Z0-9_]*=' <file>`. Never open a real `.env`, key
     file or credentials file to read values.
4. **Write `inventory.md`** at entity level. Split a field out only where
   its sensitivity, origin, retention or recipients differ from the
   entity's. Every field the format lists is present: `Owner: unassigned`,
   `Retention: undecided`, `Applied:` from evidence only (a config key, a
   `path:Symbol`, a platform default you can point at), `unknown` for
   anything unverified. Record derived copies (index, cache, log, analytics)
   as their own `store` or `log` items. Open a `Gap:` line wherever
   `Applied` provably falls short of `Required`; don't open one on an
   `unknown`.
5. **Write `flows.md`.** The components table and zones first, then one
   entry per flow, starting with every flow that crosses into a third party
   or out of the backend. Ask the baseline's flow questions of each
   crossing flow; a "no" becomes a `Gap:`. Draw the diagram last, from the
   entries.
6. **Draft `processing.md`.** One purpose per thing the code evidently does
   with personal data, named by purpose, never by tool. `Lawful basis:
   undecided`, with the likely basis in parentheses if it's obvious.
   `DPIA:` per the baseline's rule for `special` data; otherwise `not
   needed` only with a reason you can state, else `undecided`.
7. **Write `processors.md`** for each third party found, with `Contract:
   unknown` and `Safeguard: undecided` unless you were told.
8. **Write `responsibilities.md`.** Principals from service credentials,
   database roles, deploy and CI config. Grants tables for each class that
   holds data, cells `unknown` where code and config don't settle them.
   Propose the separation-of-duties rules from the baseline that apply to
   this project's principals, `Holds:` from evidence or `unknown`. Leave
   the *Access model cross-check* section stating that no check has run.
9. **Fill *Pending human decisions*.** One line per `special` item, per
   purpose without a lawful basis, per grants table with `unknown` cells,
   and for the controller and DPO. Owners and retention can be one line
   per entity group rather than per item.
10. **Tag.** Place `@data <id>` on the definitions and flow points of the
    items and flows you recorded, comment lines only, following the
    format's tag rules. On a large codebase, tag the `restricted` and
    `personal` items and the third-party flows first, and report the rest
    as untagged.
11. **Check and report.** Run the format's consistency checks on the whole
    register. Write the project instructions note. Report what you
    inventoried, which areas you didn't reach, the highest-risk gaps found,
    and the pending decisions, using the agent's report format with
    `cold-start` as the mode.
