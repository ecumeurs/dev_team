---
name: intent-cold-start
description: Use when documentalist, bootstrapping the ATD-less intent register, is pointed at an existing codebase with no declared intent (no `intent/` register, no `.atd`) and needs to extract an initial honest draft of the intent register from the implementation (trigger A, cold-start onboarding).
---

# Intent Cold-Start Extraction

Code is the source of truth; your job is to produce an honest first draft of
the register, not a complete one. Everything you write is `draft`: it
describes what the code does today, which is not the same as what anyone
has agreed it should do.

1. **Check the markers.** If `.atd` exists, this is an ATD repo: stop and
   use skill `atd-cold-start` instead. If `intent/README.md` exists, this isn't a cold
   start — extend the existing register (steps 3–8 on the uncovered areas)
   rather than recreating it.
2. **Bootstrap.** Create `intent/README.md`, `intent/business.md` and
   `intent/architecture.md` from the layout in the format reference
   (`~/.local/share/dev_team/references/intent-register.md`), then add the
   `## Declared intent` section to the project instructions (see the core
   agent instructions).
3. **Find where behavior enters.** List the product's entry points before
   reading deeply: routes and handlers, CLI commands, public API modules,
   jobs and consumers, UI routes. Read the project's own README and docs for
   stated purpose. Rank the areas by how much business behavior they carry
   and work the densest first — that's where the highest-value entries live.
   On a large codebase, stop after the first few areas and report the rest
   as uncovered rather than skimming everything.
4. **Read each area whole before drafting.** A file or module can't be
   split into entries correctly from a fragment.
5. **Draft business entries from state-changing rules, not from files.**
   One rule per entry: what the product lets whom do, under which
   conditions, and what it refuses. An "and"/"also" joining two behaviors is
   two entries. Write down the proposed list (ID, one-line intent, source
   location) in your working notes first and check it for overlap (two
   entries claiming one rule — merge them) and gaps (a rule with no entry —
   add it or list it as uncovered) before writing any entry.
6. **Draft architecture entries for the structure that carries them** — the
   modules, services, entities, APIs and flows a newcomer would need to know
   are deliberate — each with `Serves:` naming the business entries it
   carries. Skip incidental structure; an entry per file is noise.
7. **Write the entries.** `Status: draft`, `Source: cold start from code`,
   every field stating the behavior in full. Describe what the code does,
   including behavior that looks like a bug — don't record your guess at
   the intended behavior. List those suspected bugs separately in your
   report, with file:line.
8. **Tag the code.** For each entry, put one `@intent <id>` comment line
   directly above its primary implementing symbol, and on the main test
   that covers it, if there is one. Comment lines only; change nothing else.
   Skip this step if the invoker asked for a register-only pass.
9. **Draft Vision; propose Contract.** Draft Vision (purpose, in scope, out
   of scope) from the project's README and what the code evidently does.
   Leave Contract empty: guarantees need human confirmation, and nothing is
   `confirmed` yet. List candidate guarantees (security, data-integrity,
   compatibility invariants the code visibly enforces) in your report as
   proposals.
10. **Run the consistency checks** from the format reference.
11. **Report** what was extracted, at what confidence, which areas remain
    uncovered, the suspected bugs, the Contract proposals, and that
    everything awaits confirmation (see Output format in the core agent
    instructions).
