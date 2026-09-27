---
name: milestone-archive
description: Use when a milestone closes — a version is released, or a step or batch of work (such as a set of issues) is finished — for spec-writer to archive the spec tree (specs/) or ux-writer to archive the UI/UX tree (ui_ux/), including when a leader asks for it. Sorts every register entry and document, moves milestone-only records verbatim into an indexed archive with a "where it now lives" table, trims the live registers, and checks that no link dangles and nothing still open was archived.
---

# Milestone Archive

When a milestone closes, the working record that belonged only to it moves out
of the live tree into an archive. The archive is kept verbatim, and the live
tree is trimmed to what is still true, still open, or still needed. Nothing is
lost: every settled fact already lives in a live document, every archived entry
can be found from an index, and every open item stays live.

**Owner and scope.** `spec-writer` runs this for the spec tree (`specs/`), and
`ux-writer` runs it for the UI/UX tree (`ui_ux/`). A leader may request it, but
the tree's own writer does the work. Run it for **one milestone at a time**,
and name that milestone first, for example `v1` or `2026-09-26 v1.0 gate`. The
name gives the archive folder its slug (`archive/v1/`,
`archive/2026-09-26-v1.0-gate/`). Name everything as
`~/.local/share/dev_team/references/doc-tree-conventions.md` sets out.
An existing archive in another shape stays as it is: renaming it is a
migration the user asks for, not part of an archive pass.

**Where the archive lives.**

- Spec tree: `specs/archive/<milestone>/`.
- UI/UX tree: `ui_ux/archive/<milestone>/`.

Each tree has a top-level `archive/README.md` index, and each milestone folder
has its own `README.md`. Create both on the first pass.

## 1. Inventory

Before you move anything, list every candidate:

- Every entry in the decisions log (`specs/decisions.md`, `ui_ux/decisions.md`).
- Every entry in the open-questions register (`specs/open-questions.md`,
  `ui_ux/open-questions.md`), including closed-question prose that is still
  sitting in it.
- The sections and items of `ui_ux/todo.md`.
- Every document tied to the milestone: version folders, execution reports,
  feasibility reviews, plans, and superseded snapshots.

Record the set of open question IDs now. The final check compares against it.

## 2. Classify

Put each candidate in exactly one class. If you can't tell whether something
is milestone-only or still live, **ask the user**. Don't guess.

