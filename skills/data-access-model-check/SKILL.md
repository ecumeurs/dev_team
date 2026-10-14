---
name: data-access-model-check
description: Use when data-steward, in a repo with a data register (`data-register/README.md`), is handed an access model that spec-writer delivered or revised (`access-model.md` in the spec tree), or the user asks for one to be checked, to cross-check end-user permissions against the data's classification and record the result in `responsibilities.md` (trigger D, access model cross-check).
---

# Access Model Cross-Check

The access model (owned by `spec-writer`) says what each kind of end user
may do in the product. The register says how sensitive each piece of data
is and what that requires. This check finds where the two disagree. You
never edit the access model: findings go to the user and `spec-writer`.

Read the access model in full, the register's `classification.md` and
`inventory.md`, and the *Access model cross-check* section format in
`~/.local/share/dev_team/references/data-register.md`.

1. **Map resources to data.** For each resource in the access model's
   resources and matrix sections, find the inventory items it exposes. A
   resource with no matching item is a finding for the register: data the
   product exposes that nobody inventoried (record it in the report as a
   candidate item, not as an entry).
2. **Find the sensitive cells.** Every matrix cell that is `allow` or a
   condition, for an operation on a resource exposing `confidential` or
   `restricted` data, or that lets an actor `export` or `delete` personal
   data.
3. **Check each one against the class:**
   - is the actor's reach justified by a purpose in `processing.md`?
   - does the condition actually narrow access (`same-org`, ownership), or
     does it allow more than the purpose needs?
   - is a bulk read or export of `restricted` data in the access model's
     audited operations, as `export-audit` requires?
   - does listing reveal more than reading one item would (list views
     leaking fields the item view hides)?
   - is the denial behavior right for the data: does a visible-but-blocked
     denial leak the existence or name of something `restricted`?
4. **Check elevation paths.** Support impersonation, break-glass, API
   tokens and delegation, against the same questions: can any of them
   reach `special` data unlogged, export personal data without a second
   person, or outlive the role that granted them?
5. **Check the erasure and access paths.** Personal items require
   `erasure-path` and `access-path`. Does the access model give some
   actor (the person themselves, or support) an operation that honours an
   erasure or access request?
6. **Record and report.** Rewrite the *Access model cross-check* section of
   `responsibilities.md`: the access model's version or date, each finding
   in one line (actor, operation, resource, the data and its class, the
   problem), and `consistent` for the actors that passed. Run the
   consistency checks. Report with mode `access-model-check`, each finding
   phrased so `spec-writer` can act on it without reading the register.
