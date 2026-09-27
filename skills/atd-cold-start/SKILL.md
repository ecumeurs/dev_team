---
name: atd-cold-start
description: Use when documentalist is pointed at a codebase with little or no ATD coverage and needs to extract an initial honest draft of docs/*.atom.md from the existing implementation (ATD trigger A, cold-start onboarding).
---

# ATD Cold-Start Extraction

Code is the source of truth; your job is to produce an honest first draft of
`docs/`, not a complete one.

1. **Bootstrap if needed.** Check for `.atd` at the project root. If absent:
   `atd init` (or `atd init --docs <path>` / `atd init --model <name>` for
   non-default layout). `atd init` also installs the ATD pre-commit hook and
   the `req_tech_debt_backlog` escape-hatch atom — don't fight either; they
   exist so day-to-day work isn't blocked by imperfect ancestry. Then add
   the `## Declared intent` section to the project instructions (see the core
   agent instructions).
2. **Prioritize.** `atd roadmap --dir <src> --out roadmap.json` ranks files by
   complexity/density. Work the densest files first — that's where the
   highest-value atoms live.
3. **Index (best-effort).** `atd index` builds the semantic vector DB. This
   needs a configured embedding provider (Ollama by default); if it's not
   available, skip it and rely on `atd query` / grep instead — don't block
   cold-start on infrastructure that isn't your job to stand up.
4. **Dissect manually.** For each prioritized file, run the Manual
   Dissection Protocol in the ATD manual
   (`~/.local/share/dev_team/references/atd-atoms.md`) to get proposed atom
   boundaries (id, type, line range) — `atd dissect` no longer exists.
5. **Materialize DRAFT atoms.** For each proposed boundary, create the atom
   via `atd update --file docs/<id>.atom.md --set id=<id> --set type=<TYPE>
   --set layer=<LAYER> --set status=DRAFT --set priority=<n> --intent "..."
   --logic "..." --interface "..." --expectation "..."`. Check the type's
   bloat tolerance first with `atd config bloating-factor <TYPE>` — types
   like `RULE`/`MECHANIC` (factor ≥0.7) must stay single-rule; `MODULE`/
   `REQUIREMENT`/`SPECIFICATION` (0.3) and `USER_STORY`/`API`/`USECASE` (0.1)
   tolerate broader narrative. Confirm the id from the command's own output
   before moving on (see the ATD manual's CLI quick reference)
   — don't just assume your proposed id landed.
6. **Weave.** `atd weave` after any batch of new atoms, to populate
   `dependents[]` from `parents:` declarations.
7. **Link code to atoms.** `atd map --file <path>` (no `--atom`) proposes
   candidate atoms for a file; `atd map --file <path> --atom <id>` confirms
   one specific match with a rationale before you commit to it; only once
   confirmed, inject the tag with `atd update --spec-link <id> <file>`.
   Follow surgical placement: tag goes directly above the specific
   function/class/route handler being implemented, never at file/package
   level unless the atom genuinely governs the entire file.
8. **Verify the extraction, don't just dump it.** Run, in order:
   `atd weave`, `atd audit` (bloat + collision detection across the new
   atoms), `atd congruence --target <atom_id>` for any atom whose parents/
   dependents/tag-siblings look suspicious, `atd lint` (structural
   validation — required fields, enum values, broken `[[id]]` references),
   `atd crawl --gaps` (orphan STABLE atoms — shouldn't exist yet since
   everything starts DRAFT, but check anyway), `atd check --full` (impl/test
   link coverage).
9. **Leave atoms at DRAFT (or REVIEW at most).** Cold-start extraction never
   self-promotes to STABLE. Extracted atoms describe what the code currently
   does, not what's been reviewed and approved as the durable spec — that
   promotion is a human call.
10. **Report** what was extracted, at what confidence, and what's still
    uncovered (see Output format in the core agent instructions).
