---
name: build-plan-authoring
description: Use when spec-writer turns a version's settled master spec (and its design set) into a build plan of chunks grouped into waves, or revises an existing build plan — after an owner ruling, a preflight's plan corrections, a chunk inserted, split, moved or dropped, or a blocked chunk leaving its wave. Covers sizing chunks, forming waves without degenerate one-chunk waves, the gates table, the data preflight once per version, and keeping the plan a current-state document rather than a change log.
---

# Build plan authoring (for spec-writer)

The model is `~/.local/share/dev_team/references/build-plan-model.md`; read
it before writing or revising a plan. It defines the terms, the chunk
template, the wave-forming method, the verification levels, the branch
scheme and the gating rules. A plan states only its deltas from it. Never
copy the model's workflow into a plan.

A build plan adds no behaviour. What the product does is in the master
spec, what it looks like is in the design set; where the plan disagrees
with either, they win and the plan is corrected.

## When to write one

When the owner has approved a version's master spec and asks for the build
to be planned. The design set it builds from should be settled too; a
screen still being designed becomes a design gate, not a guess.

Home: `specs/versions/<version>/build-plan.md`; a version shipped as
several releases has one plan per release, `build-plan-<release>.md`. The
wave log (`wave-log.md`, or `wave-log-<release>.md` beside a per-release
plan) sits next to it and belongs to the wave driver.

## Writing it

1. **Ground the code facts.** Have `codebase-explorer` (or an earlier
   grounding document) give you the files and seams each part of the spec
   touches. A chunk's **Files** line is a claim about real code; verify it.
2. **Cut chunks.** One feature slice per chunk, ending in one commit that
   leaves the app working. Size: a chunk owner should be able to hold it in
   one session. When a chunk's brief would pass about five source files,
   give it a split rule (halves `a`, `b`) rather than cutting it smaller
   by layer: layer-by-layer cutting creates chains, and chains create thin
   waves.
3. **Fill the template** for every chunk. **Atoms** from what you know of
   the intent record (documentalist's wave preflight refines it).
   **Architecture capture** for every new or changed API, entity, module or
   flow the chunk decides. **Revisions** for intent the chunk will change.
   **Verification** says "chunk checks", plus only the checks that are
   this chunk's point.
4. **List the gates.** Every non-code step a chunk waits on: owner
   approvals and rulings, design gates for `ux-writer`, contract wording,
   measurements and hand checks. Who clears each, what it blocks.
5. **Form the waves** with the model's method: earliest layers, fill short
   layers with chunks that have slack, merge small neighbours, allow an
   in-wave dependency only when a capture fixes the interface and the
   chain is two chunks at most. Count the chunks per wave at the end; a
   wave under three chunks needs its reason written in the waves table.
   The release gate is not a wave.
6. **Write the deltas.** The project's commands for each verification
   level; chunk-level checks this project keeps (a replay-corpus guard for
   generator chunks, say); when the sweep runs; branch and worktree names;
   κ if the owner set one.
7. **Data preflight, once for the version.** In a repo with a data register
   (`data-register/README.md`), hand the draft plan, and the access model
   if it changed, to `data-steward` for a data preflight. Put its `@data`
   IDs and adopted measures into each chunk's **Data** line, a measure it
   proposes and the owner declines into the gates table as declined, and
   each human decision it raises into the gates table as a gate.
8. **Review and approve.** Ask `ux-writer` to check the chunks that build
   interface against the design set when the plan is large. Put the plan to
   the owner; it is approved only when the owner says so (record it in
   `decisions.md`).

## Revising it

The plan is a current-state document. A revision changes the lines it
concerns and nothing else. During a build, make it in the wave worktree the
driver names and commit it on the wave branch there, so the next chunk
reads it; never in the main checkout.

- **A ruling.** Record it in `decisions.md` first; then change the affected
  chunks, gates and waves. The header's status line says, in one line,
  which revision this is and which decisions it writes in. Don't copy the
  ruling's text into the plan.
- **Preflight corrections.** Apply them before the wave's first chunk
  starts. A correction the owner must rule on becomes a gate.
- **Moved chunk** (blocked at the end of its wave): move it with every
  chunk of its wave that depends on it to the next wave, and recheck that
  wave against the in-wave edge rule.
- **Inserted chunk.** A decision, the next free integer ID, the template,
  its wave by the edge rule. Tell the driver it needs a peek before it
  starts.
- **Split chunk.** Halves `<id>a` and `<id>b` in the same wave, in order.
- **Dropped chunk.** Status `dropped`, with the decision; never delete the
  section while anything refers to it.
- **Re-forming waves.** When revisions leave a future wave thin, re-run the
  forming method on the waves not yet started. Never move a chunk of a
  wave whose preflight has already run, except by the moved-chunk rule.

The execution state (chunk **Status** and **Record** lines, the waves
table's Status column, a cleared gate's status) is the driver's; leave it
as it is.

## Plans written before this model

Don't restructure an existing plan on your own initiative; that's a
migration, done when the owner asks for it. Until then, apply this skill's
revision rules to it as far as its shape allows, and use the model for
anything the plan leaves unsaid.
