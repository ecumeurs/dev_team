# Personas — document layout

The layout for the **personas** document: the standing companion `spec-writer`
keeps beside the spec whenever the product has an interface or workflow still
to be designed. It is the single authoritative answer to "who is this for,
what is each of them trying to get done, and in what circumstances do they
use it."

It exists because personas do work in three places, and each stalls or
guesses without them:

- **`spec-writer`** scopes with it. Every in-scope item serves a named goal. A
  feature that serves no goal is a scope question. A primary-persona goal that
  nothing serves is a gap. When two personas pull apart, the document records
  which one wins.
- **`ux-writer`** designs from it. Problem alignment, mental models and the
  context the design has to survive all come from here. It is barred from
  inventing personas, just as it is barred from inventing roles.
- **`ux-critic`** judges with it. "Who it breaks for" names a persona, not
  "users".

The master spec carries a short, self-sufficient summary of the personas and
the goals it serves (see skill `spec-consolidate`), so `documentalist` and
`coding-leader` get what they need without this document. This document stays
the full reference.

## Personas are not roles

The access model's actors say **what someone may do**. Personas say **why
someone is here and how they work**. The two axes are independent:

- One actor can cover several personas. A music-practice app may have a
  single `player` actor and three personas with different goals.
- One persona can act as several actors. A "team lead" persona might be both
  `member` and `project-admin`.

The personas document maps each persona to the actor or actors it acts as.
It never grants or restricts anything. A sentence about what a persona is
*allowed* to do belongs in the access model.

## Standing, not per-milestone

Unlike the master spec, the personas document outlives milestones. It is
edited in place as understanding changes. It is never re-consolidated for each
version, and it is never archived with a closed milestone. It has two states:

- **Draft**: carries a `Status: draft vN` line, tags anything the user hasn't
  confirmed `(proposed)`, may cite open-question IDs (`O4`) inline, and may
  keep a *Fit findings* section (see §8).
- **Settled**: the state it must be in before a master spec that depends on it
  is handed off. The primary persona and every goal the milestone serves carry
  no `(proposed)` tag, and the completeness check below passes. Decision or
  question IDs may remain **only as provenance**: the sentence must read
  completely with the ID deleted (`**Primary persona** (D48)` is fine, while
  `see D48 for the goal` is not). Anything unresolved is restated in plain
  language under *Known gaps*.

**Persona and goal IDs are content identifiers, not tracking IDs.** They are
defined here and restated in the master spec. The master spec and `ux-writer`'s
tier documents may cite them freely, which is not true of `O#`/`D#`. They are
stable forever. Never renumber or reuse them. A retired persona stays listed,
marked retired, with the reason.

Suggested filename: `specs/personas.md`. Use a `specs/personas/` folder with
one file per persona only when each persona has grown long enough to warrant
it. If the tree already has a location, keep it.

## The load-bearing rule

Every line must be able to change a spec or design decision. If deleting it
would change nothing, delete it. That rules out stock biography, invented
favorite brands, a stock photo and a decorative quote. Keep demographics only
when they change a decision. When a reader might assume a target, say
explicitly that there isn't one (for example "no age or gender target"). A
quote belongs only when it is the user's (or a real user's) actual words and
captures a goal better than a paraphrase.

---

## Layout

### 1. Summary

One row per persona, primary first, then secondary, then any retired.

| ID | Persona | Priority | Core want | Acts as | Served mainly by |
|---|---|---|---|---|---|
| P1 | The Curious Improviser | Primary | Learn improvisation by playing | `player` | v1, then v2 |
| P2 | The Speed Builder | Secondary | Read and play faster | `player` | v2 |

**Exactly one primary persona.** Having two primaries means nobody wins a
tension by default. If the product truly needs two, say why and state how
their tensions are settled (§6).

Say that names are working names if they are.

### 2. Basis and bias

State once what the personas rest on: user research (interviews, analytics,
support logs), the product owner's own domain knowledge, or assumption. An
assumption-based "proto-persona" is a legitimate starting point, but only when
it is labeled as one. Flag the exceptions persona by persona.

Name the known biases. The most common one is **the product owner is one of
the personas**. It is fine to record that, but say which persona exists to
pull the other way.

### 3. Per persona: `P<n> — <working name> (<priority>)`

