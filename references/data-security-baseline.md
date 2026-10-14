# Data security baseline

The starting point `data-steward` uses to propose protection: a default
sensitivity scale, a catalogue of measures with stable IDs, which measures
each class requires, the questions to ask of every flow, and common
separation-of-duties rules. A project adapts it in its own
`data-register/classification.md`; this file is never copied wholesale.

It follows the GDPR's own framing. Article 32 asks for security
"appropriate to the risk", naming pseudonymization and encryption,
lasting confidentiality, integrity, availability and resilience, the
ability to restore data after an incident, and regular testing. Article 25
asks for data protection by design and by default: collect only what a
purpose needs, keep it only as long as needed, and expose it to as few
people as possible.

## Proportionality

A measure is proposed because a specific risk justifies it, never because
it is on a list. Each proposal states:

1. **The risk**: what goes wrong, to whom, and how likely the path is
   (a leaked backup, an over-broad service role, a log shipped to a vendor).
2. **The measure**: by catalogue ID, and what it means in this stack.
3. **The cost**: implementation effort, runtime cost, what it makes harder
   (encrypted fields can't be searched with `LIKE`, masked logs slow
   debugging).
4. **The cheaper alternative**, when one exists. The cheapest measure of
   all is not collecting or not keeping the data: always ask whether a field
   is needed before asking how to protect it.

Over-protecting `internal` data wastes effort and trains people to
ignore the register. Under-protecting `restricted` data is the failure the
register exists to prevent. The class sets the floor; the proposal argues
anything above it.

## Default scale

| Class | Harm if disclosed, altered or lost | Typical content |
|---|---|---|
| `public` | None. It is meant to be published. | Marketing pages, a public catalogue, published docs |
| `internal` | Minor embarrassment or inconvenience; no harm to a person. | Feature flags, non-personal metrics, internal docs |
| `confidential` | Harm to a person or the business: privacy loss, commercial damage. | Customer contact details, order history, staff records, unpublished pricing |
| `restricted` | Serious harm: fraud, identity theft, legal exposure, loss of trust at scale. | Government identifiers, bank details, full payment data, authentication material, anything flagged `special` |

Flags add to a class:

- `personal`: GDPR applies. Adds `erasure-path`, `access-path`,
  `retention-rule`, and a `processing.md` purpose.
- `special`: Article 9 or 10 data. Raises the item to `restricted` at
  minimum, and always opens a pending decision on lawful basis and DPIA.

Secrets (passwords, API keys, signing keys, tokens) are `restricted` items
of kind `secret` with their own rule: they live in a secret store, never in
the repository, the database in clear, or a log. Stored user passwords are
hashed with a slow password hash, never encrypted.

## Measure catalogue

| ID | Measure | Guards against |
|---|---|---|
| `minimize` | Collect and keep only the fields a purpose needs; narrow what each flow carries | Everything below, at no runtime cost |
| `tls` | Encrypted transport on every hop, internal ones included where the network isn't trusted | Interception in transit |
| `enc-at-rest` | Storage-level encryption (managed database, disk, bucket default) | Stolen disks, mis-disposed media. Not a compromised app or role |
| `enc-field` | Application-level encryption of specific fields, key held outside the database | A database dump, a read-only SQL injection, an over-broad DB role |
| `pseudonymize` | Replace identifiers with tokens; keep the mapping apart, under tighter access | Analytics or test use exposing identities |
| `hash-secret` | Slow, salted hashing (argon2, bcrypt, scrypt) for stored passwords | Credential reuse after a leak |
| `secret-store` | Secrets in a dedicated secret manager or the platform's secret mechanism, injected at runtime | Secrets in git history, images, logs |
| `key-rotation` | A documented, tested way to rotate each key and secret | A leaked key staying valid indefinitely |
| `least-privilege` | Each principal gets only the operations and data it needs; separate DB roles per service | Lateral movement, accidental damage |
| `mfa-admin` | Multi-factor authentication for every human with production or admin access | Phished or reused staff credentials |
| `access-log` | Log who read or changed the data, kept where the actor can't alter it | Undetected misuse; no evidence after a breach |
| `export-audit` | Bulk exports and admin queries are logged with a reason, and reviewed | Quiet mass exfiltration by an insider |
| `mask-in-logs` | Sensitive fields redacted or truncated in application logs, traces, error reports and analytics events | Sensitive data spreading to systems with weaker access |
| `no-prod-copies` | Production data never copied to development, staging or a laptop; tests use synthetic or pseudonymized data | Exposure through weaker environments |
| `backup-protected` | Backups encrypted, access-restricted like production, and restores tested | Backups as the soft target; data unrecoverable when needed |
| `retention-rule` | A defined retention period and an automated purge or anonymization at its end, copies included | Data kept forever, growing the blast radius |
| `erasure-path` | A working way to delete one person's data on request, across every store and copy | Unanswerable erasure requests |
| `access-path` | A working way to export one person's data on request | Unanswerable access requests |
| `integrity-check` | Constraints, checksums or audit trails proving data wasn't altered | Silent corruption or tampering of important data |
| `availability` | Replication and a recovery objective matched to the item's importance | Loss of data the business can't run without |

