# Dependency security: `.tech`, `SECURITY_TODO.md` and `cve-watch`

The format reference for `security-advisor` and its skills. It is
authoritative over any summary in an agent file or a skill.

The guardrail answers one question for every project under `~/work`: does a
known vulnerability affect what this project runs? Three pieces answer it:

| Piece | Where | Written by | Read by |
|---|---|---|---|
| `.tech` | project root | `security-advisor` | `cve-watch`, people, agents |
| `SECURITY_TODO.md` | project root | `cve-watch` (items), `security-advisor` (triage notes) | people, leaders |
| `cve-watch` | `~/.local/bin/cve-watch` → `dev_team/scripts/cve-watch.py` | the user, the advisor, the daily timer | |

## Sources, and what they can and cannot tell

- **Packages: OSV.dev, through osv-scanner.** osv-scanner reads every
  lockfile and manifest it finds (npm, PyPI with `uv.lock`, `poetry.lock` or
  `requirements.txt`, Go, crates.io, Packagist, Pub, Maven…) and asks OSV
  which advisories affect each exact version. OSV gathers GitHub Security
  Advisories (GHSA), the Go, Rust (RUSTSEC) and Python (PYSEC) databases,
  malicious-package reports (MAL) and CVEs. Matching is by package and
  version range, so it is precise. A manifest without a lockfile is resolved
  through deps.dev, which is an approximation of what is actually installed.
