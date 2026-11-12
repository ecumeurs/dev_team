# UI/UX documents — the format

The shape of the tier documents `ux-writer` keeps under `ui_ux/`: what
sections each one has, how its content is cut into pieces, and how a piece
is named so that anyone can point at it and get exactly it. This file is the
one place that shape is defined. `ux-writer`'s prompt says what goes into the
documents and when; this file says how they are laid out.

Five readers depend on it:

| Reader | Uses the format to |
|---|---|
| `ux-writer` | write and revise the documents |
| `ux-critic` | check a section declared complete (skill `ux-validate`) |
| `spec-writer` | cite design items from a build plan's **Design docs** lines |
| `coding-leader`, `coding-executor` | read the items a chunk names, and only those |
| `doc-get` | print one section or item (`doc-get ui`), list them (`doc-get toc --ui`), gather a chunk's (`doc-get pack`), check this format (`doc-get lint ui`) and a plan's citations of it (`doc-get lint plan`) |

The tree itself (which documents exist and where) is in `ux-writer`'s
"The document tree" and in `doc-tree-conventions.md`.

## Why the format is strict

A handoff is read in pieces, never whole: a chunk owner needs the three
items its chunk changes, not a 200 KB screen. A piece can only be fetched
cleanly when it has a boundary and a name. A heading gives a section both. A
list item gives a boundary, and its bold label gives the name. Text with
neither can only be reached by searching for words in it and reading a
window around the hit, which brings in whatever surrounds it.

So every rule below serves one property: **everything a builder must follow
sits in a section or a labelled item, and every section and item has a name
that is unique where it stands.**

## The addressable pieces

**Sections.** The title is the only `#` heading. Sections are `##`
headings. A long section groups its items under `###` headings. Nothing
deeper: a labelled sub-item does that job. A heading title is unique in its
document, since two equal titles share one anchor.

**Items.** A list item that starts at column 0 inside a section is an item.
It runs from its bullet to the next line that starts at its own indent or
less, so its sub-items and continuation lines belong to it. An item opens
with its **label**, in bold, right after the bullet and after its change
tag if it has one:

```
- **Notice row.** `app-notice-row` is the first child of `layout-workspace`, …
- **[v3.3 new]** **Seventh chord symbols.** A chord symbol is its root, …
  - **Fit.** Each symbol's full width counts toward the minimum width of …
  - **Phone height.** Below `bp-tablet-landscape` the height that bounds …
- **Loading:** `staff-frame` holds the two empty system positions, …
- **Foundation** (`control-group`, `h3` "Foundation"): Tempo (`input-stepper`, …
```

- **The label is a name**, a few words for the element, state, rule or
  behaviour the item settles ("Notice row", "Loading", "Fit"), never a
  sentence. Its closing `.` or `:` is punctuation, not part of the name.
- **Every item in a handoff has a label**, and so does every sub-item that
  states a rule someone may need on its own (a fit rule, an exception, a
  focus move). A sub-item that only continues its parent (a list of values,
  an example) needs none.
- **Labels are unique among their siblings**: in their section for an item,
  in their parent item for a sub-item. Case and punctuation don't count, so
  "Fit." and "fit" are the same label.
- **A component's class name is not a label.** Write it in backticks in the
  item's text. An item about `jam-bar` is labelled "The kept doodle's bar",
  and others cite it by that label.
- **A change tag goes before the label**, never inside it:
  `- **[v3.3 new]** **Label.**`. An item whose only bold text is its tag has
  no label.

**Paragraphs and tables.** A section may open with a paragraph or two that
introduce its items. A rule a builder must follow goes in a labelled item,
not in a paragraph after the items, where nothing can point at it. A table
holds reference data (copy strings, a mapping) and is read through its
section; a row someone will cite on its own belongs in a labelled item
instead.

**Code blocks.** A layout tree or a mermaid diagram is one code block, read
as a whole through its section. Change marks inside it follow `ux-writer`'s
rule for code blocks.

## Names are addresses

A heading or a label is how build plans, change blocks, register entries
and briefs reach a piece. Renaming one breaks every citation of it, the same
as moving a file. Rename only when the old name has become wrong, and fix
every citation in the same change: the change block's line, the live build
plan's **Design docs** lines, and the "Now in" link of the decision that
made the change. `doc-get lint plan` lists the plan citations that no
longer resolve. Frozen copies in `versions/` keep their names; they are
never edited.

## Citing a piece

- **From outside `ui_ux/`** (a build plan, a spec section, a brief): link
  the document, then name its pieces in parentheses, exactly as written,
  separated by semicolons. A label that repeats in the document is scoped
  with its heading or parent item: `Heading: label`, `Item: sub-item`.

  ```
  [`screens/phrase-workspace/handoff.md`](../../ui_ux/screens/phrase-workspace/handoff.md)
  (Notation Contract: Seventh chord symbols; The score's spoken description)
  ```

- **Inside `ui_ux/`** (a change block, another tier document, a register
  entry): link the section's anchor, then the label after a colon:
  `([Notation Contract](#notation-contract): Seventh chord symbols)`.
