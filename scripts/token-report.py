#!/usr/bin/env python3
"""Token and cost accounting per agent from Claude Code session transcripts.

Reads session JSONL files (and the subagent transcripts beside them), dedupes
the per-content-block repeats of each API response, prices the four token
buckets, and attributes the Edit/Write lines each agent produced to
docs / tests / code / other.

    token-report.py PATH [PATH...] [--json out.json] [--by agent|type|session|chunk]

PATH is a session .jsonl, or a project directory (every session in it).
Prices live in PRICES below, per million tokens; edit them when they change.
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

# $ per 1M tokens: input, output, cache read, cache write 5m, cache write 1h.
# Source: claude-api skill model table (cached 2026-10-06); writes are 1.25x / 2x input.
def _p(i, o, r):
    return dict(input=i, output=o, read=r, w5=i * 1.25, w1=i * 2.0)

PRICES = {
    "claude-fable-5": _p(10, 50, 1.0),
    "claude-fable-5-1": _p(10, 50, 0.25),
    "claude-opus-5-5": _p(4, 20, 0.20),
    "claude-opus-5": _p(5, 25, 0.50),
    "claude-opus-4": _p(5, 25, 0.50),
    "claude-sonnet-5-5": _p(2, 10, 0.20),
    "claude-sonnet-5": _p(2, 10, 0.20),
    "claude-haiku-5-5": _p(0.10, 0.50, 0.01),
    "claude-haiku-4-5": _p(1, 5, 0.10),
}

DOC_DIRS = {"docs", "doc", "specs", "spec", "ui_ux", "intent", "data-register",
            "references", "design", "adr", "decisions"}
TEST_DIRS = {"test", "tests", "__tests__", "e2e", "cypress", "playwright", "testdata", "fixtures"}
DOC_EXT = {".md", ".mdx", ".rst", ".txt", ".adoc"}
CONF_EXT = {".json", ".yml", ".yaml", ".toml", ".lock", ".ini", ".env", ".cfg"}
TEST_NAME = re.compile(r"(\.|_|-)(test|spec)s?(\.|_|$)|^test_|_test\.")


def price_for(model):
    best = None
    for k in PRICES:
        if model.startswith(k) and (best is None or len(k) > len(best)):
            best = k
    return PRICES.get(best)


def classify(path):
    p = path.replace("\\", "/")
    parts = p.lower().split("/")
    name = parts[-1]
    ext = os.path.splitext(name)[1]
    if ext in DOC_EXT or name.endswith(".atom.md"):
        return "docs"
    if TEST_NAME.search(name) or any(x in TEST_DIRS for x in parts[:-1]):
        return "tests"
    if any(x in DOC_DIRS for x in parts[:-1]):
        return "docs"
    if ext in CONF_EXT or name in ("Makefile", "Dockerfile"):
        return "other"
    return "code"


def nlines(s):
    return 0 if not s else s.count("\n") + (0 if s.endswith("\n") else 1)


def parse(path):
    """-> (calls, writes). calls: one dict per API response; writes: tool-input edits."""
    byid = {}
    order = []
    tools = {}
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        m = d.get("message")
        if not isinstance(m, dict) or not m.get("usage"):
            continue
        if m.get("model") == "<synthetic>":
            continue
        mid = m.get("id") or d.get("uuid")
        u = m["usage"]
        cc = u.get("cache_creation") or {}
        rec = dict(
            id=mid, model=m.get("model", ""), ts=d.get("timestamp", ""),
            cwd=d.get("cwd", ""), branch=d.get("gitBranch", ""),
            input=u.get("input_tokens", 0) or 0,
            output=u.get("output_tokens", 0) or 0,
            read=u.get("cache_read_input_tokens", 0) or 0,
            w5=cc.get("ephemeral_5m_input_tokens", 0) or 0,
            w1=cc.get("ephemeral_1h_input_tokens", 0) or 0,
            wtot=u.get("cache_creation_input_tokens", 0) or 0,
        )
        if not rec["w5"] and not rec["w1"]:
            rec["w5"] = rec["wtot"]
        if mid in byid:
            old = byid[mid]
            for k in ("input", "output", "read", "w5", "w1", "wtot"):
                old[k] = max(old[k], rec[k])
        else:
            byid[mid] = rec
            order.append(mid)
        for b in m.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                tools.setdefault(b["id"], (b, d.get("timestamp", "")))
    calls = [byid[i] for i in order]
    writes = []
    for b, tts in tools.values():
        inp = b.get("input") or {}
        n = b.get("name")
        if n == "Write":
            writes.append((inp.get("file_path", ""), nlines(inp.get("content", "")), 0, tts))
        elif n == "Edit":
            writes.append((inp.get("file_path", ""), nlines(inp.get("new_string", "")),
                           nlines(inp.get("old_string", "")), tts))
        elif n == "MultiEdit":
            for e in inp.get("edits", []):
                writes.append((inp.get("file_path", ""), nlines(e.get("new_string", "")),
                               nlines(e.get("old_string", "")), tts))
    return calls, writes


def cost_of(rec):
    pr = price_for(rec["model"])
    if not pr:
        return None
    return (rec["input"] * pr["input"] + rec["output"] * pr["output"]
            + rec["read"] * pr["read"] + rec["w5"] * pr["w5"] + rec["w1"] * pr["w1"]) / 1e6


def first_prompt(path):
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message")
        if d.get("type") == "user" and isinstance(m, dict):
            c = m.get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            if isinstance(c, str) and c.strip():
                return c.strip()
    return ""


CHUNK = re.compile(r"[Cc]hunk\s+(\d+[a-z]?)\b")
WAVE = re.compile(r"\bwave\s+(\d+)\b", re.I)


def session_files(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(glob.glob(os.path.join(p, "*.jsonl")))
        else:
            out.append(p)
    return out


def collect(paths):
    agents = []
    for sf in session_files(paths):
        sid = os.path.basename(sf)[:-6]
        units = [(sf, "top-level", "", sid)]
        sub = os.path.join(sf[:-6], "subagents")
        for f in sorted(glob.glob(os.path.join(sub, "agent-*.jsonl"))):
            meta = {}
            try:
                meta = json.load(open(f[:-6] + ".meta.json"))
            except (OSError, ValueError):
                pass
            units.append((f, meta.get("agentType") or "subagent", meta.get("description", ""), sid))
        for f, atype, desc, sid in units:
            calls, writes = parse(f)
            if not calls:
                continue
            brief = first_prompt(f) if atype != "top-level" else ""
            text = desc + " " + brief[:3000]
            cm, wm = CHUNK.search(text), WAVE.search(text)
            a = dict(file=f, session=sid, type=atype, desc=desc, calls=calls,
                     chunk=cm.group(1) if cm else "", wave=wm.group(1) if wm else "",
                     models=sorted({c["model"] for c in calls}),
                     start=min(c["ts"] for c in calls), end=max(c["ts"] for c in calls),
                     branches=sorted({c["branch"] for c in calls if c["branch"]}))
            tot = defaultdict(float)
            unpriced = 0
            for c in calls:
                for k in ("input", "output", "read", "w5", "w1"):
                    tot[k] += c[k]
                cst = cost_of(c)
                if cst is None:
                    unpriced += 1
                else:
                    tot["cost"] += cst
                tot["peak"] = max(tot["peak"], c["input"] + c["read"] + c["w5"] + c["w1"])
            a["tot"] = dict(tot)
            a["unpriced_calls"] = unpriced
            lines = defaultdict(lambda: [0, 0])
            a["writes"] = [(classify(w[0]), w[1], w[2], w[3]) for w in writes]
            for path, add, rem, _ in writes:
                k = classify(path)
                lines[k][0] += add
                lines[k][1] += rem
            a["lines"] = {k: {"added": v[0], "removed": v[1]} for k, v in lines.items()}
            agents.append(a)
    return agents


def fmt(n):
    n = float(n)
    for u, s in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if abs(n) >= u:
            return f"{n / u:.1f}{s}"
    return f"{n:.0f}"


def label(a, by):
    if by == "type":
        return a["type"]
    if by == "session":
        return a["session"][:8]
    if by == "chunk":
        return f"w{a['wave'] or '?'} c{a['chunk']}" if a["chunk"] else "(no chunk)"
    return f"{a['type']}: {a['desc'][:34]}" if a["desc"] else a["type"]


def table(agents, by):
    rows = defaultdict(lambda: defaultdict(float))
    for a in agents:
        r = rows[label(a, by)]
        r["agents"] += 1
        r["calls"] += len(a["calls"])
        for k in ("input", "output", "read", "w5", "w1", "cost"):
            r[k] += a["tot"].get(k, 0)
        r["peak"] = max(r["peak"], a["tot"]["peak"])
        for cat in ("docs", "tests", "code", "other"):
            r[cat] += a["lines"].get(cat, {}).get("added", 0)
    hdr = f"{'':40} {'n':>3} {'calls':>5} {'fresh':>7} {'cwrite':>7} {'cread':>8} {'out':>7} {'peak':>7} {'$':>8} | {'docs':>5} {'tests':>5} {'code':>5} {'other':>5}"
    print(hdr)
    print("-" * len(hdr))
    for name, r in sorted(rows.items(), key=lambda kv: -kv[1]["cost"]):
        print(f"{name[:40]:40} {int(r['agents']):>3} {int(r['calls']):>5} {fmt(r['input']):>7} "
              f"{fmt(r['w5'] + r['w1']):>7} {fmt(r['read']):>8} {fmt(r['output']):>7} {fmt(r['peak']):>7} "
              f"{r['cost']:>8.2f} | {int(r['docs']):>5} {int(r['tests']):>5} {int(r['code']):>5} {int(r['other']):>5}")


def summary(agents):
    t = defaultdict(float)
    for a in agents:
        for k in ("input", "output", "read", "w5", "w1", "cost"):
            t[k] += a["tot"].get(k, 0)
    inbound = t["input"] + t["read"] + t["w5"] + t["w1"]
    print(f"\nInbound {fmt(inbound)} tokens (fresh {fmt(t['input'])}, cache write {fmt(t['w5'] + t['w1'])}, "
          f"cache read {fmt(t['read'])}); outbound {fmt(t['output'])}; total ${t['cost']:.2f}")
    # cost by bucket
    by = defaultdict(float)
    for a in agents:
        for c in a["calls"]:
            pr = price_for(c["model"])
            if not pr:
                continue
            by["fresh input"] += c["input"] * pr["input"] / 1e6
            by["cache write"] += (c["w5"] * pr["w5"] + c["w1"] * pr["w1"]) / 1e6
            by["cache read"] += c["read"] * pr["read"] / 1e6
            by["output"] += c["output"] * pr["output"] / 1e6
    tot = sum(by.values()) or 1
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        tk = {"fresh input": t["input"], "cache write": t["w5"] + t["w1"],
              "cache read": t["read"], "output": t["output"]}[k]
        allt = inbound + t["output"] or 1
        print(f"  {k:12} {tk / allt * 100:5.1f}% of tokens  {v / tot * 100:5.1f}% of cost  ${v:.2f}")
    un = sum(a["unpriced_calls"] for a in agents)
    if un:
        print(f"  ({un} calls on models missing from PRICES are not in the cost)")
    docs = defaultdict(int)
    for a in agents:
        for k, v in a["lines"].items():
            docs[k] += v["added"]
    print("Lines written by Edit/Write (added): " + ", ".join(f"{k} {v}" for k, v in sorted(docs.items())) +
          "  [Bash-made edits and commits are not counted]")


def era_of(ts, eras):
    name = eras[0][0]
    for n, start in eras:
        if ts >= start:
            name = n
    return name


def parse_eras(spec):
    out = []
    for part in spec.split(","):
        n, _, t = part.partition("=")
        out.append((n, t or ""))
    return sorted(out, key=lambda x: x[1])


def era_report(agents, eras):
    names = [n for n, _ in eras]
    R = {n: defaultdict(float) for n in names}
    P = {n: defaultdict(float) for n in names}
    for a in agents:
        for c in a["calls"]:
            n = era_of(c["ts"], eras)
            r = R[n]
            cst = cost_of(c) or 0
            pr = price_for(c["model"]) or dict(input=0, output=0, read=0, w5=0, w1=0)
            r["calls"] += 1
            r["cost"] += cst
            r["c_in"] += c["input"] * pr["input"] / 1e6
            r["c_w"] += (c["w5"] * pr["w5"] + c["w1"] * pr["w1"]) / 1e6
            r["c_r"] += c["read"] * pr["read"] / 1e6
            r["c_out"] += c["output"] * pr["output"] / 1e6
            r["inb"] += c["input"] + c["read"] + c["w5"] + c["w1"]
            r["out"] += c["output"]
            r["wr"] += c["w5"] + c["w1"]
            P[n][a["type"]] += cst
        for cat, add, rem, ts in a["writes"]:
            R[era_of(ts, eras)][cat] += add
    w = 14
    def row(label, f):
        print(f"{label:24}" + "".join(f"{f(R[n]):>{w}}" for n in names))
    print(f"{'':24}" + "".join(f"{n:>{w}}" for n in names))
    row("calls", lambda r: f"{int(r['calls'])}")
    row("total $", lambda r: f"{r['cost']:.0f}")
    row("  cache write $", lambda r: f"{r['c_w']:.0f} ({r['c_w'] / (r['cost'] or 1) * 100:.0f}%)")
    row("  cache read $", lambda r: f"{r['c_r']:.0f} ({r['c_r'] / (r['cost'] or 1) * 100:.0f}%)")
    row("  output $", lambda r: f"{r['c_out']:.0f} ({r['c_out'] / (r['cost'] or 1) * 100:.0f}%)")
    row("inbound tokens", lambda r: fmt(r["inb"]))
    row("outbound tokens", lambda r: fmt(r["out"]))
    row("out / in", lambda r: f"{r['out'] / (r['inb'] or 1) * 100:.2f}%")
    row("lines code", lambda r: f"{int(r['code'])}")
    row("lines tests", lambda r: f"{int(r['tests'])}")
    row("lines docs", lambda r: f"{int(r['docs'])}")
    row("tests : code", lambda r: f"{r['tests'] / (r['code'] or 1):.2f}")
    row("docs : code", lambda r: f"{r['docs'] / (r['code'] or 1):.2f}")
    row("$ per line written", lambda r: f"{r['cost'] / ((r['code'] + r['tests'] + r['docs']) or 1):.3f}")
    row("$ per code line", lambda r: f"{r['cost'] / (r['code'] or 1):.2f}")
    print("\nShare of cost by persona:")
    types = sorted({t for n in names for t in P[n]}, key=lambda t: -sum(P[n][t] for n in names))
    for t in types[:9]:
        print(f"{t:24}" + "".join(f"{P[n][t] / (R[n]['cost'] or 1) * 100:>{w - 1}.0f}%" for n in names))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--by", choices=["agent", "type", "session", "chunk"], default="type")
    ap.add_argument("--eras", help="name=ISO-UTC-start,... e.g. v1=2026-01-01,v2=2026-09-26T16:39")
    ap.add_argument("--json", help="write per-agent and per-call data here")
    a = ap.parse_args()
    agents = collect(a.paths)
    if not agents:
        sys.exit("no usable transcripts found")
    if a.eras:
        era_report(agents, parse_eras(a.eras))
        return
    table(agents, a.by)
    summary(agents)
    if a.json:
        json.dump([{k: v for k, v in x.items() if k != "file"} | {"file": x["file"]} for x in agents],
                  open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
