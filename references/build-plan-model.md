# Build plans — the model

A build plan turns a version's settled master spec and design set into
numbered **chunks**, grouped into **waves**, that the team builds one wave
at a time. This file is the one place the model is defined. A project's
plans state only how they differ from it (see "What a plan holds"), never
restate it.

Three parties read it: `spec-writer`, who writes and maintains the plan
(skill `build-plan-authoring`); the **wave driver**, normally the user's
top-level session, which runs it (skill `wave-execution`); and
`coding-leader`, which builds one chunk at a time in chunk mode.

## Why waves

The checks that cost the most run once per wave, not once per chunk: the
intent preflight, the architecture captures, the full test and performance
pass, and the post-task sync. A chunk checks only its own change. The owner
accepts that the chunks of one wave may drift a little apart until the wave
gate catches it. A wave is a **gate batch**. It is not a parallel-dispatch
set, although its chunks may run in parallel (see "Concurrency").

`unit-decomposition`'s batches are a different thing: the units inside one
chunk or one task, dispatched by a leader. A chunk leader never arranges a
chunk into waves.

## Terms

| Term | Meaning |
|---|---|
| **Chunk** | One feature-sized unit of the plan, built by one owner in its own branch, ending in one commit merged into the wave branch. |
| **Wave** | A set of chunks sharing one wave preflight at the start, one wave gate at the end, and one merge into `main`. |
| **Gate** (in the gates table) | A step that is not code and that some chunk waits on: an owner step (a ruling, an approval, a wording sign-off), a design gate (`ux-writer` deliverable), a spec gap (`spec-writer`), a measurement or hand check, a contract sign-off. Each has a status. |
| **Chunk checks** | The verification a chunk runs (see "Verification levels"). |
| **Wave gate** | The full verification at the end of a wave, then the post-task sync. |
| **Release gate** | The final check of the whole release against the master spec's definition of done. It runs after the last wave's gate. It is a step, not a wave. |
| **Wave driver** | Whoever runs the waves: the user's top-level session by default. |
| **Wave log** | The execution record next to the plan (`wave-log.md`, or `wave-log-<release>.md` beside a `build-plan-<release>.md`): what each preflight found, each gate's results and figures, what was moved and why, each report to the owner. |
| **κ (concurrency)** | How many chunks may be in flight at once. Default 1. |

## Roles

| Who | Does |
|---|---|
| `spec-writer` | Writes the plan from the master spec and the design set, forms the waves, revises the plan when a ruling, an insertion, a split or a move changes it, and records rulings in `decisions.md`. The plan's only writer, except for its execution state. |
| Wave driver | Runs each wave per skill `wave-execution`: branches, the wave preflight, chunk dispatch at κ, the wave gate, the sync, the report, the merge on the owner's word. Keeps the wave log and the plan's **execution state** current: each chunk's **Status** and **Record** lines, the waves table's Status column, a gate's status once it clears. Routes every other plan change to `spec-writer`. |
| `coding-leader` (chunk mode) | Builds one chunk: tests first, implement, chunk checks, documents, one commit, merge into the wave branch. Writes the code itself. |
| `documentalist` | One wave preflight per wave (a verdict per chunk), the architecture captures before any code, one post-task sync over the wave's diff. |
| `data-steward` | Once per version: a data preflight on the draft plan, a post-task sync at the release gate. See "Data register". |
| `ux-writer`, `spec-writer` | Clear the design gates and spec gaps that block chunks. |
| The owner | Rules on gates, approves the plan, asks for each wave's merge into `main`. |

## What a plan holds

A plan holds the **current state** only. History lives elsewhere: rulings in
`decisions.md`, execution in the wave log, earlier wordings in git.

1. **Header.** `Status: vN (date): <one line on what this version
   changed>`, approval state, the master spec and design versions it was
   written from. One line per revision, never a growing changelog; older
   lines go once they are older than the current wave.
2. **Read first.** Anything the plan undoes or changes in the previous
   version that a builder must know before starting.
3. **Gates table.** `Gate | What | Cleared by | Blocks | Status`. A cleared
   gate stays in the table with its status `done (date, spec Dn)` until the
   release closes, so a chunk's **Depends on** never dangles.
