---
name: dependency-gating-protocol
description: Use when coding-leader or coordination-leader is planning or closing a change that adds, upgrades, removes or replaces a dependency — a package in any manifest or lockfile, a runtime, server or engine version, or a Docker base image — in any project under ~/work, to know when to call security-advisor for a dependency check, what to give it, and how to act on its verdict. Applies to every project, with or without a `.tech` file; independent of declared intent and the data register.
---

# Dependency Gating Protocol (for leaders)

This is the leader's side of the protocol. `security-advisor` runs the
checks with its own skills and the `cve-watch` command. Your job is knowing
when a task changes dependencies, calling the advisor at both ends, and
acting on its verdict. You never edit `.tech` or `SECURITY_TODO.md`
yourself. The formats are in
`~/.local/share/dev_team/references/dependency-security.md`.

## Does the task change dependencies?

It does when the plan would:

- add, remove, upgrade or downgrade a package in a manifest (`package.json`,
  `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml`,
  `composer.json`, `pubspec.yaml`, `build.gradle*`…), or regenerate a
  lockfile (`npm update`, `uv lock --upgrade`, `cargo update`…);
- replace one library with another;
- change a runtime, server or engine version: `engines`, `.nvmrc`,
  `.tool-versions`, the `go` directive, a Docker base image tag, an image in
  a compose file, a CI runtime matrix;
- add a new platform: a database, a cache, a queue, a web server.

A change that only touches application code, tests or docs does not. When
unsure, ask for a quick check: it costs one command.

The gate applies to every project. A project without `.tech` still gets the
check; the advisor writes its `.tech` on the way.

## When to call security-advisor

1. **Once the plan names the dependency, before you finalize it**
   (preflight). Give it the project, each package or platform with the
   version you intend (or "latest"), and why it is needed. On a single
   package bump, ask for a quick preflight. Under declared intent or a data
   register, run those gates as usual; this one is independent of them.
2. **After the change lands and the lockfile is regenerated, before you
   report to the user** (post-change). Give it the project, the base commit
   or the changed manifest and lockfile paths, and the preflight's
   recommendations you followed or not.

If you implement through `coding-executor`, the brief carries the vetted
versions, and the executor runs `cve-watch check` itself after installing
(its own instructions say so); you still call the advisor's post-change
check before closing.

## Under a build plan

A chunk that changes dependencies says so in its brief. The chunk owner
installs the versions the chunk names, runs `cve-watch check <dir>` and
reports the result to the driver; it calls neither check itself. The wave
driver calls one post-change check per wave over the wave's dependency
changes, so `.tech` is updated once per wave. A chunk that has to add a
dependency its brief doesn't name gets a preflight from the driver before
that part is built.

## Acting on the verdict

- **CLEAR**: carry the vetted versions into the work and the handoff.
- **FIX-AVAILABLE**: use the version and upgrade path it names (direct bump,
  parent upgrade, override or resolution for a transitive package). If you
  can't (out of scope, breaks something), tell the user which and why;
  never ship a known finding at or above the threshold silently.
- **NEEDS-HUMAN-DECISION**: put the question to the user before going
  further on that dependency: accept the risk (the advisor then records an
  `[[ignore]]` with their approval), choose a breaking upgrade, or drop or
  replace the dependency. Relay the answer to the advisor, never edit
  `.tech` yourself.

## Fixing SECURITY_TODO.md items

When the user asks you to work through a project's `SECURITY_TODO.md`, ask
the advisor for a triage first if the items have no `Triage` line, then
build the upgrades it groups, then call the post-change check. Don't tick
items yourself: the next sweep ticks what the scan no longer finds, and
`cve-watch check` shows it immediately.

## Close-out

Before reporting to the user, the post-change check has run. Your report
mentions the findings introduced or fixed by the change, any you left in
place and why, and the host commands the advisor listed for platform
upgrades, so the user sees the dependency-security outcome next to the
code.
