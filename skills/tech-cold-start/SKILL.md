---
name: tech-cold-start
description: Use when security-advisor is asked to write a `.tech` file for a project that has none, or for every project under ~/work that lacks one (trigger A, cold start), so that cve-watch checks its platform technologies and people and agents can see what it is built on.
---

# Tech cold start

Read `~/.local/share/dev_team/references/dependency-security.md`, section
`.tech`, before writing. The output is one honest `.tech` per project: what
the project runs on, pinned where the code pins it, `unknown` where it
doesn't. Accepted risks are never inferred: a cold start writes no
`[[ignore]]`.

## 1. Scope

- One project: the directory you were given.
- All projects: `cve-watch projects` lists those a sweep covers; take every
  one without `tech` in its row. Skipped directories (worktrees, non-git
  without `.tech`) stay out unless the user names them. Report the
  non-git ones so the user can decide whether they are projects.
- Never write into a git worktree (`.git` is a file): its main checkout
  holds the `.tech`.

Work project by project and keep each pass small: you read manifests and
configuration, not the source.

## 2. Read what the project runs on

- **Lockfiles and manifests**: `git ls-files` (or `find` outside git,
  skipping `node_modules`, `vendor`, `.venv`, `target`, `dist`) for
  `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`,
  `pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `go.mod`,
  `Cargo.toml`, `Cargo.lock`, `composer.json`, `composer.lock`,
  `pubspec.yaml`, `build.gradle*`, `pom.xml`. These go in
  `[stack].lockfiles`; flag a manifest with no lockfile, since its scan is an
  approximation.
- **Direct technologies** for `[stack]`: the manifests' direct dependencies
  that shape the project (framework, ORM, test runner, bundler, UI kit),
  never the transitive tree. Major.minor from the lockfile.
- **Platforms** for `[[platform]]`, with the version actually run and where
  it comes from:
  - Dockerfiles (`FROM`), compose files (`image:`), devcontainer config;
  - `engines` in `package.json`, `.nvmrc`, `.node-version`,
    `.tool-versions`, `.python-version`, `requires-python`, the `go`
    directive, `rust-toolchain*`, `composer.json` `require.php`, the Flutter
    or Dart SDK constraint, Gradle's Android Gradle Plugin and SDK levels;
  - databases and servers named in configuration (`DATABASE_URL` hosts by
    key name only, compose services, docs that state a version);
  - engines and SDKs the README or the project's instructions name (Godot,
    Unity, an embedded runtime).
  A platform the project only needs as a client library (a PostgreSQL
  driver) is a package, not a platform; the server it talks to is a
  platform when the project ships or pins it (compose, Dockerfile, docs).
  When only "host" applies (a CLI that runs on the machine's Node.js), you
  may record the host's version with `source = "host"`: `node --version`,
  `psql --version`, `php --version`.
- **CPE** for each platform: `cve-watch cpe <keyword>`, then pick the
  product prefix whose name is the technology itself (`nodejs:node.js`,
  `php:php`, `postgresql:postgresql`, `python:python`, `golang:go`,
  `rust-lang:rust`, `nginx:nginx`, `godotengine:godot`). NVD is rate
  limited: one lookup per distinct technology, reused across projects. If
  no CPE fits, leave `cpe` out and say so in the report.
- **Scan narrowing**: if `cve-watch check` fails (unreadable directory) or
  reports findings only from fixtures, examples or test stubs, add
  `[scan].exclude` for those directories, never for real dependency sets.

## 3. Write and verify

- Write `.tech` with the header comment, `schema = 1`, `updated` today,
  `[stack]`, `[scan]` only when needed, one `[[platform]]` per platform.
  Write `version = "unknown"` with a `source` that says what was looked for
  rather than guessing.
- `cve-watch lint <dir>`: no errors. Warnings for a missing `cpe` are
  acceptable when the report says why.
- `cve-watch check <dir>`: the scan succeeds (exit 0 or 1). Record the
  counts; don't triage here, that is trigger C.
- Add the project instructions note if the project has a `CLAUDE.md` or
  `AGENTS.md` (see your agent file).

## 4. Report

The standard handback with mode `cold-start`, plus a table, one row per
project: platforms recorded (with versions or `unknown`), lockfile-less
manifests, `[scan]` exclusions and why, check counts at or above the
threshold. End with the platform versions that look outdated (a runtime
branch past end of life, a base image several minors behind) as
"Platform actions for the user".