4. **Waves table.** `Wave | Chunks | Waits for | Status`, plus a dependency
   graph. A wave of fewer than three chunks says why in its row.
5. **Workflow deltas.** Only what this plan adds to or changes in this
   model: κ if not 1, the project's commands for each verification level,
   checks a chunk keeps at chunk level (a replay-corpus guard, say), when
   the sweep runs at the wave gate, the branch and worktree names.
6. **Measurements and hand checks**, each assigned to the chunk or gate
   that runs it.
7. **Chunks**, in the template below.
8. **Release gate.**

### The chunk template

```
### Chunk <id> — <title>

Status: planned | ready | in progress | built | merged (w<n>, <commit>) | blocked (on <gate or chunk>) | moved (to w<n>) | dropped
Wave: <n>
Depends on: <chunk ids, gate names>
Architecture capture: <what the wave preflight must record, or "none">

- Goal: one or two sentences.
- Scope: what is in, what is explicitly out.
- Files: the source and test files it creates or changes.
- Spec sections / Design docs: links.
- Atoms (or intent entries): the governing IDs known when the plan was written.
- Data: `@data` IDs and adopted measures, when the project has a data register.
- Revisions: intent changes the wave sync applies once this chunk is merged
  (pre-authorized by the plan's approval; anything else is drift).
- Done when: testable statements.
- Verification: "chunk checks", plus any check that is this chunk's point
  (a measurement, the area's own suite), and any check it places at the
  wave gate.
- Split rule: when the brief would pass about five source files, the
  halves (<id>a, <id>b) and what each covers.
```

After merge, the driver adds one `Record:` line: the commit, and any place
the code had to differ from the spec or the design (with where that was
reported).

### Chunk IDs

- Chunks are numbered with integers. A chunk inserted after approval takes
  the next free integer, never a letter.
- Letters are only split halves: `7a`, `7b`. A split half of a split half
  is not allowed; split the chunk into three instead.
- Numbers never imply order. Order inside a wave is topological, ties
  broken by number.
- Never renumber; issues, briefs and commits point at the IDs. An existing
  plan keeps the IDs it already has.

## Forming waves

`spec-writer` forms the waves when it writes the plan, and again whenever a
revision moves chunks. The method avoids waves that pay a full preflight and
gate for one chunk.

1. **Graph.** Nodes are chunks and gates; an edge means "needs to be done
   first". A gate expected to clear before its wave starts counts as done.
2. **Earliest layers.** Give each chunk its earliest wave: one more than the
   latest wave among its predecessors.
3. **Fill short layers.** For each layer under the minimum (default 3
   chunks), first push in chunks from earlier layers that have slack (no
   successor would be delayed by moving them later), then pull in chunks
   from the next layer whose only edges into this layer meet the in-wave
   edge rule (step 5).
