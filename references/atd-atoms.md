# ATD — atoms, rules and tooling

`documentalist` keeps declared intent with ATD (Atomic Traceable
Documentation) in a repo with a `.atd` config at the project root. This file
is the ATD half of its manual: what an atom is, how to cut one, the rules the
`atd` tooling enforces, and the commands. The backend-neutral rules
(temperament, triggers, drift handling, report format) stay in the agent.
The ATD-less backend has its own manual, `intent-register.md`.

The ground truth is the real ATD project: the `atd` CLI built from
`scripts/cmd/atd/`, and its reference manual `ATD.md`. If `atd --help` or a
subcommand's `--help` disagrees with a flag named here, the CLI's own
`--help` output is authoritative. Check it before guessing.

## MCP first, CLI fallback

Every atom operation goes through the real `atd` tooling. Prefer the `atd`
MCP server's tools when it's connected, and fall back to the `atd` CLI via
bash when it isn't; don't block or stall waiting on MCP. The operations and
their semantics are the same either way, so everything below applies to
both.

## ATD principles

These add to the agent's backend-neutral principles.

- **Bidirectional traceability.** `parents:`/`dependents:` link atom to
  atom; `@spec-link [[id]]` links code to atom; `@test-link [[id]]` links
  tests to atom. The chain runs Business → Architecture → Implementation →
  Test, both ways.
- **Token economy.** Prefer deterministic subcommands (`lint`, `weave`,
  `crawl`, `query`, `stats`) over LLM-backed ones (`audit`, `map`, `search`,
  `congruence`, `fix`) when a deterministic one answers the question.
  `atd dissect` has been removed from `atd` entirely; boundary
  identification is done by hand (see Manual Dissection Protocol, below).
- **LLM-assisted, human-governed.** Bulk extraction and audit are fine to
  run through `atd`'s own LLM plumbing. Final architecture calls (splitting
  an atom, changing a STABLE atom's intent, resolving real drift) are for a
  human or a leader.

## Atom anatomy

YAML frontmatter (`id`, `human_name`, `type`, `layer`, `version`, `status`,
`priority`, `tags`, `parents`, `dependents`) plus four mandatory H2 sections
(`## INTENT`, `## THE RULE / LOGIC`, `## TECHNICAL INTERFACE`,
`## EXPECTATION`). Three layers:

- BUSINESS (requirement/user_story/rule/domain): low volatility, heavy human
  gate.
- ARCHITECTURE (module/service/entity/api/ui/specification): moderate
  volatility.
- IMPLEMENTATION (mechanic): high volatility, evolves freely with code.

Status moves `DRAFT → REVIEW → STABLE`, and can demote back down if a spec
changes.

**Naming convention (`id` field).** Per ATD.md, `id` is a `snake_case` slug
of the form `<type_lowercase>_<descriptive_slug>`: a `RULE` atom about rate
limiting is `rule_rate_limiting`, a `USER_STORY` about checkout is
`user_story_guest_checkout`. Lowercase, underscores, no
spaces/hyphens/camelCase. The type prefix always matches the atom's actual
`type` field, and the slug is short and descriptive, not a restatement of
the whole intent. Apply this whenever you draft a proposed id (Manual
Dissection Protocol step 4, and every `atd update --set id=<id>` creation in
`atd-cold-start`, `atd-spec-ingestion` and `atd-architecture-capture`).
Never invent an id in another shape: no numeric-only ids, no id copied from
a spec section heading verbatim.

## Manual Dissection Protocol

`atd dissect` has been removed, so boundary identification is always
manual. Even when it existed, its extraction prompt was generic and produced
boundaries that didn't map onto ATD's own model. Do boundary identification
yourself, directly against the source (code file or spec document):

1. **Read the whole unit first, don't scan line-by-line.** A file or spec
   section can't be atomized correctly from a fragment. Read it end to end
   once before proposing any boundary.
2. **Find sentence-level state-changing rules, not paragraphs.** The unit of
   atomization is one rule or responsibility. An "and"/"also" joining two
   distinct behaviors inside one candidate atom is a split signal: draft two
   atoms, not one with a compound INTENT.
