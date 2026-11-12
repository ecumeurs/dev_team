# Document trees — shared conventions

`spec-writer` keeps the spec tree (`specs/`) and `ux-writer` keeps the UI/UX
tree (`ui_ux/`). The two trees do the same jobs, so they use the same names
for them. A reader arriving cold should be able to navigate either tree
after learning one, and that includes a leader, `ux-critic`, or the other
writer.

## Names

- **Lowercase kebab-case** for every file and folder you create:
  `generator-contract.md`, `flows/controller-connection/`. The exceptions are
  `README.md` and two fixed names in the UI/UX tree: the tree root `ui_ux/`,
  and the token file `ui_common.css`, which application code imports.
- **Name by content, not by date or state.** Use `rolling-phrase.md`, not
  `2026-09-25-rolling-phrase.md` or `rolling-phrase-draft.md`. The
  `Status:` line records the state, and git records the date.
- **Milestone folders** are named after the version (`v1`, `v2`,
  `v5-plus`). A milestone that isn't a version uses
  `<yyyy-mm-dd>-<slug>` (`2026-09-26-v1.0-gate`).
- **A folder holding more than a couple of documents has a `README.md`**
  that lists them with a one-line purpose each.

## The shared skeleton

Both trees have these files at the root, one file per job:

| Job | `specs/` | `ui_ux/` |
|---|---|---|
| Index and status snapshot | `README.md` | `README.md` |
| Open-questions register | `open-questions.md` (`O1`, `O2`, …) | `open-questions.md` (`Q1`, `Q2`, …) |
| Decisions log, append-only | `decisions.md` (`D1`, `D2`, …) | `decisions.md` (`D1`, `D2`, …) |
| Progress tracker | none; the index's status snapshot does this job | `todo.md` |
| Closed milestones | `archive/` | `archive/` |

### Spec tree only

```
specs/
  <topic>.md                one per topic or concern
  <concern>/                a group of topic docs, once the root is crowded
  personas.md               standing: who the product is for
  versions/
    README.md               versions index
    <version>/
      README.md             the version's scope and status
      master-spec.md        the consolidated deliverable for that version
      access-model.md       its companion, when there is more than one kind of user
      build-plan.md         the version's build plan (build-plan-<release>.md when it ships as several releases)
      wave-log.md           the build's execution record, kept by the wave driver (wave-log-<release>.md beside a per-release plan)
```

A project without versions keeps `master-spec.md` and `access-model.md` at
the `specs/` root. The build plan's format is `build-plan-model.md` in this
directory. Standing documents, which describe the product rather than
one milestone (`personas.md`, a vision), live at the root and are never
archived.

### UI/UX tree only

`strategy.md`, `ui_common.css`, `motion.md`, `flows/<flow-name>/` and
`screens/<screen-name>/`, each of the last two holding `intent.md` and
`handoff.md`. The layout is set in `ux-writer`'s document tree; the shape of
each document (its sections, its labelled items, how a piece is cited) in
`ui-ux-docs.md` in this directory.

```
ui_ux/
  versions/
    <version>/        an approved version's design, frozen, with a summary README
```

Both trees have a `versions/` folder, for different things. The spec tree's
holds each version's scope and master spec, including versions not yet built.
The UI/UX tree's holds only designs the user has approved, copied there
frozen; everything else at the `ui_ux/` root is the next version's work in
progress, specified in full, with what it adds, changes and removes marked.
The rules are in `ux-writer`'s "Versions and change marking".

## Archive

- `archive/README.md` indexes the archive. Each closed milestone gets
  `archive/<milestone>/` with its own `README.md`. Nothing sits loose at the
  archive root.
- A moved document keeps its name, and its depth where possible
  (`specs/versions/v1/` becomes `specs/archive/v1/`). The UI/UX tree's
  `versions/` is never archived: it is the frozen design, not a working
  record.
- An archived slice of a register keeps the live file's name and adds the ID
  range: `decisions-D45-D71.md`, `open-questions-O12-O30.md`. A single
  extracted entry uses its one ID: `open-questions-Q15.md`.

## Decision entries: short, and archived with each release

A decisions log is looked up by ID (a grep for the heading), cited from
other documents, and written to constantly. It is almost never read whole,
and most of an entry's content also lives in the document the ruling
changed. So an entry is a pointer with a reason, not a second copy:

```
- **D<n> (<date>): <the ruling in one phrase>.** <What was decided, one or
  two sentences. Why, one sentence, only if it isn't obvious. Closes O<m>
  when it does.> Now in: <link to the spec section, design document or plan
  that states it>.
```

- **Aim for six lines or fewer.** Never restate text that the master spec,
  the design set or the plan now says: link it, and make the edit to that
  document in the same pass, before you write the entry.
- **A decision with no other home keeps its reasoning**, up to about ten
  lines: a process choice, a rejected alternative, a trade-off nobody wrote
  into a document. The log is then the only record, so it must explain
  itself. Say what was rejected in one line.
- **No change reports in an entry.** "No behaviour changed; the spec now says
  what is built" and lists of which agent applied what belong in the commit
  message or the wave log.
- **IDs stay stable and bare in their tree** (see below). Other documents cite
  the ID, never the text.
- **Existing entries are not rewritten.** The log is append-only and its
  archive is verbatim; the short form applies from the next entry on.
- **Nobody reads a log whole.** Look an entry up by its ID (find the heading,
  read that entry), or read the window around the range you need. A cold
  session resumes from the tree's index and its open questions, not from the
  log.