- **Platform technologies: NVD, by CPE.** Runtimes, servers and engines that
  no lockfile pins (Node.js, PHP, PostgreSQL, Godot, nginx, a Docker base
  image's main component) are declared in `.tech` with a CPE and looked up on
  NVD. Two limits to keep in mind: NVD analyses CVEs late, and a CVE it has
  not analysed yet has no product configuration, so it matches nothing; and
  CPE matching is coarse. `cve-watch` keeps only CVEs whose configuration
  marks the product itself vulnerable, not those that merely run on it. For a
  platform that matters, check its vendor's security page too.
- **Severity.** The CVSS score osv-scanner reports; failing that, the
  database's own rating (GHSA `LOW`/`MODERATE`/`HIGH`/`CRITICAL`); failing
  that, the CVSS 3 vector of a GHSA or CVE alias. MAL (malicious package) is
  always `critical`. RUSTSEC informational advisories (unmaintained,
  unsound) are `low`. An advisory with no severity anywhere is `unknown`,
  which counts as meeting the threshold.
- **Reachability.** For Go, osv-scanner runs call analysis. A finding whose
  vulnerable symbols are never called is marked *not reachable per call
  analysis*. It still counts, but it is a strong argument at triage.

## When is a vulnerability fixed?

An advisory describes affected version ranges. Each range ends either at
the first **fixed** version (OSV `fixed`, NVD `versionEndExcluding`) or at
the **last affected** version (OSV `last_affected`, NVD
`versionEndIncluding`), and a project may sit on one of several branches
(22.x, 24.x). `cve-watch` shows `fix X` (the nearest fixed version above
the one installed), `fixed after X` (the next release after X on that
branch), or `no fixed version known`, when the advisory has an open range.

A project is fixed when the version it actually resolves to falls outside
every affected range. Upgrading the manifest is not enough: the lockfile has
to move, and a transitive dependency may need an override or a parent
upgrade. The proof is a scan: `cve-watch check <dir>` no longer reports it,
and the next sweep ticks the `SECURITY_TODO.md` item (`· gone <date>`).
Advisories also get corrected after publication (a range widened, a fix
withdrawn); a ticked item that reappears is reopened (`· back <date>`).

Distribution packages are a separate case: Debian backports security fixes
without changing the upstream version, so an NVD match on a distro-packaged
runtime can be a false positive. The Debian security tracker settles it.

## `.tech`

TOML, at the project root. It records what the project is built on and
what the lockfiles cannot say. It never lists package dependencies: the
lockfiles are the truth for those, and a copy would be wrong after the next
install.

```toml
# Technologies this project depends on. Kept by security-advisor (dev_team),
# read by cve-watch. Package dependencies come from the lockfiles; list here
# only what they don't cover.
schema = 1
updated = 2026-10-26

[stack]                        # overview for people and agents, free keys
languages = ["TypeScript"]
frameworks = ["Vue 3.5", "Express 5"]
runtime = ["Node.js 22"]
data = ["PostgreSQL 17"]
tooling = ["Vite 7", "Vitest 4"]
lockfiles = ["package-lock.json", "back/package-lock.json"]

[scan]                         # optional; default: the whole project
paths = ["."]                  # directories osv-scanner walks, recursively
exclude = ["tests/fixtures"]   # directory names or g:/r: patterns (--x-exclude)

[[platform]]                   # one per runtime, server or engine
name = "PostgreSQL"
version = "17.2"               # the version actually run; exact when known
cpe = "cpe:2.3:a:postgresql:postgresql"
source = "docker-compose.yml"  # where that version is pinned, or "host"
exposure = "internal"          # optional: "exposed" (default) or "internal"

[[platform]]
name = "Docker Engine"
version = "29.0.1"
cpe = "cpe:2.3:a:docker:engine"
source = "host: docker version"
host = true                    # optional: runs on the host itself; always exposed, findings flagged

[exposure]                     # optional: lockfiles and SBOMs whose findings are internal
internal = ["services/worker/requirements.txt", "images/exporter/sbom/"]

[[ignore]]                     # an accepted risk: a human approved it
id = "GHSA-xxxx-xxxx-xxxx"     # the advisory ID or any alias (CVE-…)
package = "npm/esbuild"        # optional: only for this ECOSYSTEM/package
reason = "dev server only, never exposed"
approved_by = "bastien"
until = 2027-01-31             # review date; after it the finding counts again
```

Rules:

- `schema` and `updated` are required. Bump `updated` on every edit.
- `[stack]` is free-form: lists of short `"Name major.minor"` strings, the
  direct technologies a newcomer must know, never the transitive tree.
  `lockfiles` lists the lockfiles and lockfile-less manifests that matter,
  relative to the root, so a reader knows what the scan covers.
- `[scan]` exists only to narrow the scan: exclude fixtures, vendored
  examples, test stubs and unreadable data directories (a Docker volume
  owned by another user makes osv-scanner fail the whole project).
  Excluding a real dependency set to make findings disappear is not
  allowed; that is what `[[ignore]]` with a human's approval is for.
  `packages = false` turns the package scan off, for a `.tech` with no
  lockfile of its own (the host's, below).
- `[[platform]]`: `name` and `version` are required. `cpe` is the
  five-part product prefix, found with `cve-watch cpe <keyword>`. Without it
  the platform is documented but not checked, and lint warns. Record the
  version that is actually run (the Docker tag, `.nvmrc`, `engines`, the host
  package), and `source` says where it comes from. A floating tag
  (`node:22`, `postgres:latest`) is recorded as its major with a note in
  `source`, and the finding list for it is approximate.
- `version_cmd` (a list, no shell) and `version_pattern` (a regex whose
  group 1 is the version, default the first dotted number) read a
  platform's version at scan time, for a tool that updates itself. `version`
  stays required as the fallback, and a failed command is reported. Only the
  host `.tech` runs it: a repository's `.tech` is that repository's to write,
  so there it is ignored and lint warns.
- `[[ignore]]`: `id`, `reason`, `approved_by` and `until` are required. The
  advisor never writes one without a human's explicit approval, relayed by
  whoever invoked it. An expired entry stops applying; lint warns.
- **The exposure class.** Every finding is `exposed` unless `.tech` says
  otherwise, and an exposed finding gets the full treatment described below.
  An `internal` finding is still found, listed and reported, but it writes no
  `SECURITY_TODO.md` item, it does not count toward `check`'s exit code, and
  it needs no per-CVE `[[ignore]]`: one human ruling covers the whole class.
  Use it for what an attacker can only reach from inside something already
  trusted (a throwaway environment's internal containers that publish no
  port and that no web route reaches), never because a finding is
  inconvenient. Classing something internal is a risk decision, like an
  `[[ignore]]`: the advisor writes it only from a human's ruling, and
  `.tech`'s header comment cites the ruling and says what is in each class.
  - `exposure` on a `[[platform]]`: `"exposed"` (the default when absent) or
    `"internal"`; anything else is a lint error. An entry that spans
    something exposed (a package installed in an exposed image as well) is
    exposed as a whole.
  - `[exposure].internal` classes package findings, by the lockfile or SBOM
    they come from: a list of paths relative to the root, each an exact
    file, a directory (every lockfile below it) or a glob (`*`, `?`, `[…]`;
    `*` also matches `/`). A finding is internal only when every lockfile it
    was found in matches; one exposed source makes it exposed. An entry must
    stay inside the project (lint error); a literal path that doesn't exist
    gets a lint warning.
  - `host = true` on a `[[platform]]` marks what runs on the host itself:
    the kernel, the container engine (Docker Engine, containerd, runc), a
    tool installed on the host. Its findings are always exposed (`host =
    true` with `exposure = "internal"` is a lint error) and flagged *reaches
    the host* in `check`, the sweep's report and the item. This is the only
    host signal `cve-watch` has: it never reads a CVE's text. Whether a
    finding on internal content reaches the host anyway (a privileged
    container, a mounted Docker socket, a host path, a kernel-facing
    feature) is judged at triage, by hand.

`cve-watch lint [dir…]` checks all of this, and the skills run it after every
edit.

**The host `.tech`**, `~/work/.tech`, records what is installed outside any
project: Claude Code (the CLI and the editor extension). It has
`packages = false`, platforms only, and is the one `.tech` that may use
`version_cmd`. Its `SECURITY_TODO.md` sits beside it, in `~/work`.

## `SECURITY_TODO.md`

At the project root, created by the first sweep that finds something. One
item per advisory and package:

```markdown
- [ ] **high 8.7** GHSA-m2qf-hxjv-5gpq (CVE-2023-30861) · PyPI `flask` 0.12.2 → fix 2.2.5 · `requirements.txt` · found 2026-10-26 <!-- cve-watch:GHSA-m2qf-hxjv-5gpq:PyPI/flask -->
  Flask vulnerable to possible disclosure of permanent session cookie … https://osv.dev/vulnerability/GHSA-m2qf-hxjv-5gpq
```

- The `<!-- cve-watch:<advisory>:<ecosystem>/<package> -->` marker is the
  item's identity. Never edit or remove it on an open item.
- The sweep appends new items, ticks an item `· gone <date>` when the scan
  no longer finds it, `· accepted risk in .tech <date>` when an `[[ignore]]`
  now covers it, `· internal in .tech <date>` when `.tech` now classes it
  internal, and unticks it `· back <date>` when it returns (or turns
  exposed again). An item on a host platform ends with `· reaches the
  host`. It only
  ticks what the part of the scan that would find it actually checked: a
  failed scan closes nothing.
- Triage notes go on indented lines under the item, starting with
  `Triage (<date>):`. They say what the advisor found (dev-only, not
  reachable, upgrade path, blocked by a parent package) and what it
  proposes. The sweep never touches lines without a marker.
- Ticked items may be deleted by anyone at any time.

## `cve-watch`

| Command | Does | Network |
|---|---|---|
| `cve-watch check [dir] [--package NAME] [--json] [-v]` | Scans one project now (packages and platforms) and prints every finding, `!` at or above the threshold, `[reaches the host]` on a host platform's; internal findings follow under their own heading, `i` at or above the threshold. Exit 0 clean, 1 exposed findings at or above threshold (internal ones never count), 2 the scan failed. `--json` gives each finding its `exposure` and `host`. Writes nothing. Also works in a worktree. | OSV, NVD |
| `cve-watch query <ecosystem> <package> [version]` | Is this version affected, and what fixes it? Without a version, every advisory for the package. Exit 1 if anything at or above threshold affects it. | OSV |
| `cve-watch latest <ecosystem/package or cpe> [--version V] [--limit N]` | The most recent advisories for a package or a technology, newest first, no date bound. With `--version`, only those affecting it. | OSV or NVD |
| `cve-watch cpe <keyword>` | Candidate CPE product prefixes for a technology, for a `[[platform]]` entry. | NVD |
| `cve-watch sweep [--days N] [--all] [--project P] [--dry-run] [--from-run RUN]` | The daily sweep, below. | OSV, NVD |
| `cve-watch projects` | The projects a sweep covers, and why the others are skipped. | none |
| `cve-watch lint [dir…]` | Validates `.tech` files. | none |

Ecosystem names: `npm`, `pypi`, `go`, `cargo` (crates.io), `composer`
(Packagist), `pub`, `maven`, `rubygems`, `nuget`, or OSV's exact spelling.

### The sweep

Run daily at 07:30 by the user timer `cve-watch.timer` (systemd, no agent
involved), or by hand.

1. **Projects**: the host `.tech` at `~/work` itself, if there is one, and
   every top-level directory of `~/work` that is a git repository or has a
   `.tech`. Git worktrees (`.git` is a file) are skipped,
   since their main checkout is scanned, and so are names in the config's
   `exclude`.
2. **Scan**: osv-scanner over the project (narrowed by `[scan]`), and NVD for
   each `[[platform]]` with a CPE. Findings an `[[ignore]]` covers are set
   aside; the rest take their exposure class from `.tech`.
3. **New exposed findings** at or above the threshold (default `medium`) get a
   `SECURITY_TODO.md` item: those published in the last `days` (default 7),
   and those first detected since the previous sweep whatever their date (a
   dependency added without a check, an advisory whose range widened). The
   first sweep of a project only applies the date window, so an old backlog
   doesn't flood the file; `--all` writes the whole backlog. Internal
   findings never get an item and are not recorded as seen, so one whose
   class turns exposed counts as newly detected then.
4. **Report**: `~/.local/state/cve-watch/reports/<date>.md` and `.json`,
   `latest.md` pointing at the newest: new findings across projects,
   resolved ones, every open finding per project (internal ones in their
   own collapsed table, counted apart), problems (failed scans,
   lint, projects without `.tech`), skipped directories. A desktop
   notification announces new findings.

### Configuration, cache and state

- `~/.config/cve-watch/config.toml` (optional): `root` (`~/work`),
  `exclude` (`[]`), `days` (7), `min_severity` (`medium`),
  `retention_days` (30), `report_dir`, `notify` (true), `osv_scanner` (path),
  `scan_timeout` (900 s). `NVD_API_KEY` in the environment raises NVD's rate
  limit.
- `~/.cache/cve-watch/`: each sweep's raw osv-scanner output under
  `runs/<run id>/`, advisory records under `vulns/`, NVD answers under
  `nvd/` (reused for a day). Everything older than `retention_days` is
  pruned. `sweep --from-run <run id> --dry-run` replays a recorded run
  offline, which is how matching and TODO changes are tested.
- `~/.local/state/cve-watch/state.json`: per project, every finding key and
  the date it was first seen. This is what "first detected since the
  previous sweep" compares against.

## Verdicts

The advisor's dependency check ends in one of the three below. They weigh
exposed findings only (host-flagged ones included): an internal finding is
listed in the report, labelled internal, and never needs an acceptance.

- `CLEAR`: nothing at or above the threshold affects the versions checked.
- `FIX-AVAILABLE`: something does, and a version that fixes it exists; the
  verdict names it per package, with the upgrade path (direct bump, parent
  upgrade, override/resolution).
- `NEEDS-HUMAN-DECISION`: something does and either no fix exists, the fix
  is a breaking major upgrade, or the only way forward is accepting the
  risk (an `[[ignore]]`). The leader asks the user before going further on
  that dependency.
