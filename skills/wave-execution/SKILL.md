---
name: wave-execution
description: Use when driving a build plan wave by wave (a `specs/versions/<v>/build-plan*.md` whose chunks are grouped into waves) — normally from the user's top-level session — to start a wave, get its single intent preflight and captures, dispatch each chunk to a coding-leader in chunk mode with the standard brief, run the wave gate and the sync, report to the owner and merge on request. Also covers mid-wave events (a blocked chunk, an insertion, a ruling, a chunk owner whose context is getting heavy).
---

# Wave execution (for the wave driver)

You run the plan; you don't write it. The model is
`~/.local/share/dev_team/references/build-plan-model.md`: read it once per
session before the first wave action, then the plan's header, gates table,
waves table and workflow deltas. Read a chunk's full text only when you
brief it.

What stays yours: the wave log, the execution state in the plan (each
chunk's **Status** and **Record** lines, the waves table's Status column, a
gate's status once it clears), dispatching, relaying between the owner and
the agents, the wave's merge into `main`.
What never is: plan content (send it to `spec-writer`), intent records
(`documentalist`), design (`ux-writer`), the code itself (the chunk's
`coding-leader`). Keep your own context small: you read reports, not diffs.

## Where every wave edit lands

Everything a wave produces besides chunk code lands **on the wave branch,
in the wave worktree**: the wave log, the execution state, `spec-writer`'s
plan revisions, `documentalist`'s captures and sync, design changes for the
wave. So:

- Brief every docs agent (`spec-writer`, `documentalist`, `ux-writer`)
  with the wave worktree and branch, and ask it to commit its own changes
  there.
- Make your own edits (the log, the state) in the wave worktree, not in
  the main checkout, and commit them there.
- Before you cut a chunk's branch, everything that chunk should read is
  committed on the wave branch. A chunk branch cut earlier reads the old
  plan.

The main checkout stays untouched until the wave merges. At release end,
the same rule holds for the last wave's branch (or a release branch the
plan's deltas name).

## Starting a wave

1. **Check it can start.** The previous wave has merged into `main`, or the
   owner said to go on without the merge (then branch from the gated wave
   branch, per the model). Every chunk's **Depends on** is merged or
   cleared, or the chunk is marked blocked from the start.
2. **Branch.** Create the wave branch and its worktree, as the plan's
   workflow deltas name them.
3. **Wave preflight.** In a repo with declared intent, dispatch
   `documentalist` once for the wave, on the wave branch's worktree:

   > Wave preflight for <release> wave <n> (build plan
   > `<path>`, model `~/.local/share/dev_team/references/build-plan-model.md`,
   > "Intent gating under a plan"). Chunks: <ids>. Run a full preflight
   > from each chunk's **Atoms** line and **Files**; give one verdict per
   > chunk. Then record every **Architecture capture** these chunks name,
   > before any code, and commit your record changes on branch `<wave
   > branch>` in `<worktree>`. Report per-chunk verdicts, the capture IDs,
   > and anything that needs the owner.

4. **Act on the verdicts.** A halted chunk is blocked (status
   `blocked (on <what>)`); route its gap to `spec-writer` (spec) or
   `ux-writer` (design), or put the question to the owner. The other chunks
   go on. Plan corrections the preflight found go to `spec-writer` now,
   before the first chunk starts, never "listed, not applied".
5. **Log.** Append the wave's entry to the wave log: date, chunks, the
   per-chunk verdicts, capture IDs, anything sent to whom.

## Running chunks

Dispatch chunks in the wave's order (topological, ties by number), at most
κ in flight (the plan's delta, default 1). One `coding-leader` per chunk,
in the background, with the brief below. Fill it from the plan and the wave
log; don't paraphrase the chunk's text and don't pre-settle its design
beyond what the plan, the spec and the design set already settle: that
judgment is the chunk owner's.

```
Chunk mode. Build chunk <id> — <title> of <release>, wave <n>.

Plan: <build plan path>, section "Chunk <id>" (read it in full), plus
§<read-first section> and the workflow deltas. Model:
~/.local/share/dev_team/references/build-plan-model.md.

Settled for this chunk:
- Wave preflight verdict: <verdict>; governing entries: <ids>.
- Architecture captured: <ids, or "none">.
- Data: <@data IDs and adopted measures, or "no register" / "none">.
- Rulings since the plan was written that touch it: <spec Dn, one line each, or "none">.

Branch: create worktree <path> on branch <release>-c<id>-<slug> from
<wave branch> (checked out in the wave worktree <wave worktree>); install
dependencies there. Work only in your worktree, and in the wave worktree
only to merge; never touch main or another worktree; never push.

Merge gate: <gate, or "none">.

Done: chunk checks per the model and the chunk's Verification line, with
the project's commands from the plan's deltas. Not the full suite or any
measurement unless that line names it. One commit (one per half if the
split rule applies). With no merge gate: merge --no-ff into <wave branch>
in the wave worktree (no owner approval needed); resolve a conflict in a
shared list (a test-script list, a README table) there, and stop and
report any other conflict; then remove your worktree. With a merge gate:
don't merge; report the chunk as built, its branch kept.

Stop and report instead of deciding if: an intent entry contradicts the
chunk; the chunk needs an architectural decision nobody captured; the code
must differ from the spec or the design. Make a WIP commit on your branch
first. Report it; never fix it silently.

If your context gets heavy before you finish: reach a point where the
checks you've written pass or are clearly listed as failing, make a WIP
commit on your branch, and report what is done and what is next. A fresh
owner will resume from it.

Report back: commit(s) and merge commit; Done when, item by item, with
evidence; checks run and their results; deviations from the spec or design
and where you reported them; anything left for the wave gate; risks.
```

When a chunk owner reports:

- **Merged.** Check the report against the chunk's **Done when** (not the
  diff). Set **Status** to `merged (w<n>, <commit>)` and add the **Record**
  line. Start the next chunk.
- **Built, waiting on a merge gate.** Status `built`; merge its branch
  into the wave branch yourself once the gate clears (it no longer counts
  against κ).
- **Stopped on a contradiction or a gap.** Mark the chunk blocked and go on
  with another chunk of the wave if one is ready. Route the question: an
  intent contradiction or a spec gap to `spec-writer` and the owner, a
  design gap to `ux-writer`, an uncaptured architectural decision to the
  owner or `spec-writer` to decide (the chunk owner's report proposes one).
  Once it is settled, `documentalist` records it (a capture, or the entry's
  revision, with the owner's sign-off where it needs one) on the wave
  branch; log it; then a fresh `coding-leader` resumes from the stopped
  chunk's WIP commit, with the settlement in its brief.
- **Paused (WIP).** Start a fresh `coding-leader` on the same brief, plus:
  "Resume from WIP commit <sha> on <branch>; its report: <paste>."
- **Owner wants a running chunk to pause.** Send the owner a message to
  pass on: reach a safe point, WIP commit, report. Don't kill it.

## Mid-wave events

Each of these follows the model's "Changing a wave once it starts":

- **A ruling arrives.** Have `spec-writer` record it and revise the plan.
  Pass the lines it changes to a running chunk owner only if they touch its
  chunk; otherwise the next brief carries them.
- **A chunk is still blocked when the rest is done.** It leaves the wave
  with its dependents in the wave; `spec-writer` moves it; log why.
- **A chunk must be inserted or split.** `spec-writer` revises the plan
  first. An inserted chunk gets a `documentalist` peek over its files (and a
  `data-steward` peek if it adds data the version preflight didn't cover)
  before it starts; log both.
- **Other agents commit on the wave branch** (captures, plan revisions,
  design). Fine; tell running chunk owners only when it changes what they
  build.

## The wave gate

When every chunk still in the wave is merged:

1. On the wave branch, on an idle machine (nothing else heavy running, no
   intent audit), run the wave-gate commands from the plan's deltas: run
   them yourself in the background and read the summary, or dispatch a
   `coding-executor` with "verification level: wave gate" when fixes are
   likely.
2. A failure: trace it to its chunk, then have a `coding-executor` fix it
   on the wave branch in its own commit. A fix that would change stated
   behaviour goes to `spec-writer` or `ux-writer` instead.
3. Record the figures (bundle, performance, with machine and date) for the
   wave's merge message and the wave log.
4. **Wave sync.** After the tests are done, dispatch `documentalist` once
   for the post-task sync over the wave's diff (from the wave branch's base
   on `main`), naming every merged chunk's **Revisions** to apply and every
   owner confirmation relayed during the wave. It commits on the wave
   branch.

## Report and merge

Give the owner a short report: chunks merged, chunks moved and why, the
gate's results, the bundle figure, the sync's changes, what needs the
owner's sign-off. Log it. Merge the wave branch `--no-ff` into `main` only when the
owner asks, with the figures in the merge message, then remove the wave's
worktrees and branches. Ask whether to start the next wave.

## Release end

After the last wave's gate, run the plan's release gate (usually its own
dispatch), on the last wave's branch before it merges, or on the release
branch the plan's deltas name; its commits (the release notes, the data
sync) land there. In a repo with a data register, dispatch `data-steward` for one
post-task sync over the release's diff. Then ask `spec-writer` (and
`ux-writer` where a `ui_ux/` tree exists) to archive the milestone with
skill `milestone-archive`.
