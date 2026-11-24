---
name: vuln-triage
description: Use when security-advisor is asked to triage vulnerability findings — new `SECURITY_TODO.md` items written by the daily cve-watch sweep, a whole project's list, or the latest sweep report across ~/work (trigger C, triage) — to sort each item into fix now, batch, dev-only or not reachable, watch, or propose accepting the risk, and hand back the work grouped as a leader would build it.
---

# Vulnerability triage

Read `~/.local/share/dev_team/references/dependency-security.md`
(`SECURITY_TODO.md`, "When is a vulnerability fixed?") first. You write
triage lines and nothing else; the items' state belongs to the sweep.

## 1. Scope

- **The latest sweep**: `~/.local/state/cve-watch/reports/latest.md`, section
  "New findings", and its `.json` twin for fields. Triage per project.
- **One project**: every open item (`- [ ]`) of its `SECURITY_TODO.md` with
  no `Triage` line, or all of them if asked.
- Refresh first: `cve-watch check <dir> --json`. An item the check no longer
  reports is already fixed; say so and skip it (the next sweep ticks it).
  An item whose finding the check now gives `"exposure": "internal"` is out
  of scope too: the next sweep ticks it `internal in .tech`.
- **Internal findings** (`.tech`'s exposure class; the reference, `.tech`)
  get no item and no per-CVE triage: the ruling the class cites covers
  them. Don't propose an `[[ignore]]` for one. Look at them only for two
  things: one that reaches the host (below), and a class that no longer
  holds (the component now publishes a port, a web route reaches it): say
  which entry to move to `exposed`, as a `.tech` change for a human to
  confirm.

## 2. Classify each item

Look at the package's place in the project, then the advisory:

- **Role**: shipped at runtime, build-time only, dev or test only, or a
  fixture (a lockfile under `tests/`, `examples/`, `stubs/`). Read the
  manifest section it comes from (`devDependencies`, `[dependency-groups]`,
  `dev-dependencies`) or `npm ls <pkg>` / `uv tree` / `go mod why` /
  `cargo tree -i` to see which direct dependency pulls it.
- **Exposure**: what the project is (a public web app, an internal service,
  a local CLI, a course exercise) as `.tech`, the README and the project
  instructions say, and where the finding sits within it.
- **Host reach**: a finding flagged *reaches the host* (a `host = true`
  platform) is triaged as exposed and named in the hand-back. `cve-watch` has no
  other host signal: when a finding, exposed or internal, is a container
  escape or otherwise reaches the host through how the component runs (a
  privileged container, a mounted Docker socket or host path, a
  kernel-facing feature), you judge it by hand and say so in the triage
  line, internal findings included.
- **Reachability**: Go's call analysis (`not reachable per call
  analysis`); otherwise whether the vulnerable feature is used, when that
  can be read in a minute from the advisory and a search of the code. Don't
  spend longer: say "not assessed".
- **Fix**: the nearest fixed version on the project's branch, and the
  upgrade path (direct, via parent, override), breaking or not.

Then give one class:

| Class | When |
|---|---|
| `fix-now` | Shipped and exposed, at least high, or any MAL (malicious package): remove or pin away immediately. |
| `batch` | A fix exists and the risk is real but not urgent: group it with the project's next dependency update. |
| `dev-only` | Build, dev, test or fixture only, and no path to production. Still fix when cheap. |
| `not-reachable` | The vulnerable code is not called, with the evidence. |
| `watch` | No fixed version yet: say what to watch (the advisory, the upstream issue). |
| `accept-risk?` | A human should decide to accept it: propose `reason` and an `until` date for an `[[ignore]]`. |

## 3. Write

Under each item, one indented line, never touching the item line or its
marker:

```
  Triage (2026-10-26): batch — runtime dep via `express` 4.21; fix 0.7.1 through express 4.22 (non-breaking).
```

## 4. Hand back

The standard handback with mode `triage`, plus the work grouped as a leader
would build it, per project: one line per upgrade (`package from → to`, path,
items it closes, breaking or not), `fix-now` first. List `accept-risk?`
items under "Pending human decisions". Platform findings (NVD) that need a
host upgrade go under "Platform actions for the user" as the command to
run. Internal findings get one summary line per project (counts, and any
that reaches the host or whose class no longer holds), not a line each. A
large backlog is fine to triage in passes: say what is left.
