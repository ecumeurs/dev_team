# TODO

- [ ] `data-steward` agent: drafted and wired, to review and try.
  - done: agent (Claude and OpenCode), `references/data-register.md`, `references/data-security-baseline.md`, skills `data-cold-start`, `data-preflight`, `data-post-task-sync`, `data-access-model-check`, `data-review`, leaders' skill `data-gating-protocol`; bound into coding-leader, coordination-leader, spec-writer, codebase-explorer, documentalist; README section
  - review the draft: verdict scale (CLEAR / MEASURES-PROPOSED / NEEDS-HUMAN-DECISION), preflight writing nothing, default classes and measures
  - checker script for the register (the format's consistency checks, run at the end of every skill), shipped inside a skill folder
  - maybe split `references/data-register.md` per file, so each skill reads only the formats it writes
  - try it: cold start on a real repo with personal data
- [ ] Build plans (wave model): written for both ports and the skills (`references/build-plan-model.md`, skills `build-plan-authoring` and `wave-execution`, coding-leader chunk mode, documentalist wave mode, data-steward once per version).
  - migrate infinite_flow's v3 plans onto the model, when the owner asks: one shared workflow instead of four §3 copies, a status line per chunk, a wave log for the wave records, waves of v3.1–v3.3 re-formed (v3.1's chunk 16 back to wave 5, v3.2's waves 5, 10 and 11, v3.3's wave 6)
  - try it on the next wave and review the chunk brief
