---
name: intent-post-task-sync
description: Use when documentalist, in a repo with an intent register (`intent/README.md`, no `.atd`), is called after coding-leader (or any other agent) closes a coding task, to verify the intent-register entries touched by that work still describe what the code does, complete missing @intent tags, and report drift (trigger B, ongoing sync).
---

# Intent Post-Task Sync

Verify the entries touched by a just-closed coding task still describe what
the code does, complete missing tags, record anything the user confirmed,
and report drift without resolving it.

1. **Scope the change.** Use the file list or base commit the handoff gives
   you, or `git diff --name-only <base>` / `git log` to find what code
   actually moved. Read the diff itself (`git diff <base> -- <file>`), not
   just the file names.
2. **Collect the entries involved.** Three sources, merged:
   - tags in the changed code, including removed lines:
     `git diff <base> | grep '@intent'`;
   - the governing entry IDs the leader's handoff carries (preflight and
     architecture capture);
   - entries the diff plainly implements but that no tag or handoff
     mentions — search the register for the diff's key terms, as preflight
     D1 does.
3. **For every entry involved**, read it in full, plus the entries it
   `Serves` or that serve it, and compare its `Rule`/`Decision` and
   `Expectation` against what the changed code now does. Read the code; a
   tag's presence proves nothing about behavior.
4. **Classify each entry:**
   - **Aligned** — the code satisfies the entry's `Expectation`. If the
     handoff says the user confirmed a `draft` entry, set it to
     `confirmed`. Otherwise leave the status alone, and list the entry as a
     candidate for confirmation with the evidence (the code, and the tests
     tagged with it) — moving to `confirmed` is a human call, never yours.
   - **Missing tag** — code clearly implements an entry but carries no
     `@intent` tag. Add the tag: one comment line, in the file's comment
     syntax, directly above the specific symbol. Change nothing else in the
     file. Do the same for a test that clearly tests the entry.
   - **Dangling tag** — a tag names an ID that doesn't exist or is
     `retired`. Don't delete or retarget it; report it with file and line.
   - **No entry exists at all** — new behavior with no plausible entry. If
     the leader ran architecture capture during planning, this should be the
     exception (an emergent decision made mid-implementation), not the
     default. Don't record it silently: draft the entry (business or
     architecture, with its `Serves`) in your report and hand it back for
     confirmation. You don't originate intent on your own authority.
   - **Drift** — the entry and the code both exist and disagree: the code
     now does something the entry's `Rule`/`Decision`/`Expectation` rules
     out, or no longer does something it requires. **Stop. Edit neither the
     entry's meaning nor the code.** Add one `Drift:` line to the entry
     naming both sides (the code's file:line and what it does, against what
     the entry says) and the task that surfaced it. Report it. The leader or
     a human decides which side is wrong.
5. **Apply what the handoff settled.** A preflight draft the user rejected
   and that never became code comes out of the register (it was never
   declared intent). A drift the leader resolved — by fixing the code, or
   by asking you to revise the entry with the user's sign-off when it's
   `confirmed` — gets its `Drift:` line removed once the two agree again.
   An entry the leader says no longer applies is set to `retired` with a
   `Retired:` line; its tags must come off the code in the same task, so
   report any that remain.
6. **Close the loop.** Run the consistency checks from the format reference
   (`~/.local/share/dev_team/references/intent-register.md`) on the whole
   register, since a tag change anywhere can dangle.
7. **Report** status changes, tags added, entries recorded or retired, and —
   most importantly — every drift you flagged and did not resolve yourself.
