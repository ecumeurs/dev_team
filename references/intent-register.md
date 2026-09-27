# The intent register — format

The intent register is the ATD-less record of declared intent: what the
product must do, why, and which architectural decisions serve it. The
leaders' gates check every change against it. `intent-keeper` is its only
writer. Everyone else reads it: the leaders, `codebase-explorer`,
`ux-writer`, `ux-critic`, and humans. A repository uses the register when
`intent/README.md` exists at the project root. If `.atd` exists too, ATD
wins and the register is not gated against (see skill
`intent-gating-protocol`).

The spec tree (`specs/`) is where intent is worked out and published per
milestone. The register is the standing record the gates check against. It
holds only settled or explicitly drafted intent, never deliberation. Open
questions, options under debate and superseded decisions stay in the spec
and UI/UX trees' own registers.

## Layout

```
intent/
  README.md        marker and index: Vision, Contract, file list
  business.md      business entries: what the product must do, and why
  architecture.md  architecture entries: decisions that serve business entries
```

When a file gets hard to scan (around 40 entries), split it by area into a
folder, `business/<area>.md` or `architecture/<area>.md`, and give the
folder a `README.md` that lists its files, each with a one-line purpose.
Names follow `references/doc-tree-conventions.md`: lowercase kebab-case,
named by content. The register is standing: it describes the product, not
a milestone, so it is never archived. Entries that stop applying are
retired in place.

## `intent/README.md`

```markdown
# Intent register

Declared intent for <product>. Maintained by `intent-keeper`; format in
`~/.local/share/dev_team/references/intent-register.md`.

## Vision
<One or two sentences: what the product is for, and for whom.>

In scope:
- <capability or concern>

Out of scope:
- <capability or concern the product deliberately does not take on>

## Contract
Guarantees that change only with the user's explicit agreement.
- <guarantee, in one sentence> (`<entry-id>`)

## Files
- `business.md` — business entries
- `architecture.md` — architecture entries
```

**Vision** is scope. A change that would take the product outside it needs
the user's agreement and a Vision update in the same change. **Contract** is
the guaranteed surface. Each line restates a guarantee in one sentence and
names the `confirmed` entry that holds it in full. Removing or weakening a
Contract line needs the user's agreement. Only `confirmed` entries can back
a Contract line. On a young project, Contract is short or empty, and that is
correct. Vision and Contract are separate axes: a change can trip either
one, so check both.

## Entries

Each entry is an H2 heading carrying its ID, followed by `Field: value`
lines. A field may continue on indented lines below it.

### Business entry (`business.md`)

```markdown
## guest-checkout
Status: confirmed
Intent: A visitor can buy without creating an account.
Rule: Checkout accepts an email address and a payment method with no
  account. The order is attached to that email address. An account is
  offered after payment, never required before it.
Expectation: A visitor with no session completes a purchase and receives
  the confirmation at the email address given.
Source: master spec v2
```

### Architecture entry (`architecture.md`)

```markdown
## payment-provider-adapter
Status: draft
Serves: guest-checkout, saved-cards
Decision: Payments go through one `PaymentProvider` interface with one
  adapter per provider. Checkout code never imports a provider SDK.
Why: Two providers are planned. A direct SDK call would tie checkout to one
  of them. A generic gateway service was rejected as too heavy for two.
Expectation: No module outside `payments/adapters/` imports a provider SDK.
Source: planning decision, task "add second payment provider"
```

### Fields