- **Archive with every release.** When a release closes, its decisions leave
  the live log with the rest of its working record (skill
  `milestone-archive`), so the live log holds the current release's
  decisions and any older ruling still being applied. Cited IDs stay
  resolvable through the archive index's "where it now lives" table.

## IDs across the two trees

Both trees number their decisions `D1`, `D2`, … independently, so a bare
`D45` is ambiguous outside its tree. Inside its own tree an ID stays bare.
Anywhere else, qualify it with the tree: in the other tree's registers, an
issue, a commit message, or a leader's brief or report. Write `spec D104`,
`ux D45`, and for consistency `spec O24` and `ux Q7`. Never renumber to avoid
the clash. The master spec and the UI/UX tier documents carry no tracking IDs
at all, so the rule only ever applies to registers and to text outside the
trees.

## Numbering: `doc-ids`

A new ID comes from the `doc-ids` command, never from reading the log. The
header's "continues from" line goes stale with the first new entry, and
another branch or worktree may already hold the next number.

- **`doc-ids next spec D`** (or `spec O`, `ux D`, `ux Q`) prints the next
  free ID and reserves it for every worktree of the repo. It reads this
  worktree, every other one, the archives and the earlier reservations. Ask
  for it when you write the entry. `--peek` shows the number without
  reserving it.
- **`doc-ids lint`** before committing a register change. An ID defined
  twice is an error. A citation past the highest ID, the other tree's ID
  cited bare, and a stale "continues from" line are warnings.
- **`doc-ids compare main <branch>`** before merging a branch that wrote to
  a register (main, or whichever branch it merges into, comes first). A
  collision, meaning both sides added a different entry under one number, is
  fixed on the incoming branch before the merge, with the command it prints.
- **`doc-ids renumber <tree> <ID>`** prints a dry run, then `--apply` writes
  it. It rewrites the entry and every citation that can only mean it. It lists
  the rest for you to settle by hand: a mention inside a range
  (`D339–D341`), an unqualified mention outside the trees, archived text,
  and a citation that may mean another entry.
- **A collision is the one case that renumbers.** The entry already on the
  target branch keeps its number. The incoming one is renumbered with its
  citations, and the log's header records the old number ("D350 was D339 on
  branch `plan-migration`"). An ID already on `main` is never renumbered.
- **A duplicate already merged** shows in `doc-ids lint`, with each entry's
  origin and every citation. Renumber the newer one with
  `--def FILE:LINE`, and `--take` each citation that means it.

## Reading: `doc-get`

Read a targeted piece of either tree, the build plan or the intent record
with the `doc-get` command, not with grep and a window of lines. A grep
window brings in whatever surrounds the hit, and a reader can't tell the
target from its neighbours. `doc-get` prints the target from its own
heading or entry to where the next one at the same level begins, after a
`==> path:lines · what <==` marker to cite it by. When the target is missing
or ambiguous, it prints nothing and exits 1, naming the candidates.

| Need | Command |
|---|---|
| A chunk, or some of its fields | `doc-get chunk 10`, `doc-get chunk 10 -f files -f "done when"` |
| A master spec section, or items of a numbered list | `doc-get spec D7.1`, `doc-get spec D15 --item 11` |
| Any document's section | `doc-get section plan "Workflow deltas"`, `doc-get section docs/x.md some-anchor` |
| A register entry, live or archived | `doc-get decision D527`, `doc-get decision ux D459`, `doc-get question O267` |
| An atom or intent entry, whole or by section | `doc-get intent rule_x -s rule -s expectation` |
| A design section or labelled item | `doc-get ui phrase-workspace "Notation Contract: Seventh chord symbols"` |
| What a document holds, before reading any of it | `doc-get toc spec`, `doc-get toc --ui flows/jam` |
| A chunk with every spec section, design item and intent entry its lines point to | `doc-get pack 10` (`--refs-only` leaves the chunk's own text out) |
| Check the UI/UX documents' format | `doc-get lint ui` (`ui-ux-docs.md`) |
| Check that every reference a plan's chunks make resolves | `doc-get lint plan` |

A design item is addressed by its heading or the bold label that opens its
list item (`- **[v3.3 new]** **Seventh chord symbols.**`), scoped with
`Heading: label` or `Item: sub-item` when a label repeats (`ui-ux-docs.md`).
A lookup typed by hand may match a name by prefix and says so; a citation
(`pack`, `lint`) must match exactly. `pack` resolves
what the plan names exactly; anything it can't resolve it lists under
"Unresolved references" rather than guess, and a reader reports those
instead of searching for them.

## The intent record is not a third tree

The declared-intent record — ATD's `docs/` or, without ATD, the intent
register `intent/` — belongs to `documentalist`, not to either writer, and
follows its own format rather than the skeleton above. The register's format
is `intent-register.md` in this directory: no open-questions register,
decisions log or archive, and an entry that stops applying is retired in
place. Atom and entry IDs are named slugs such as `guest-checkout`, never
numbered, so they can't clash with `D`, `O` or `Q`. Neither tree writes into
the record, and the record never cites a tree's IDs.

## Existing trees in another shape

Don't rename anything on your own initiative. Bringing an existing tree onto
these conventions is a migration, and it happens only when the user asks for
it or agrees to it. Do it as its own pass: `git mv`, then fix every inbound
link, with the same no-dangling-links check as skill `milestone-archive`.
The pass may rename archived files, but it never changes their wording.
Until that pass happens, work with the names the tree already has. A new
file still follows these conventions unless it would break a pattern
already established next to it.
