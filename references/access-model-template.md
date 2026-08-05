# Access Model — document layout

The layout for the **access model** document: the companion `spec-writer`
delivers alongside the master spec whenever a product has more than one kind
of user. It is the single authoritative answer to "who exists, what may each
of them do, and what happens when they try something they may not."

It exists because three downstream agents are *barred* from inventing this
material and will stall without it: `ux-writer` (needs to know which roles
reach which screens, and what a denial looks like on screen), `coding-leader`
and `coding-executor` (need enforceable rules, not intent), and
`documentalist` (atomizes it into BUSINESS-layer atoms, which requires each
rule to stand on its own).

## Two lives

The document has a draft life and a final life, exactly like the master spec:

- **Draft** (inception phase): lives in the working set alongside the other
  topic docs. Carries a `Status: draft vN` line, may cite open-question IDs
  (`O4`) inline, may leave matrix cells marked `?`, and tags unconfirmed
  entries `(proposed)`. A partial access model is a normal, honest state.
- **Final** (delivered with the master spec): complete matrix with no `?`
  cells, no `(proposed)` tags, and **no internal tracking IDs of any kind**.
  Anything still undecided is restated in plain language under *Known gaps*.
  Same self-sufficiency requirement as the master spec, for the same reason:
  documentalist ingests it and will never see the register those IDs point
  into.

Suggested filename: `access-model.md`, beside the master spec.

---

## Layout

### 1. Purpose and scope