| Field | Where | Meaning |
|---|---|---|
| `Status` | both | `draft`, `confirmed` or `retired` (below). |
| `Intent` | business | One sentence, one rule. An "and" or "also" joining two behaviors means two entries. |
| `Rule` | business | The rule in full: what state changes, under which conditions, and what is refused. |
| `Serves` | architecture | The business entry IDs this decision exists for. At least one is required. |
| `Decision` | architecture | What was decided: the API, entity, module, service, UI flow or specification, and its shape. It never describes how the code is written. |
| `Why` | architecture | The reasoning, including the alternatives rejected. |
| `Expectation` | both | Observable behavior, or a checkable property, that shows the entry holds. This is what the post-task sync compares code against. |
| `Source` | both | Provenance: `master spec vN`, `cold start from code`, `preflight, task "<task>"`, `planning decision, task "<task>"`, `user`. Provenance only: the entry must mean the same without it. |
| `Drift` | both, optional | Present only while an unresolved drift is open (see Drift). |
| `Retired` | both, when retired | One line: why, and the replacing entry's ID if there is one. |

### IDs

- Lowercase kebab-case, short and descriptive: `guest-checkout`, not
  `checkout-1` and not a copied heading.
- Unique across the whole register, business and architecture together.
- Never reused and never renamed. A retired ID stays in its file. Renaming
  would orphan every `@intent` tag that points at it.
- Slugs never clash with the spec and UI/UX trees' numbered IDs (`D12`,
  `O4`, `Q7`), so they need no tree qualifier anywhere.

### Status

- **`draft`**: extracted from code, ingested from a master spec, inferred at
  preflight, or captured at planning. Nobody has confirmed it yet. The gates
  still check against it, but it can change without sign-off.
- **`confirmed`**: a human confirmed it. Changing its meaning (`Intent`,
  `Rule`, `Decision`, `Expectation`, `Serves`) needs the user's explicit
  agreement. `intent-keeper` never sets `confirmed` on its own initiative.
- **`retired`**: no longer applies. The entry stays, with a `Retired:` line,
  so the ID is never reused. Code must not carry a tag for it.

## Self-sufficiency

An entry states its rule in its own words. It never points outward as if the
reference completed the meaning: no "see spec §4", no "per D12", no issue
links. The register has to stand on its own after the spec tree is archived,
stale or gone. If the spec's wording is worth keeping, quote it inline.
Links between entries (`Serves`, the Contract's entry IDs) are the
register's own structure and are fine.

## Code links: `@intent`

A comment tag directly above the function, class, route handler, component
or test that implements or tests an entry:

```python
# @intent guest-checkout
def create_guest_order(email, payment): ...
```

```ts
// @intent payment-provider-adapter, guest-checkout
export interface PaymentProvider { ... }
```

- Use the host language's comment syntax. Several IDs are comma-separated.
- Place it on the specific symbol, not at the top of the file, unless the
  entry really governs the whole file.
- Tests use the same tag, which makes coverage findable:
  `git grep -n '@intent guest-checkout'`.
- Business and architecture entries are both taggable. Code usually
  implements an architecture entry. Tag the business entry directly when no
  architecture entry sits between them.
- The implementer places tags while writing the code; the leader's handoff
  carries the IDs. The post-task sync adds a missing tag (the comment line
  only, never touching logic) and reports tags that point at unknown or
  retired IDs.

## Drift

Drift means an entry and the code both claim to be right and disagree. It
is recorded, not resolved. `intent-keeper` adds one line to the entry and
leaves the rest of the entry, and the code, as they are:

```markdown
Drift: `src/checkout/guest.py:42` requires an account before payment; this
  entry says an account is never required before payment. Reported after
  task "checkout redesign".
```

Deciding which side is right belongs to a human or a leader. The `Drift:`
line comes off when the entry or the code is changed to agree, and the
change that resolves it removes the line. `git grep -n '^Drift:' intent/`
lists every open drift.

## Consistency checks

`intent-keeper` runs these after every write. `codebase-explorer` and the
leaders can run them read-only:

- Every entry has the fields its kind requires, and a valid `Status`.
- IDs are unique across the register.
- Every `Serves` ID exists and is not `retired`.
- Every Contract line names an existing `confirmed` entry.
- Every `@intent` tag in the code (`git grep -n '@intent'`) names an
  existing entry that is not `retired`.
- No entry cites a spec section, register ID or outside document as its
  meaning.
