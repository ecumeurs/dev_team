---
name: spec-personas
description: Use when spec-writer starts a product or feature with an interface or workflow still to design and its users aren't written down yet, when the user describes who the product is for, or when an existing personas document needs revising — to elicit, write, use, and maintain the personas document (who it's for, their goals, their context of use) that scopes the spec and grounds ux-writer's design.
---

# The Personas Document

Whenever the product has an interface or workflow still to be designed, which
covers anything `ux-writer` will work on, the spec carries a standing
**personas** document. It says who the product is for, what each of them is
trying to get done, and the circumstances they use it in. Follow the layout
in `~/.local/share/dev_team/references/persona-template.md`.

A personas document that nobody consults is decoration. Its value comes from
being the lens you scope with and the ground `ux-writer` designs from, so
writing it is half the job and using it is the other half.

## When to start it

- **Early in inception, before the mechanics settle.** Personas are an input
  to scope, not something retrofitted afterwards. If the idea arrives with
  mechanics already in mind, start the personas document alongside them anyway.
- **Skip it only when there is nothing to design for.** An example is a
  headless tool whose only user is the person asking. Record the skip in one
  line in the spec index so the absence reads as a decision.
- **On an existing product with no personas document**, propose starting one
  when the next milestone's scope is being set, not in the middle of a
  milestone. Personas introduced onto shipped work usually expose fit gaps.
  Track those in the draft's *Fit findings* section.
- **On an existing personas document in a different shape**, don't rewrite it
  wholesale. Migrate it section by section when a decision next touches it,
  and get the user's agreement first. Missing required sections (usually
  Context of use) are worth raising as open questions straight away.

## Eliciting without fiction

- Start from the user's own description. Draft a strawman persona and let them
  correct it. Ask one question at a time.
- The user decides who the personas are, which one is primary, and what their
  goals are. Every such decision goes in the decisions log and stays
  `(proposed)` until the user confirms it.
- Ask the three questions that usually go unasked:
  - **Context of use.** Where are their hands, eyes and attention while they
    use it? On what device? For how long? In what environment?
  - **Current alternative.** What do they use today, and where does it fail
    them?
  - **Non-target.** Who is this deliberately *not* for?
- Check for **the owner's bias**. Ask whether the user is one of the personas.
  If they are, record it and look for a secondary persona that pulls the other
  way. That persona is the counterweight, not padding.
- Be honest about the basis. Assumption-based personas are a legitimate start,
  labeled as such. Never dress up a guess as research.
- Apply the template's load-bearing rule as you write. If a line wouldn't
  change any spec or design decision, cut it.

## Using personas while specifying

- **Trace scope to goals.** When a mechanic or feature is specified, name the
  goal ID or IDs it serves in the topic document. Something that serves no goal
  is a scope question to raise, not something to keep quietly. A primary goal
  that nothing in the milestone serves is a gap to raise, or an explicit
  deferral to record in the coverage table.
- **Surface tensions.** When two personas' goals pull a decision apart, say so,
  let the user settle it, and record the result in the Tensions section. The
  primary persona wins by default, but only once the user has seen the
  tension.
- **Mine context of use for questions.** Each persona's context of use drives
  the Interaction, Non-functional and Edge-case items of the ambiguity
  checklist. Examples: hands busy leads to "what input is available
  mid-task?", and a noisy room leads to "is audio feedback enough?".
- **Align terminology.** The persona's vocabulary informs the spec's canonical
  terms. Where the two differ on purpose, note it.
- **Keep roles separate.** If a sentence says what a persona may or may not
  *do*, it belongs in the access model. The personas document only maps
  personas to actors.

## Maintaining it

- The personas document is a standing document, edited in place. Every change
  is a decision in the log.
- **Changing the primary persona, retiring a persona, or dropping a goal is a
  scope event.** Re-check each version's scope against the change, and tell
  the user which settled decisions it now puts in question. Don't silently
  re-derive them.
- Never renumber a persona or goal ID. A retired persona stays listed as
  retired, with the reason.
- The personas document is never archived with a milestone. Its resolved *Fit
  findings* leave it the normal way: the decision goes to the log, and the
  settled consequence goes into a topic document.

## Handing it off

- Before handing off a master spec that depends on the personas document, bring
  the document to its **settled** state and run the template's completeness
  check.
- The master spec carries a self-sufficient summary of the personas and the
  goals it serves (skill `spec-consolidate`).
- Forward the personas document itself to `ux-writer`, alongside the master
  spec and the access model. Don't forward it to the intent owner
  (`documentalist`, or `intent-keeper` without ATD), which takes the personas
  from the master spec's summary and never from this document.
- If `ux-writer` comes back with a persona gap (a context of use nobody
  described, or a goal a flow clearly serves that isn't listed), treat it like
  any other open question. Settle it with the user, then update the document.
