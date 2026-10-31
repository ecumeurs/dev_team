# TODO

- [ ] `data-steward` agent: drafted and wired, to review and try.
  - done: agent (Claude and OpenCode), `references/data-register.md`, `references/data-security-baseline.md`, skills `data-cold-start`, `data-preflight`, `data-post-task-sync`, `data-access-model-check`, `data-review`, leaders' skill `data-gating-protocol`; bound into coding-leader, coordination-leader, spec-writer, codebase-explorer, documentalist; README section
  - review the draft: verdict scale (CLEAR / MEASURES-PROPOSED / NEEDS-HUMAN-DECISION), preflight writing nothing, default classes and measures
  - checker script for the register (the format's consistency checks, run at the end of every skill), shipped inside a skill folder
  - maybe split `references/data-register.md` per file, so each skill reads only the formats it writes
  - try it: cold start on a real repo with personal data
- [ ] Build plans (wave model): written for both ports and the skills (`references/build-plan-model.md`, skills `build-plan-authoring` and `wave-execution`, coding-leader chunk mode, documentalist wave mode, data-steward once per version).
  - migrate infinite_flow's v3 plans onto the model, when the owner asks: one shared workflow instead of four §3 copies, a status line per chunk, a wave log for the wave records, waves of v3.1–v3.3 re-formed (v3.1's chunk 16 back to wave 5, v3.2's waves 5, 10 and 11, v3.3's wave 6)
  - token levers done in the skills (uncommitted): the chunk brief embeds the chunk text so leaders don't search the plan; a ~200k-token / ~150-call hand-over rule for chunk owners; "Between waves: start fresh" in `wave-execution`. Measure them on v3.1's first wave against the v3 baseline (`scripts/chunk-report.py`: median $17.7 per chunk, $1.00 per 100 code+test lines, leader peak context 570k, ~2,000 plan greps)
  - migration prepared on infinite_flow branch `plan-migration` (worktree `../infinite_flow-plan-migration`): v3.1 first, then v3.2 and v3.3; merge only after v3.0 is finished
  - `scripts/token-report.py`, `scripts/chunk-report.py`: written, uncommitted; to do: HTML graphs, a survival measure
  - decisions logs: short entry form + archive with every release written into `references/doc-tree-conventions.md`, `milestone-archive`, `spec-writer`, `ux-writer` (uncommitted); infinite_flow's existing long entries are left as they are
  - open owner decisions: a test-volume ceiling in chunk mode; Sonnet for executors
  - try it on the next wave and review the chunk brief
- [ ] `doc-ids` (register numbering): written and wired, to try on a real wave.
  - done: `scripts/doc-ids.py` (`next`, `lint`, `compare`, `renumber`), linked by hookup; `doc-tree-conventions.md` "Numbering" (the collision exception to "never renumber"); spec-writer and ux-writer (both ports), `milestone-archive` (no next ID in headers, lint in its check), `wave-execution` (compare before the wave merges)
  - tested on infinite_flow: `compare 68a04c4^1 88caa03` finds the D339–D341 collision and the O177 clash; renumber and the duplicate flow on a scratch clone
  - infinite_flow's lint warnings to settle by its writers: stale "continues from" lines in both decisions logs; spec D400–D414 cited bare in `ui_ux/`; the wave log's "Next free IDs" lines can go
  - maybe: a pre-commit hook running `doc-ids lint` in projects with a spec tree
- [ ] `security-advisor` agent and `cve-watch`: drafted and wired, to review and try.
  - done: agent (Claude and OpenCode), `references/dependency-security.md`, skills `tech-cold-start`, `dependency-check`, `vuln-triage`, leaders' skill `dependency-gating-protocol`; bound into coding-leader, coordination-leader, coding-executor, reviewer, wave-execution; `scripts/cve-watch.py`, `systemd/cve-watch.{service,timer}` installed by setup; osv-scanner 2.7.0 in `~/.local/bin`; README section
  - run the cold start over `~/work` (`.tech` everywhere); `cours` needs `[scan].exclude` for `devops/exo_compose/db_peppermint_data` (unreadable Docker volume fails its scan), `llmward` probably for `security/skill-audit/scripts/ecosystem-stubs` (fixture lockfiles)
  - decide whether the non-git directories (`postgresql`, `upsilon`, `vue_beat`, `pgdays`, `db_audit_gm-wt`, `pg_anon_studio_atd_trial`) are projects: a `.tech` makes the sweep cover them
  - first triage pass: 610 open findings at or above medium on 2026-10-26, 130 published in the last 7 days (pillow 12.2.0, brotli, certifi, aiohttp…)
  - host `.tech` at `~/work` (Claude Code CLI and VS Code extension, versions read by `version_cmd`); cve-watch: root `.tech` discovered, `[scan] packages = false`, `version_cmd` host-only
  - maybe: an `NVD_API_KEY` (raises NVD's rate limit), a spec-writer **Dependencies** line on build-plan chunks
- [ ] Host runtimes, postponed on 2026-10-26: Node.js 22.23.3 (nodesource) → 22.23.4 is available (`sudo apt-get install --only-upgrade nodejs`); PHP is not installed on the host, so check the projects that pin it (grav's `composer.json`, Docker images) instead

