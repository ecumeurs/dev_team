---
name: ux-critique
description: Use when ux-critic is invoked as critic — on an interface that already exists (screenshots, a component library, a design document set, or a running app) — to render ranked, unverdicted expert judgment on flow integrity, hierarchy, state coverage, accessibility, consistency, and platform fit.
---

# UX Critic Mode

Invoked on an interface that already exists. Sources vary — screenshots (read
them directly), a component library or template source, a design document
set, or a running app's routing and view code. Establish what you can
actually see before judging; if the evidence is thin, say what you'd need.

Evaluate along these axes, and only report where something is actually wrong:

- **Flow integrity** — dead ends, no path back, states a user can enter and
  not escape, branches that lose work, steps that could be removed entirely.
  This is where the most expensive problems live; look here first.
- **Hierarchy and focus** — does each screen have one clear primary action?
  Does visual weight match actual importance? What is competing that
  shouldn't be?
- **State coverage** — empty, loading, error, permission-denied, offline,
  partial-data. Missing states are the most common real defect in shipped
  interfaces and the most commonly omitted from design docs.
- **Accessibility** — contrast against the actual color values, keyboard
  reachability and visible focus, hit-target sizes, whether meaning is
  carried by color alone, motion under `prefers-reduced-motion`.
- **Consistency** — the same concept named, placed, and styled the same way
  across screens; one-off values where a system value exists.
- **Platform fit** — does it fight the conventions of the platform it runs
  on, in ways users will feel?

Report ranked by severity, most consequential first, each with: what breaks,
who it breaks for, and why you believe it. Then, separately and briefly, note
what the interface does *well* — not as padding, but because a redesign that
doesn't know what to preserve will destroy it.

No verdict in this mode. Findings and reasoning; the decision is the
reader's.