Two or three sentences: which product this governs, and what it deliberately
does not cover (e.g. "covers application-level authorization only;
infrastructure and database-level access are out of scope").

### 2. Actors

Every kind of user, **including the ones that aren't people and the one that
isn't logged in** — those are the two most commonly omitted, and both have
permissions whether or not anyone wrote them down.

For each actor: a stable identifier, a one-line definition, how someone
becomes one, and whether it stacks with other roles or is exclusive.

| Actor | Definition | How acquired | Stacks? |
|---|---|---|---|
| `visitor` | Unauthenticated. Any request with no valid session. | Default state | No — exclusive |
| `member` | Authenticated user belonging to ≥1 organization | Invited and accepted | Yes |
| `project-admin` | Member with elevated rights on a specific project | Granted per-project by `org-owner` | Yes — scoped per project |
| `org-owner` | Full control of one organization and its billing | Creates the org, or transferred | Yes — scoped per org |
| `support` | Internal staff who may act on a customer's behalf | Employment + break-glass grant | Yes — see §8 |
| `api-token` | Non-human caller acting under a user's identity | Issued by a `member` | No — see §8 |

State explicitly whether roles are **global or scoped**. "Admin" almost never
means global admin, and a matrix that doesn't say which is unimplementable.

### 3. Role assignment and lifecycle

The section everyone forgets. Cover:

- Who may grant each role, and who may revoke it.
- Whether a role can be self-assigned or self-revoked.
- What happens to the **last** holder of a role (can the only `org-owner`
  leave? what happens to the org?).
- What happens to **in-flight work** when a role is revoked mid-action —
  open sessions, queued jobs, pending approvals the user authored.
- Whether revocation is immediate or takes effect at next login. These are
  very different systems; pick one.

### 4. Resources and operations

The nouns that have access rules and the verbs that apply, named once so the
matrix has stable axes. Keep the verb set small and reuse it —
`view` / `create` / `edit` / `delete` / `share` covers most products, and
inventing a verb per resource makes the matrix unreadable.

Call out any resource where **listing** differs from **reading a single
item** — they very often do, and a matrix with only `view` hides that.

### 5. Permission matrix

The core. **One table per resource**, rows = operations, columns = actors —
this keeps tables narrow enough to read, where a single combined table wraps
and becomes useless.

Every cell is one of: `allow`, `deny`, or the name of a condition defined in
§6.

**No blank cells, ever.** A blank is indistinguishable from an operation
nobody considered, and that ambiguity is exactly where authorization bugs
live. If it's undecided, mark it `?` in the draft and resolve it before
final.

**Project**

| Operation | `visitor` | `member` | `project-admin` | `org-owner` |
|---|---|---|---|---|
| `list` | deny | `same-org` | `same-org` | `same-org` |
| `view` | `is-public` | `same-org` | `same-org` | `same-org` |
| `create` | deny | `same-org` | `same-org` | allow |
| `edit` | deny | deny | `own-project` | `same-org` |
| `delete` | deny | deny | deny | `same-org` |
| `share` | deny | deny | `own-project` | `same-org` |

### 6. Conditions

Every condition named in the matrix, defined once, precisely enough to
implement. A condition is a predicate over (actor, resource) — if it needs
prose to explain, it's underspecified.

| Condition | Holds when |
|---|---|
| `same-org` | The resource's organization is one the actor belongs to |
| `own-project` | The actor holds `project-admin` **on this specific project**, not merely somewhere |
| `is-public` | The project's visibility field is `public` |

Watch for conditions that quietly depend on each other, and for the
`project-admin`-on-*a*-project vs *this*-project distinction — it is the most
common real-world authorization bug and the matrix cannot express it without
a named condition.

### 7. Denial behavior

What the user actually experiences when a cell evaluates to deny. `ux-writer`
consumes this directly; a spec that stops at "deny" leaves it unable to
design the screen.

The load-bearing distinction is **hidden vs. visible-but-blocked**:

- *Hidden* — the resource is filtered from lists and a direct URL returns
  "not found". The user cannot learn it exists. Costs discoverability;
  required when existence itself is confidential.
- *Visible-but-blocked* — the user sees it and is told they lack access.
  Enables "request access" flows; leaks existence and often the name.

These are different products, not implementation details. Choose per
operation class and say why.

| Operation class | Behavior | Rationale |
|---|---|---|
| Any op on another org's resources | Hidden (404) | Cross-tenant existence is confidential |
| `edit`/`delete` without `own-project` | Visible-but-blocked, with a request-access path | Same-org users benefit from discovering the project |
| Any op by `visitor` on a non-public resource | Redirect to sign-in, then resume | Preserves intent through auth |

Also specify: whether a denial is logged, and whether repeated denials
rate-limit or lock the account.

### 8. Elevation, delegation, and non-human actors

- **Support/impersonation** — may staff act as a user? With whose consent?
  Is it announced to the user, time-boxed, and logged? Which operations stay
  forbidden even while impersonating (usually: billing changes, password
  changes, deleting the audit log itself).
- **Break-glass** — the emergency path that bypasses the matrix, who may
  invoke it, and what it triggers afterward.
- **API tokens / service accounts** — whether a token may be scoped *narrower*
  than its issuing user (it should be), and what happens to live tokens when
  the issuing user's role is revoked or they leave.
- **Delegation** — can a user grant another user a subset of their own
  rights, and can the delegate re-delegate?

### 9. Audited and step-up operations

Which operations must be written to an audit log, and which require
re-authentication or explicit confirmation beyond the normal session.
`ux-writer` needs this — a step-up requirement is an extra screen in a flow
that would otherwise not exist.

### 10. Out of scope

Access questions deliberately not answered here, and where they're answered
instead.

### 11. Known gaps

Final version only. Every unresolved access decision, in plain language, with
its consequence. Never silently drop one by omitting it — an access model
that looks complete but isn't is worse than one that's honestly partial.

Draft versions use an *Open questions* section instead, which may cite IDs.

---

## Completeness check

Run before marking the document final. `ux-critic` and `documentalist` both
rely on these holding:

- Every actor in §2 appears as a column in every §5 table.
- No blank or `?` cells remain in any matrix.
- Every condition named in §5 is defined in §6, and every condition defined
  in §6 is used.
- Every deny (and every condition that can evaluate false) has a behavior
  covered by §7.
- Unauthenticated and non-human actors are both represented.
- Listing and single-item reading are distinguished wherever they differ.
- Role revocation semantics are stated (§3), not merely role granting.
- No `O#`/`D#` or equivalent tracking ID appears anywhere in the document.
