---
name: secret-safe-authoring
description: Never write a real or fake secret-shaped string (API key, DB/DSN connection string with embedded credentials, private key, bearer token) anywhere in your output — chat prose, code examples, file writes. Use whenever a task involves credentials, connection strings, tokens, or "show me an example of the config/env/key" — including purely illustrative examples.
---

# Secret-Safe Authoring

Goal: never *originate* a secret-shaped string, whether the value is real or made up. This applies everywhere your output goes: chat replies, files you write, code you generate.

## Why this is a hard rule, not a style preference

Many workstations route LLM traffic through a local DLP proxy (Presidio-style regex/entity detection in front of the model). That detection is **shape-based** — it matches `postgres://user:pass@host`, `sk-...`, `AKIA...`, JWT triple-dot shapes, etc., regardless of whether the value is real. It cannot tell "here's a fake example" from "here's a live credential."

The failure mode this causes: you write an illustrative fake secret in a reply → it becomes part of the conversation transcript → every subsequent turn re-sends the **full transcript** to the model → the proxy blocks the request **again, every time**, because the poisoned message is still in history. One fabricated example can wedge an entire session. There is no hook or client-side mechanism that reliably intercepts your own generated text before it's appended to history and resent — prevention has to happen at authoring time, by you, before you emit the text.

## Rule

Never write, in any output:
- A literal `scheme://user:password@host` connection string (real or placeholder values in the credential position) — this shape alone is enough to trigger detection regardless of content.
- A string matching a real provider key format (`sk-...`, `AKIA...`, `ghp_...`, `xox...`, `-----BEGIN ... PRIVATE KEY-----`, JWT triples, etc.) — even a syntactically-valid *fake* one for illustration.
- A `key=value`/`key: "value"` assignment where value is a plausible-looking 16+ char secret, for the same reason.

## What to do instead

- **When a task needs a real secret** (API key, DB password, service token): tell the user to store it in this project's secrets manager if one exists (check for Infisical, Vault, `.env` + keyring, etc. — a project-level skill may already cover the exact flow, e.g. this repo's `infisical-key-onboarding` if present). Never ask the user to paste the value into chat "to check the format" — if they do anyway, treat it as a leak (see `leak-response` if that skill is available) rather than proceeding as normal.
- **When a running process needs the secret**: prefer injection that never puts the value in your context — wrapper scripts, `infisical run -- <cmd>`, `env_file:`, OS keyring lookups performed by the app itself — not you reading/typing/echoing the value.
- **When you just need to illustrate a shape** (docs, examples): break the pattern instead of completing it — describe fields separately ("a Postgres DSN has the form `scheme://user:password@host/db`" as prose about the *shape*, not a filled-in instance), or use a single non-colon-separated placeholder (`postgres://REDACTED@host/db` — no `user:pass` segment at all), never a filled `user:fakepass@host` instance.
- **Verify a credential works without displaying it**: use a health/status probe (login test, `/health` endpoint, a 401-vs-200 check) instead of asking to see or print the value.

## If you've already done it

If you notice mid-session that you just wrote a secret-shaped string: say so plainly to the user, and note that your next message (or a later `/clear`/`/compact`) is the fix — the string stays live in history until it's summarized away or the session restarts. Don't repeat it while explaining.
