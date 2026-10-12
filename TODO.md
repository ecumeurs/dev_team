# TODO

- [ ] Work on a data modelist agent. The team must have one, triggered to maintain a register of our data (for GDPR, but for other uses too):
  - data modeling: schemas, entities, relationships, migrations
  - per data item: origin, sensitivity, importance, usage, applicable regulation (GDPR, etc.)
  - mitigation strategy matched to sensitivity (protection level vs. how sensitive the data is)
  - design the register's layout: how to document each data source and the data usage graph (where data comes from, which components/processes use it, where it flows)
  - triggering: define when it runs (e.g. when a change adds or alters data, or after a coding task closes), like documentalist's gates