3. **Assign type before drafting content**, using the type's family and
   typical layer as a first filter (Governance/Requirements/Logic →
   BUSINESS; Architectural/Interface → ARCHITECTURE;
   Logic-as-implementation → IMPLEMENTATION). Then confirm against the
   type's bloat factor (`atd config bloating-factor <TYPE>`): high-factor
   types (RULE, MECHANIC, ENTITY, UI ≈0.8) get one rule per atom; low-factor
   types (USER_STORY, API, USECASE ≈0.1) tolerate broader narrative. Let the
   bloat tolerance decide how aggressively to split, not a line-count
   heuristic.
4. **Draft boundaries as (proposed id, type, layer, source line-range or
   section anchor) before writing full atom content.** Propose each id per
   the naming convention at this stage. Write this list in your own working
   notes, not as atoms yet, so you can check total coverage and overlap
   before materializing anything.
5. **Check the boundary list for overlap and gaps** before creating a
   single atom. Two boundaries claiming the same rule is a collision to fix
   by merging or re-scoping now, not after `atd audit` flags it. A rule
   with no boundary is a gap to add or consciously note as deferred.
6. **Only then materialize** each boundary into a real atom via
   `atd update`, per the skill you're running.

The "Dissect" steps in `atd-cold-start` and `atd-spec-ingestion` mean this
procedure.

## ATD hard rules

These add to the agent's hard boundaries.

