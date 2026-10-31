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
