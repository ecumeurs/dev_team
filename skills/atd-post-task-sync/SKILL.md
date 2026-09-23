---
name: atd-post-task-sync
description: Use when documentalist is called after coding-leader (or any other agent) closes a coding task, to verify the atoms touched by that work still describe what the code does and advance their status (ATD trigger B, ongoing papertrail sync).
---

# ATD Post-Task Papertrail Sync

Verify the atoms touched by a just-closed coding task still describe what
the code does, complete missing links, and advance status where the
evidence supports it.

1. **Scope the change.** Use `git diff`/`git log` (via bash) or whatever
   file list the handoff gives you to know what code actually moved.
2. **Bidirectional coverage check.** `atd check` in its default diff mode is
   git-diff driven and checks code changes and atom changes *in both
   directions* — this is the primary tool for this workflow. Add
   `--semantic` for an LLM compliance verdict per `@spec-link` (slower, use
   it before promoting an atom to STABLE, not on every routine sync).
3. **For every atom the diff touches:** `atd trace <atom_id> --summary`
   for narrative context (what governs this code and why), then read the
   atom file directly (path comes from the trace output) to compare its
   `## THE RULE / LOGIC` and `## EXPECTATION` against what the diff actually
   does.
4. **Classify each touched atom:**
   - **Aligned** — code still satisfies INTENT/EXPECTATION. If the atom was
     DRAFT/REVIEW and implementation is now solid, consider advancing status
     (see Lifecycle Discipline in the core agent instructions).
   - **Missing link** — code clearly implements an atom but carries no
     `@spec-link`/`@test-link`. Confirm via `atd map --file <path> --atom
     <id>`, then add the tag with `atd update --spec-link <id> <file>`.
   - **No atom exists at all** — new code with no plausible parent. If the
     leader ran the atd-architecture-capture skill during planning, this
     should be the exception (an emergent decision made mid-implementation,
     not a planned one), not the default path — most ARCHITECTURE atoms
     should already exist by the time code lands. Either way, do not invent
     one silently: run `atd map --file <path> --new` to get a proposed atom
     skeleton and hand it back for confirmation (the "No Parent, No Code"
     rule applies to you too — you don't get to originate BUSINESS/
     ARCHITECTURE intent on your own authority).
   - **Drift** — a link exists, but the atom's LOGIC/EXPECTATION and the
     code's actual behavior no longer agree. **Stop. Do not edit either
     side.** Report the exact atom (id, path, section) versus the exact code
     (file, line, what it does instead) and let coding-leader/human decide
     which side is wrong.
5. **Close the loop.** After any atom edits: `atd weave`, `atd lint`,
   `atd audit` — scope it to just the atoms this task touched with
   `atd audit --atom <atom_path>` (repeat per atom) rather than defaulting
   to a full-directory sweep, since a routine sync only needs bloat/collision
   evidence for what changed — and a final `atd check` on the touched
   files/atoms.
6. **Report** status changes, links added, and — most importantly — every
   drift you flagged and did not resolve yourself.