**Required** subsections:

- **Who.** Only load-bearing traits: domain expertise (what they can already
  do, and what they can't yet), relevant skills and gaps, comfort with
  technology, and attitude. Say what the persona is *not* tied to when a
  reader might assume it is (an instrument, a device, a job title).
- **Goals.** Each goal gets a stable ID, unique across the document. The
  persona-prefixed form `P1.G1` is recommended so that a bare citation says
  whose goal it is. A project with an established scheme keeps it. Phrase each
  goal as an outcome in the persona's terms, never as a feature: "gain speed
  reading unfamiliar material", not "adaptive tempo". Experience goals ("never
  feel graded") count as goals.
- **Context of use.** Where, when, for how long, on what device and input, and
  where their hands, eyes and attention are while using it. Include
  interruptions and environment (noise, distance to the screen, standing or
  seated). This is the most design-relevant section and the one most often
  missing. "Both hands are on the instrument while playing" rules out a whole
  class of interaction before any screen is drawn.

**Optional** subsections, included when they are load-bearing:

- **Mental model and vocabulary.** How they think about the domain, the terms
  they use, and what they expect things to mean. When this drives a product
  decision, name the consequence in one line ("they pick keys in their own
  instrument's pitch, so transposition belongs to the instrument").
- **Current alternatives and frustrations.** What they do today instead, and
  where it fails them. This is the gap the product fills.
- **Boundaries.** What would put them off, or what they explicitly don't want
  ("being scored"). These often harden into guiding principles.
- **Why they matter to the spec.** Mainly for secondary personas: which
  decisions they stress-test that the primary persona doesn't.

### 4. Non-target personas

Candidates that were considered and dropped, each with the reason in one line.
This stops the same candidate from being re-proposed. It also tells
`ux-writer` whom not to optimize for. If none were considered, write "none
identified", not an empty heading.

### 5. Actor mapping

Include this only when an access model exists: which actor or actors each
persona acts as. If every persona is the same single actor, one line says so.
No permissions go here.

### 6. Tensions

Places where two personas' goals pull a decision in different directions, and
how each one was settled.

| Tension | Personas | Resolution |
|---|---|---|
| Time pressure while reading | P1 (own pace) vs P2 (speed) | v1 has no pressure; v2's pressure is opt-in and mild |

The default resolution is that **the primary persona wins**. Record a tension
even when the default settled it, so that nobody re-argues it.

### 7. Goal coverage

Every goal against the milestones, at coarse grain: *full*, *partial (how)*,
or *not yet*. The master spec states the per-milestone detail. This table is
the cross-version view that shows a primary goal with no home.

| Goal | v1 | v2 | v3 |
|---|---|---|---|
| P1.G1 Vocabulary by exposure | full | full | full |
| P1.G2 Real-time reading | partial (own pace) | full | full |

### 8. Fit findings (draft only)

When personas are introduced onto an existing product, this section holds the
gap analysis: where the shipped product fails a persona. Each finding moves
out once it resolves. Its decision goes to the decisions log, and any settled
consequence goes into the relevant topic document. A settled personas document
keeps only unresolved findings, and those go under *Known gaps*.

### 9. Open questions (draft) / Known gaps (settled)

Draft: open questions, which may cite IDs. Settled: every unresolved persona
question in plain language, with its consequence for scope or design.

---

## Completeness check

Run this before handing off a master spec that depends on the document.
`ux-writer` and `ux-critic` both rely on these points holding:

- Exactly one primary persona, or an explicit reason for more with the
  tension rule stated.
- Every persona has Who, at least one goal, and Context of use.
- Every goal has an ID that is unique in the document, and no ID has been
  reused or renumbered.
- Every goal is phrased as an outcome, not a feature.
- Every goal appears in the coverage table (§7), and every goal the next
  milestone claims to serve is marked there.
- Every tension that a spec decision had to settle has a row in §6.
- The basis is stated, and known biases (including "the owner is this
  persona") are named.
- Non-targets are listed, or "none identified" is written.
- When an access model exists, every persona maps to at least one actor, and
  no permission statement appears anywhere in this document.
- No `(proposed)` tag remains on the primary persona or on a goal the milestone
  serves.
- Any `O#`/`D#` left in the document is provenance only: every sentence still
  reads completely with the ID deleted.
