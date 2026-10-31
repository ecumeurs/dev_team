---
name: dependency-check
description: Use when security-advisor is called by a leader (or the wave driver) about a dependency change in a project under ~/work — before the plan is finalized, to vet candidate package or platform versions, or after the change lands, to check the resolved versions and update `.tech` (trigger B, dependency check: preflight or post-change).
---

# Dependency check

Read `~/.local/share/dev_team/references/dependency-security.md` ("When is a
vulnerability fixed?", `.tech`, Verdicts) before giving a verdict.

## Preflight: before anything is installed

You write nothing in this mode.

1. **List the candidates** from the leader's plan: per package its
   ecosystem, name and intended version (or "latest"); per platform its
   CPE and version. For "latest", find the current release from the
   registry (`npm view <pkg> version`, `pip index versions <pkg>`,
   `go list -m -versions <module>`, the crates.io or Packagist page) without
   installing anything.
2. **Vet each one**: `cve-watch query <ecosystem> <package> <version>`; for a
   platform `cve-watch latest <cpe> --version <v>`, and the vendor's
   security page when NVD shows nothing recent (it lags).
3. **When a candidate is affected**, find the nearest version that is
   outside every affected range at or above the threshold (`query` it too),
   and say whether it is a breaking change for this project (major bump,
   changelog breaking notes).
4. **Look at what comes with it** when the package is new to the project: a
   quick `cve-watch latest <ecosystem/package> --limit 5` shows how often it
   gets advisories and how fast fixes land; a package abandoned with open
   advisories is worth a word in the report. For a package that pulls a
   large tree, say that the post-change check is where its transitive
   findings will show.
5. **Verdict**: `CLEAR`, `FIX-AVAILABLE` (the version to use instead), or
   `NEEDS-HUMAN-DECISION` (no fixed version, only a breaking fix, or the
   dependency is only usable by accepting a risk), per candidate and
   overall.

## Post-change: after the lockfile moved

1. **Check the resolved tree**: `cve-watch check <dir> --json`. Compare with
   the project's open `SECURITY_TODO.md` items and, when the leader gave a
   base commit, with the base's lockfile (`git show <base>:<lockfile>`):
   which packages changed version on each side. Sort findings into introduced by this change, fixed by it, and
   pre-existing.
2. **Transitive findings**: for one that comes through a parent, name the
   parent version that pulls a fixed copy, or the override mechanism
   (`overrides` in npm, `resolutions` in yarn, `[tool.uv] override-dependencies`,
   a `replace` in `go.mod`, `[patch]` in Cargo) as the leader's options.
3. **Update `.tech`** when the change touched something it records: a
   platform version, a new platform, a new lockfile or manifest, a
   direct technology in `[stack]`, a scan path. Bump `updated`. If the
   project has no `.tech`, write one now following skill
   `tech-cold-start`, section 2, for this project only.
4. **Verify**: `cve-watch lint <dir>` clean, `cve-watch check <dir>` run, its
   exit code in the report.
5. **Verdict** on the state after the change: `CLEAR` when nothing it
   introduced is at or above the threshold, `FIX-AVAILABLE` when something
   is and a fix exists, `NEEDS-HUMAN-DECISION` otherwise. Pre-existing
   findings are reported, not blocking, unless the change was meant to fix
   them.

Never tick `SECURITY_TODO.md` items: say which ones the next sweep will
tick.

## Report

The standard handback with mode `preflight` or `post-change`. Name each
version you vetted and the exact command that vetted it.