`integrity-check` and `availability` follow the item's **importance**, not
its class: they are proposed for any item whose loss or corruption would
stop the business, whatever its sensitivity.

## Default requirements per class

| Class | Required |
|---|---|
| `public` | `integrity-check` where tampering would mislead users |
| `internal` | `tls`, `enc-at-rest`, `least-privilege` |
| `confidential` | `internal`'s, plus `mask-in-logs`, `no-prod-copies`, `access-log`, `backup-protected`, `mfa-admin` |
| `restricted` | `confidential`'s, plus `enc-field` (or `pseudonymize` where the identity isn't needed), `export-audit`, `key-rotation` |
| flag `personal` | adds `retention-rule`, `erasure-path`, `access-path`, `minimize` |
| kind `secret` | `secret-store`, `key-rotation`, `mask-in-logs`; `hash-secret` for stored user passwords |

## Flow questions

Ask these of every flow that crosses a zone boundary. A "no" or "unknown"
is a gap or a pending decision, not a blocker on its own.

1. Does the flow carry only what the receiver needs? (`minimize`)
2. Is it encrypted in transit, and is the receiver authenticated?
3. Is the credential it uses scoped to this flow only, held in a secret
   store, and rotatable?
4. If the receiver is a third party: is it in `processors.md`, where does
   it store the data, and for how long?
5. Can the receiver send data back, and is that inbound data validated and
   classified like anything else entering the system?
6. Does the flow write copies along the way: logs, retries, dead-letter
   queues, caches? Each copy is an inventory item or is masked.
7. If the flow stops or fails, is data lost or duplicated, and does that
   matter for this item's importance?

## Separation-of-duties patterns

Common rules to propose in `responsibilities.md`, adapted to the project's
principals. Small teams can't always split people; when one person must
hold both sides, the compensating control (logging, review by a second
person after the fact) is stated instead.

| Rule | Why |
|---|---|
| Whoever can access `restricted` data can't alter or delete the log of that access | Access can't be hidden afterwards |
| Whoever writes code that touches `restricted` data isn't the only approver of its merge and deploy | One person can't ship an exfiltration path unreviewed |
| Whoever administers keys doesn't routinely read the data those keys protect | Key custody and data access stay two compromises apart |
| Application services don't hold `administer` on their own data stores | A compromised service can't widen its own access |
| Exports of personal data are requested by one person and approved by another | Mass export needs two people |
| Backup deletion needs a different principal from production deletion | One compromised account can't destroy both copies |
| CI can deploy but not read production data | A compromised pipeline doesn't become a data leak |
| Each service has its own credential; none is shared between services | One leak doesn't expose every flow, and access logs name the real actor |
| Developers have no standing production data access; break-glass is time-boxed and logged | Day-to-day work never touches real data |

## What `data-steward` does not decide

- Lawful basis, whether a DPIA is needed, controller vs processor roles,
  transfer safeguards, retention periods, and data ownership. It suggests
  and records `undecided` until a human decides.
- Whether a security gap is acceptable. It states the risk and the cost of
  closing it; accepting a risk is the user's call, recorded on the entry as
  a `Gap:` line ending in `Accepted by the user: <reason>`.
- How a measure is implemented. It names the measure and what it must
  achieve; the leader plans the implementation.