- **Never cite by description** ("where the level never moves") or by line
  number. A description resolves to nothing, and line numbers move with
  every edit.

## The header block

Directly under the title, before the first section, in this order:

1. `> **New in <version>.**` when the document has no copy in the latest
   `versions/<version>/`; then there is no change block.
2. Otherwise, when it differs from that copy, the change block
   (`> **Changes since <version>**`), one line per change. Each line names
   where the change is: a section link, and the item's label after a colon
   when the change is one item. Removals link the frozen copy.

The block's wording and the inline tags follow `ux-writer`'s "Versions and
change marking". This file only fixes where they sit and how a line points
into the document.

## Screen handoff

`ui_ux/screens/<name>/handoff.md`. These sections, in this order:

| Section | Holds | |
|---|---|---|
| `## Layout Tree` | One code block with the element tree: element or class names, indentation for nesting, short notes in parentheses. Labelled items after it for what the tree can't show. | required |
| `## Components and Content` | One labelled item per element or group: the Tier 2 component, its content and copy, its behaviour. | required |
| `## <What it settles>` | A screen-specific contract, titled by what it settles ("Notation Contract", "What Save Does"). | as needed |
| `## Focus and Keyboard` | One labelled item per focus move or key: on open, on close, after each action. | required when the screen has anything focusable |
| `## Responsive Behavior` | One labelled item per breakpoint range, named by its breakpoint tokens. | required |
| `## States` | One labelled item per state, its label the state's name as other documents write it in bold (**Empty**, **Loading**, **Session running**). The Tier 1 edge-case policy's states are all there. | required |

## Flow handoff

`ui_ux/flows/<name>/handoff.md`. These sections, in this order:

| Section | Holds | |
|---|---|---|
| `## Flow` | The flow's overall mermaid diagram or numbered step map, naming each screen by its `screens/` name. | expected; a flow whose diagrams each belong to one stage keeps them in their stage sections instead |
| `## <Stage or topic>` | One section per stage of the flow or per topic that cuts across stages ("Entering and Leaving Jam Mode", "Saving the Session"), its rules as labelled items. | as needed |
| `## Routing Rules` | One labelled item per routing condition: what sends the user where, and when. | expected; routing conditions that belong to one stage may stay, as labelled items, in that stage's section |

What makes a flow readable in pieces is that every routing condition is a
labelled item somewhere; gathering them in one section is the default, not
a reason to empty the stage sections other documents cite.

## Intent documents

`ui_ux/flows/<name>/intent.md` and `ui_ux/screens/<name>/intent.md`: one
`##` section per topic ("The Focal Point", "What Was Left Out"). These are
reasoning, read whole or by section, so prose is fine and labels are
optional. The header block, the single `#` title and unique headings apply
as to every tier document.

## Strategy, motion and the README

`strategy.md` has one `##` section per Tier 1 part, named as in
`ux-writer`'s Tier 1 list (Problem alignment, Context of use, Mental
models, Trade-off analysis, Edge-case mapping, Flow index). The edge-case
policy is one labelled item per case, so a screen's States section can
match it item by item. `motion.md` and `README.md` have `##` sections and
no further rules.

## Size

- **A `##` section over about 20 KB** groups its items under `###`
  headings, each a coherent part of the screen or flow ("Header", "Score
  panel", "Controls"), so its table of contents stays readable.
- **An item over about 4 KB** splits its rules into labelled sub-items.
- A document has no size limit: its pieces are what gets read.

## Checking: `doc-get lint ui`

`doc-get lint ui` checks the root tier documents (never `versions/` or
`archive/`) against this file. It prints `path:line: error|warning:
message` and exits 1 when any error is found.

- **Errors** break an address: a tier document over 2 KB with no `##`
  section; a second `#` heading; two headings with one title; an unlabelled
  item in a handoff; two sibling labels that are the same; a required
  section missing from a screen handoff.
- **Warnings** make reading harder: an expected section missing (a
  screen's Focus and Keyboard, a flow's Flow or Routing Rules); sections
  out of order; a heading
  deeper than `###`; a section over 20 KB without `###` groups; an item
  over 4 KB without labelled sub-items; a change-block line whose link or
  label doesn't resolve; a register ID (`D12`, `Q4`) in a tier document.
`ux-writer` runs it on the documents a section touches before declaring the
section complete, and `ux-critic`'s validation counts its errors as DRIFT.

`doc-get lint plan` is the other side: it resolves every reference the live
build plan's chunks make (spec anchors, definition-of-done items, design
pieces, intent IDs) exactly as `doc-get pack` will, and lists each one that
doesn't resolve. A near name is reported, never taken: "What Is Saved" does
not stand for "What Is Saved, and When". `spec-writer` runs it whenever it
writes or revises a plan.

## Existing trees

A tree written before this format keeps its shape until the user asks for a
migration, per `doc-tree-conventions.md` ("Existing trees in another
shape"). The migration is one pass at the root: add the missing labels and
sections, fix the inbound citations, and leave `versions/` as it was. New
documents and new items follow this format from the start. Until the
migration, `doc-get` reads the old shape where it can and reports, rather
than guesses, what it can't address.
