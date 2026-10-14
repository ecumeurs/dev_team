# TODO

- [ ] `data-steward` agent: drafted and wired, to review and try.
  - done: agent (Claude and OpenCode), `references/data-register.md`, `references/data-security-baseline.md`, skills `data-cold-start`, `data-preflight`, `data-post-task-sync`, `data-access-model-check`, `data-review`, leaders' skill `data-gating-protocol`; bound into coding-leader, coordination-leader, spec-writer, codebase-explorer, documentalist; README section
  - review the draft: verdict scale (CLEAR / MEASURES-PROPOSED / NEEDS-HUMAN-DECISION), preflight writing nothing, default classes and measures
  - checker script for the register (the format's consistency checks, run at the end of every skill), shipped inside a skill folder
  - maybe split `references/data-register.md` per file, so each skill reads only the formats it writes
  - try it: cold start on a real repo with personal data