- **(a) Settled fact, still true and needed.** First make sure it is stated as
  fact in a live document: a topic doc, version README or master spec, or for
  `ui_ux/` a tier doc (`strategy.md`, `motion.md`, the token file, a flow's or
  screen's `intent.md`/`handoff.md`). Tier docs must stay free of IDs. If the
  fact isn't in a live document yet, write it there first as a normal edit
  under the tree's own rules, or leave the entry live. Once the fact is in a
  live document, the entry can be archived, and it gets a row in the "where it
  now lives" table.
- **(b) Milestone-only working record.** This covers execution reports,
  feasibility reviews, finished todo sections, closed questions, and
  superseded or withdrawn decisions. Move it to the archive verbatim.
  Superseded entries are marked as history in the table and get no live home.
- **(c) Still open or still pending.** Open questions, pending todo items and
  decisions still waiting to be applied stay live and are carried forward.
  Where a next-version folder exists, cross-link the item to it. The spec
  tree's version folders belong to `spec-writer`, so `ux-writer` asks for that
  entry rather than writing it. Never silently drop an item from this class.
- **(d) Referenced from outside the tree.** Before you move any document, find
  every file that links to it: `git grep -n -e '<path>' -e '<basename>'`
  across the whole repo. Referrers can be other docs, issues, READMEs, code
  comments or tests. Then pick one:
  - Move it, and fix every inbound link in the same pass.
  - Leave it in place, and list it in the milestone README's "left in place"
    table with its role and its referrers.

  Prefer leaving it in place when any referrer is a file you may not edit,
  such as application source for `ux-writer`. It is also the better choice
  when the document is still the contract for running code.

  ATD atoms are never a reason to keep a document in place. Atoms must be
  self-sufficient: they never link to, cite, or depend on a document outside
  the atom set (spec, ui_ux, issue, or register ID). An atom that does is
  already an ATD violation, whatever the archive does. Report it to
  `documentalist` to inline the content, and archive the document on its own
  merits.

**Standing documents are never archived as a unit.** The spec tree's
personas document — and any other document that describes the product rather
than a milestone, such as a vision — stays live and is edited in place. Only
milestone-bound material inside it (for example a personas document's
resolved fit findings against a closed version) follows the classes above.

## 3. Archive

- **Move with `git mv`**, keeping each file at the same directory depth when
  you can (for example `specs/versions/v1/` to `specs/archive/v1/`). That way
  its relative links still resolve.
- **Add one archive notice at the top** and change nothing else:
  `> **Archived <date>.** <why it closed>. Live summary: <link>.` If the
  relative links no longer resolve from the new location, the notice must say
  so: "Relative links were written from `<original dir>`."
- **Archived files are frozen.** The notice, the path repair of links to
  files moved in the same pass, and an archiving-pass addendum (below) are the
  only edits, and all of them happen in the archiving commit. After that, never edit an archived file.
- **Verbatim means the moved text is never rewritten, even to correct it.** If
  archiving reveals that an archived statement is stale or wrong (for example
  a "queued" item that has since shipped), leave it as written and append a
  clearly dated addendum (`## Archiving-pass addendum (<date>)`) that records
  what was found true and says it is new text.
- **Append-only logs are archived as a closed, contiguous range.** Move the
  entries verbatim to `archive/<milestone>/decisions-D<first>-D<last>.md`, and
  do the same for a question history (`open-questions-Q<first>-Q<last>.md`).
  Every entry in the range must be class (a) or (b). If one isn't, end the
  range before it.
  - When closed entries are interleaved with still-open ones (common in a
    question register), don't force a range. Extract each closed entry to its
    own file (`open-questions-Q15.md`), and name each one in the live header.
  - The live log keeps a header that names each archived range and its link,
    says that archived IDs keep their meaning, and gives the next ID
    ("Numbering continues from D45"). Never renumber anything.
  - A citation by ID elsewhere stays valid through that header, so don't
    rewrite it.
  - In an append-only log, whether live or archived, only link paths may
    change. The wording never does.
- **Split `ui_ux/todo.md` by section.** Move the finished sections and the
  done items for the milestone verbatim to `archive/<milestone>/todo.md`.
  Leave `In Progress`, the pending items in `Remaining`, and `Next Unit` live.
  Add one line under `Complete` that points to the archived record.
- **Write the indexes.**
  - The milestone `README.md` holds a status line
    (`Status: archived <date>`), a list of the archived files with a one-line
    purpose for each, the "where it now lives" table (decision and question
    IDs mapped to live documents, with history rows marked as such), and the
    "left in place" table.
  - The top-level `archive/README.md` states the rule ("Files here are kept
    verbatim and are never edited"), has a row per archive entry, and notes
    where relative links were written from.
  - Archive READMEs are working registers, so IDs are allowed in them.

## 4. Clean up the live tree

- **Trim the live registers.** The open-questions register keeps
  only questions that are truly open, with their original IDs. The decisions
  log keeps its header and any entries after the archived range.
- **Mark the milestone's status in the tree's index files.**
  - Spec tree: the `specs/README.md` status snapshot, the versions index
    table, and the version README's `Status:` line.
  - UI/UX tree: `ui_ux/README.md` (a tier doc, so no IDs; name the archive in
    its map) and `todo.md`.
  - Bump the `Status: draft vN` line of every live spec document you edit.
- **Record the archive action in a live log only if that tree already does
  so.** The spec log records milestone events ("D75 — the v1.0 gate is
  closed; its working documents are archived"). `ui_ux/decisions.md` records
  design decisions only, so there the note goes in `todo.md`.

## Boundaries

- Never touch ATD atoms (`docs/*.atom.md`); `documentalist` owns them. Atoms
  must never reference documents outside the atom set; report every atom that
  does (a moved file or not) as a self-sufficiency violation for
  `documentalist` to fix.
- Never delete, close or move the issue tracker or its files, or any
  deliverable: code, tests or release evidence. You may repair link paths in
  them. Don't change their wording.
- Never decide an open question while archiving. Resolving a question is a
  separate, user-confirmed decision.
- In the other writer's tree, you may repair link paths only.
- Commit once per tree, or follow the host repo's commit workflow (worktree,
  merge style, quality gate) where it has one.

## Verification

Check every item before you report the pass as done:

1. **No dangling links.** Grep the whole repo for each moved file's old path
   and basename. There are zero hits outside git history, the archive's own
   notices, and link text that was checked on purpose. Every relative link in
   the files you edited resolves, and every link in a moved file resolves or
   is covered by its notice.
2. **Every archived entry is accounted for.** Each moved decision or question
   has a "now lives" row or is explicitly marked as history.
3. **Nothing open was archived.** The open IDs recorded in step 1 all still
   appear in the live register, and every pending todo item is still live.
4. **Numbering is continuous.** The live log's header names every archived
   range and the next ID, and no ID was reused or renumbered.
5. **The formatter passes on the changed files.** Run the host's formatter or
   linter check on exactly the files you changed. Run the same check on those
   files at the base commit to separate pre-existing failures from new ones,
   and fix only the new ones.
6. **The report lists:** what moved and where; what stayed in place and why;
   any atom that references an outside document, for `documentalist`; the items carried
   forward; and any question you had to put to the user.