- **Never hand-write or bulk-rewrite a `.atom.md` file.** Always go through
  `atd update` (single-field edits), so IDs, renames and `[[id]]` reference
  propagation stay consistent. Use the Edit tool only for files `atd` has no
  subcommand for (free-form notes in `docs/` that aren't atoms).
- **Links are placed with `atd update --spec-link`**, never by hand-editing
  the source file.
- **Never bypass `atd update`'s STABLE+BUSINESS guard with `--force`**
  without explicit confirmation. If the CLI refuses the edit, the guard is
  working: report it, don't work around it.
- **Never list `contract_atd`/`vision_atd` (or a project's equivalent) in
  any atom's `parents:`.** CONTRACT and VISION are read for governance, not
  linked as ancestry (ATD.md §1.4). An atom that already does this is a
  lint-worthy finding to report.
- **Confirm a created atom's id from `atd update`'s own output**, never from
  the `--set id=<id>` value you passed in. If the output doesn't echo an id,
  or echoes a different one, re-read `docs/<id>.atom.md` (or
  `atd query --field id --search <id>`) and use the confirmed id in every
  report and downstream reference.

## Drift evidence

A present but stale `@spec-link`/`@test-link` is drift. Get evidence with:

- `atd map --atom <atom_id> --file <code_path>` (MCP: `atd_recon`): confirm
  mode. Validates one code file against one atom and returns a confidence
  score plus rationale.
- `atd congruence --target <id>`: checks the atom's
  parents/dependents/tag-siblings for INTENT/LOGIC contradictions.

`atd audit --atom <path>` scopes audit's own bloat/collision sweep to one
atom file, but audit has no atom-vs-code compliance mode. Passing both
`--atom` and `--code` is a hard CLI/MCP error, so never reach for
`atd audit --code`.

`atd fix` auto-splits atoms flagged `[BLOATED]` by `atd audit`, rewriting
the original as a MODULE parent with child atoms. It is docs-only and
legitimate to run, but always with `--dry-run` first: it changes atom IDs
and everything that references them.

## Lifecycle

- **Bloat control is per type.** Check `atd config bloating-factor <TYPE>`
  before writing new atom content or deciding whether one needs splitting.
- **Status.** You may advance IMPLEMENTATION-layer atoms toward REVIEW
  yourself when the evidence (aligned `atd check`, passing `@test-link`
  coverage) supports it. Advancing to STABLE, or touching anything at
  BUSINESS layer, needs explicit sign-off.
- **VISION gate (scope).** Before creating or altering a BUSINESS-layer
  atom, read the project's unique `VISION` atom
  (`atd query --field type --search VISION`, then read the file). An atom
  outside VISION's in-scope/out-of-scope framing needs the user warned and
  VISION updated to match.
- **CONTRACT gate (surface).** Run the atom through the **Contract Surface
  Grid** (ATD.md §1.4): eligible only if `status: STABLE` and `layer` is
  `BUSINESS`/`ARCHITECTURE`; surface by default for
  `REQUIREMENT`/`USER_STORY`/`API`/`UI`/`SPECIFICATION`/`SERVICE`/
  BUSINESS-layer `RULE`; conditional (ask) for `MODULE`/`ENTITY`; never for
  IMPLEMENTATION-layer atoms, `DOMAIN`, or ARCHITECTURE-layer `RULE`. If the
  grid says surface, removing it or altering its guarantee needs the
  project's unique `CONTRACT` atom to take a MAJOR `version` bump in the
  same change (human-confirmed); newly promoting it to STABLE needs a MINOR
  bump.
- **No parent, no code.** Every atom except CONTRACT/VISION needs a parent
  that traces back to a BUSINESS-layer atom, never CONTRACT or VISION
  directly.

## CLI quick reference

When the `atd` MCP server is connected, prefer its tools: same operations,
one tool call per row.

| Need | Command |
|---|---|
| Bootstrap project | `atd init` / `atd init --docs <path> --model <name>` / `atd init --upgrade` |
| Prioritize files by complexity | `atd roadmap --dir <src> --out roadmap.json` |
| Build semantic index | `atd index` |
| Propose atom boundaries | **Manual Dissection Protocol** (above); `atd dissect` no longer exists |
| Rebuild parent/dependent graph | `atd weave` |
| Find/confirm/propose atom-code matches | `atd map --file <path> [--atom <id>] [--new]` |
| Search atoms by field | `atd query --field <field> --search <value> [--paths-only]` |
| Semantic/keyword search | `atd search --query "<text>" \| --grep "<text>" [--scope code\|docs\|all]` |
| Create/edit an atom (never hand-write) | `atd update --file <path> --set k=v ... --intent "…" --logic "…" --interface "…" --expectation "…" [--force]`. **Multi-value `--set` (e.g. `parents` with 2+ entries) needs an extra outer-quote layer**: `--set` is parsed as CSV, so an unquoted comma splits one value into two flag args and drops the second. Use `--set '"parents=[[a]],[[b]]"'`, not `--set "parents=[[a]],[[b]]"`. |
| Inject a `@spec-link` tag into code | `atd update --spec-link <atom_id> <source_file>` |
| Batch-update matching atoms | `atd update --filter 'type=RULE,status=DRAFT' --set status=REVIEW` |
| Bloat + collision audit (optionally one atom; `--concurrency` bounds parallel LLM calls, default 4) | `atd audit [--docs <dir>] [--workspace] [--threshold <0-1>] [--atom <atom_path>] [--concurrency <int>]` |
| Atom-vs-code compliance check (never `atd audit --code`) | `atd map --atom <atom_id> --file <code_path>` (MCP: `atd_recon`) |
| Consistency across parents/dependents/tag-siblings | `atd congruence --target <atom_id>` |
| Auto-split bloated atoms | `atd fix --audit <report.json> [--dry-run]` |
| Structural validation | `atd lint [dir]` |
| Dependency graph / orphan detection | `atd crawl [--gaps] [--src <dir>] [--workspace]` |
| Impl/test link coverage (diff-driven by default) | `atd check [--full] [--atom <id>] [--file <path>] [--semantic] [--out <path>]` |
| Health snapshot + blast radius for one atom | `atd trace <atom_id> [--summary] [--src <dir>] [--docs <dir>]` |
| Quantitative health metrics | `atd stats [--src <dir>] [--workspace]` |
| Check a type's bloat tolerance | `atd config bloating-factor <TYPE>` |
| View full config | `atd config list` |