4. **Merge small neighbours.** Merge two adjacent layers when the merged
   wave stays under the maximum (default 6 chunks, or fewer when the
   chunks are large: the wave preflight has to read every chunk's files)
   and every new in-wave edge is allowed (next rule).
5. **In-wave edges.** Chunks with no path between them must not change the
   same source file (shared lists such as a test-script list or a README
   table are fine; the chunk owner resolves those when it merges). A dependency between
   two chunks of the same wave is allowed only when the interface the second
   one needs is fixed by an architecture capture made in the wave preflight,
   and the chain is at most two chunks long. Then one preflight still holds
   for both.
6. **What's left.** A wave below the minimum stays only when nothing else can
   join it. Say why in the waves table ("the critical path is a chain whose
   interface can't be captured ahead"). The release gate is never a wave.

## Concurrency

κ is how many chunks may be in flight at once: started and not yet merged
into the wave branch. The default is 1, a cost choice that the owner can
change for a wave or a plan; nothing in the model depends on it being 1.

- At κ > 1, chunks with no path between them run side by side, each in its
  own worktree; a chain inside a wave still runs in order.
- A chunk that is built and waiting only on a merge gate (a contract
  sign-off) does not count against κ.

## Changing a wave once it starts

A wave's membership is frozen when its preflight runs. After that:

- **Blocked chunk.** A chunk still blocked when the rest of its wave is done
  leaves the wave with every chunk of that wave that depends on it, and
  joins the next wave, whose preflight covers it. The wave closes without
  them.
- **Inserted chunk.** Needs a decision in `decisions.md`, a new integer ID,
  a `documentalist` peek over its files before it starts (recorded in the
  wave log), and the in-wave edge rule above.
- **Split chunk.** Its halves stay in the same wave and run in order, each
  with its own commit.
- **Ruling mid-wave.** `spec-writer` writes it into the plan; the driver
  passes the changed lines to a running chunk owner only if they touch that
  chunk, and otherwise after it finishes.

Any of these is a plan revision: `spec-writer` makes it, and the header's
status line names it.

## Verification levels

The plan's workflow deltas name the project's commands for each level.

| Level | Runs | Never runs |
|---|---|---|
| **Chunk checks** | The chunk's **Done when**; the tests it adds or changes; the existing unit tests related to the files it touches; typecheck, lint, format; link lint when it changed Markdown; a debug run showing the behaviour; any check its **Verification** line names. | The full suite, the end-to-end, accessibility or notation suites as a whole, the sweep, bundle or timing measurements, unless its **Verification** line names one. |
| **Wave gate** | The full quality command; the sweep when a chunk places it there; every check chunks deferred to it; the bundle figure against the previous wave; performance figures, recorded with machine and date (a virtual machine's figure never gates); then the post-task sync. | — |
| **Release gate** | Every item of the definition of done on the merged code; the release notes. | — |

A failure at the wave gate is traced to the chunk that caused it and fixed
on the wave branch in its own commit. A fix that would change behaviour the
spec or the design states goes to `spec-writer` or `ux-writer` instead.

## Branches

- At a wave's start, a wave branch `<release>-w<n>` is cut from `main` in
  its own worktree.
- Each chunk runs in its own worktree on a branch cut from the wave branch,
  `<release>-c<id>-<slug>`, ends in one commit (two for a split chunk), and
  merges `--no-ff` into the wave branch as soon as its chunk checks pass.
  That merge needs no owner approval; the plan's approval authorizes it.
- Everything else the wave produces lands on the wave branch, in the wave
  worktree: the wave log and the execution state, plan revisions,
  captures, the sync, design changes. A chunk's branch is cut only once
  everything it should read is committed there.
- The wave branch merges `--no-ff` into `main` after its gate, when the
  owner asks. `main` only receives gated waves. Then its worktrees and
  branches are removed.
- The next wave branches from `main` once the previous wave has merged. If
  the owner wants to go on before merging, the next wave branches from the
  gated wave branch, and `main` is merged into it after.

## Intent gating under a plan

Where the repo declares intent (skill `intent-gating-protocol`), gating moves
from the task to the wave:

- **Wave preflight.** At the wave's start, `documentalist` runs one full
  preflight over every chunk of the wave, from the chunks' **Atoms** lines
  and **Files**. It returns a verdict per chunk. A halt stops that chunk
  only; the wave's other chunks go on. A spec gap goes to `spec-writer`, a
  design gap to `ux-writer`.
- **Captures.** In the same pass, before any code, `documentalist` records
  every **Architecture capture** the wave's chunks name, committed on the
  wave branch.
- **Chunks run no preflight.** A chunk owner calls `documentalist` only for
  a peek, when it meets an entry that contradicts the chunk, or an
  architectural decision nobody captured. It never resolves either alone.
- **Wave sync.** Once over the whole wave's diff, after the wave gate's
  tests (never while they run: an audit can saturate the machine). It
  applies every merged chunk's **Revisions**, which the plan's approval
  already authorized, and reports anything else as drift.

## Data register

Where the repo has a data register (skill `data-gating-protocol`), the gate
runs **once per version**:

- **Version preflight.** When `spec-writer` has a draft plan, it hands the
  plan (and the access model, if it changed) to `data-steward`. Its verdict
  goes into the chunks: `@data` IDs and adopted measures in each chunk's
  **Data** line, human decisions into the gates table.
- **Version sync.** At the release gate, `data-steward` runs one post-task
  sync over the release's whole diff.
- **In between.** An inserted chunk, or a ruling, that adds data the version
  preflight didn't cover gets a `data-steward` peek before the chunk starts.
