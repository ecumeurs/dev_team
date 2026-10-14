---
name: data-gating-protocol
description: Use when coding-leader or coordination-leader is operating in a repo with a data register — a `## Data register` section in the project instructions, or `data-register/README.md` at the project root — to know when a task counts as touching data, when to call data-steward for a data preflight or post-task sync, and how to act on its verdict. Shared by both leaders; independent of whether the repo also declares intent.
---

# Data Gating Protocol (for leaders)

This is the leader's side of the protocol. `data-steward` runs the checks
with its own skills. Your job is knowing whether the repo has a register,
whether a task touches data, when to call `data-steward`, and what its
verdict obliges you to do. You never write to the register yourself.

## Does this repo have a register?

The project instructions normally say so in a `## Data register` section.
Without one, check for `data-register/README.md` at the project root. With
neither, skip this protocol. Don't create a register on your own
initiative; on non-trivial work that adds personal or sensitive data, say
in your final report that the repo has no data register and that
`data-steward` can cold-start one.

The data register and declared intent (`intent-gating-protocol`) are
separate gates with separate markers. A repo can have either, both, or
neither; when it has both, run both.

## Does the task touch data?

It does when the plan would do any of these:

- add, remove, or change an entity, a field, a table, or a migration;
- store data somewhere new: a file or object store, a cache, a queue, a
  search index, an export file;
- put user data in logs, traces, error reports or analytics events;
- send data to a third party, or start using a new SDK that receives it;
- use existing personal data for something it wasn't used for before;
- add or change a principal or credential with access to data: a service,
  a database role, a job, a CI permission, an admin path;
- change end-user permissions on sensitive data (that also goes through
  `spec-writer`'s access model).

A pure refactor that moves code without changing what is stored, sent or
who can reach it does not touch data. When unsure, call for a peek: it's
cheap.

## When to call data-steward

1. **Once the plan is formed, before you finalize it or write a handoff**
   (data preflight). Give it the plan in plain language and the files in
   scope if you know them. On a small change (one field, one call, one
   log line), ask for a peek. In a repo that also declares intent, run
   documentalist's preflight first: what the change is for comes before
   how its data is handled.
2. **After the work closes, before you report to the user** (post-task
   sync). Give it the base commit or changed files, the IDs and skeletons
   its preflight returned, which proposed measures were built and which
   were not, and anything the user decided along the way.

## Under a build plan: once per version

When the work is a chunk or a wave of a build plan
(`specs/versions/<v>/build-plan*.md`), the gate runs once for the whole
version, per "Data register" in
`~/.local/share/dev_team/references/build-plan-model.md`:

- `spec-writer` calls the data preflight on the draft plan and writes its
  result into the plan: `@data` IDs and adopted measures on each chunk's
  **Data** line, human decisions and declined measures in the gates table.
- The wave driver calls one post-task sync over the release's diff at the
  release gate.
- A chunk owner calls neither. It builds the chunk's **Data** line and
  places its `@data` tags. When a chunk turns out to add data that line
  doesn't cover, or an inserted chunk adds data, the driver gets a peek
  before that part is built.

## Acting on the verdict

- **CLEAR**: carry the entry IDs it gives into the work and the handoff,
  so `@data` tags are placed while the code is written.
- **MEASURES-PROPOSED**: build the proposed measures into the plan and the
  handoff, with the IDs. If you leave a measure out (too costly for this
  task, out of scope, disagreement), tell the user which and why in your
  report; never drop one silently. A measure you adopt that is an
  architectural decision also goes to documentalist for architecture
  capture, in a repo that declares intent.
- **NEEDS-HUMAN-DECISION**: put its questions to the user before building
  the part they affect. The rest of the plan can proceed. Relay the
  answers to `data-steward` in the post-task sync handoff, not as your own
  edits to the register.

## What goes in a handoff

When you delegate implementation in a repo with a register, the handoff
carries:

- the `@data` IDs for the items and flows the unit defines or moves, and
  the tag rule: one comment line directly above the model, migration, or
  call that defines or moves the data;
- the measures adopted from the preflight, each with what it must achieve;
- the constraint that no real data or secret value goes into code,
  fixtures, tests or logs.

## Close-out

Before reporting to the user, the post-task sync has run. Your report
mentions the gaps it opened or closed, any drift it flagged, and any
measures you left out, so the user sees the data-handling outcome alongside
the code.
