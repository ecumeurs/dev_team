#!/usr/bin/env python3
"""Per-chunk cost against the code the chunk actually changed (git).

    chunk-report.py --repo REPO --sessions PROJECT_DIR [--eras name=ISO,...]

Joins token-report.py's agent costs to git commits whose subject starts with
"Chunk <id>" or "v<version> chunk <id>" (the repo's conventions up to v3.0 and
from v3.1). Cost is attributed to a chunk from the chunk number in an agent's
brief; a subagent without one inherits its parent's;
top-level calls are charged to the chunks whose agents were running at that
moment (split equally), the rest is reported as unattributed.
"""
import argparse, importlib.util, json, os, re, subprocess, sys
from collections import defaultdict
from datetime import datetime, timezone
from statistics import median

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("tr", os.path.join(here, "token-report.py"))
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

CHUNK = re.compile(r"[Cc]hunk\s+(\d+[a-z]?)\b|\bc(\d+[a-z]?)-[a-z]")
GIT_CHUNK = re.compile(r"(?:v\d+(?:\.\d+)+\s+)?[Cc]hunk\s+(\d+[a-z]?)\b")
VERS = re.compile(r"\bv(\d\.\d)(?:\.\d)?-(?:c|w)\d|\bv(\d\.\d)\b")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def era_name(t, eras):
    if not isinstance(t, str):
        t = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return tr.era_of(t, eras)


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout


def git_chunks(repo, eras):
    """chunk key -> line counts from commits titled 'Chunk <id>...' or 'v3.1 chunk <id>...' (new files vs changed files)."""
    fmt = "--format=@@%H|%aI|%s"
    added = defaultdict(set)
    h = None
    for line in git(repo, "log", "--no-merges", "--no-renames", "--diff-filter=A", "--name-only", fmt).splitlines():
        if line.startswith("@@"):
            h = line[2:].split("|", 1)[0]
        elif line.strip():
            added[h].add(line.strip())
    ch = defaultdict(lambda: defaultdict(int))
    commit = None
    for line in git(repo, "log", "--no-merges", "--no-renames", "--numstat", fmt).splitlines():
        if line.startswith("@@"):
            h, d, s = line[2:].split("|", 2)
            m = GIT_CHUNK.match(s)
            commit = (re.sub(r"[a-z]$", "", m.group(1)), era_name(datetime.fromisoformat(d).timestamp(), eras)) if m else None
            if commit:
                ch[commit]["commits"] += 1
            continue
        parts = line.split("\t")
        if commit and len(parts) == 3 and parts[0].isdigit():
            add, rem, path = int(parts[0]), int(parts[1]), parts[2]
            cat = tr.classify(path)
            ch[commit][f"{cat}_{'new' if path in added[h] else 'mod'}"] += add
            ch[commit][f"{cat}_del"] += rem
    return ch


def code_size_at(repo, ref):
    """Bytes of code+test files at a ref (codebase size proxy)."""
    try:
        out = git(repo, "ls-tree", "-r", "-l", ref)
    except subprocess.CalledProcessError:
        return 0
    tot = 0
    for l in out.splitlines():
        meta, path = l.split("\t", 1)
        size = meta.split()[-1]
        if size.isdigit() and tr.classify(path) in ("code", "tests"):
            tot += int(size)
    return tot


def agent_key(a, eras):
    text = a["desc"] + " " + (tr.first_prompt(a["file"]) if a["type"] != "top-level" else "")[:6000]
    m = CHUNK.search(text)
    if not m:
        return None
    cid = re.sub(r"[a-z]$", "", m.group(1) or m.group(2))
    v = VERS.search(text)
    era = era_name(ts(a["start"]), eras)
    return (cid, era)


def parents(agents):
    """agent file -> parent agent file, through meta.toolUseId."""
    owner = {}
    for a in agents:
        for line in open(a["file"], errors="replace"):
            if '"tool_use"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            m = d.get("message")
            if isinstance(m, dict):
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        owner[b["id"]] = a["file"]
    out = {}
    for a in agents:
        mf = a["file"][:-6] + ".meta.json"
        try:
            tid = json.load(open(mf)).get("toolUseId")
        except (OSError, ValueError):
            continue
        if tid in owner:
            out[a["file"]] = owner[tid]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--sessions", nargs="+", required=True)
    ap.add_argument("--eras", default="v1=2000-01-01,v2=2026-09-26T16:39,v3=2026-10-07T12:11,v3.1=2026-10-16T18:04")
    ap.add_argument("--json")
    a = ap.parse_args()
    eras = tr.parse_eras(a.eras)
    agents = tr.collect(a.sessions)
    byfile = {x["file"]: x for x in agents}
    par = parents(agents)

    key = {x["file"]: agent_key(x, eras) for x in agents}
    for _ in range(4):  # propagate parent's chunk to children without one
        for f, p in par.items():
            if key.get(f) is None and key.get(p) is not None and byfile[f]["type"] != "top-level":
                key[f] = key[p]

    cost = defaultdict(lambda: defaultdict(float))
    windows = defaultdict(list)
    for x in agents:
        k = key[x["file"]]
        if x["type"] == "top-level":
            continue
        if k is None:
            cost["(no chunk)"]["sub"] += x["tot"].get("cost", 0)
            continue
        cost[k]["agents"] += x["tot"].get("cost", 0)
        cost[k]["n"] += 1
        for c in x["calls"]:
            cost[k]["calls"] += 1
        windows[k].append((ts(x["start"]), ts(x["end"])))
    # top-level calls -> chunks whose agents were running then
    unattr = 0.0
    for x in agents:
        if x["type"] != "top-level":
            continue
        for c in x["calls"]:
            t = ts(c["ts"])
            live = [k for k, ws in windows.items() if any(s - 120 <= t <= e + 120 for s, e in ws)]
            cs = tr.cost_of(c) or 0
            if live:
                for k in live:
                    cost[k]["top"] += cs / len(live)
            else:
                unattr += cs

    g = git_chunks(a.repo, eras)
    size = {}
    for n, _ in eras:
        pass
    tags = {"v1": "v1.0", "v2": "v1.0", "v3": "v2.0.0", "v3.1": "v3.0.0"}  # codebase at the era's start
    for n in [e[0] for e in eras]:
        size[n] = code_size_at(a.repo, tags.get(n, "HEAD")) if n != "v1" else 0

    rows = []
    for k in sorted(set(cost) | set(g), key=lambda k: (str(k[1]) if isinstance(k, tuple) else "z", str(k))):
        if not isinstance(k, tuple):
            continue
        cc, gg = cost.get(k, {}), g.get(k, {})
        total = cc.get("agents", 0) + cc.get("top", 0)
        new = gg.get("code_new", 0) + gg.get("tests_new", 0)
        mod = gg.get("code_mod", 0) + gg.get("tests_mod", 0)
        code = gg.get("code_new", 0) + gg.get("code_mod", 0)
        tests = gg.get("tests_new", 0) + gg.get("tests_mod", 0)
        docs = gg.get("docs_new", 0) + gg.get("docs_mod", 0)
        rows.append(dict(chunk=k[0], era=k[1], cost=total, agents=cc.get("agents", 0), top=cc.get("top", 0),
                         commits=gg.get("commits", 0), new=new, mod=mod, code=code, tests=tests, docs=docs))

    print(f"{'chunk':>8} {'era':>4} {'$':>7} {'commits':>7} | {'code':>5} {'tests':>5} {'docs':>5} | {'new':>5} {'mod':>5} {'mod%':>5} | {'$/100 code+test lines':>21}")
    for r in rows:
        if not r["commits"]:
            continue
        ct = r["new"] + r["mod"]
        print(f"{r['chunk']:>8} {r['era']:>4} {r['cost']:>7.1f} {r['commits']:>7} | {r['code']:>5} {r['tests']:>5} {r['docs']:>5} | "
              f"{r['new']:>5} {r['mod']:>5} {r['mod'] / (ct or 1) * 100:>4.0f}% | {r['cost'] / (ct or 1) * 100:>21.1f}")

    print("\nBy era (chunks with commits and cost):")
    print(f"{'era':>4} {'chunks':>6} {'median $':>9} {'median $/100':>12} {'mod share':>9} {'tests:code':>10} {'code base start':>16}")
    for n, _ in eras:
        rs = [r for r in rows if r["era"] == n and r["commits"] and r["cost"] > 0]
        if not rs:
            continue
        per = [r["cost"] / ((r["new"] + r["mod"]) or 1) * 100 for r in rs if r["new"] + r["mod"]]
        mod = sum(r["mod"] for r in rs)
        tot = sum(r["new"] + r["mod"] for r in rs)
        print(f"{n:>4} {len(rs):>6} {median(r['cost'] for r in rs):>9.1f} {median(per) if per else 0:>12.1f} "
              f"{mod / (tot or 1) * 100:>8.0f}% {sum(r['tests'] for r in rs) / (sum(r['code'] for r in rs) or 1):>10.2f} "
              f"{size.get(n, 0) / 1e6:>14.2f}MB")
    attributed = sum(r["cost"] for r in rows)
    allc = sum(x["tot"].get("cost", 0) for x in agents)
    print(f"\nAttributed to chunks: ${attributed:.0f} of ${allc:.0f} total "
          f"(subagents without a chunk ${cost['(no chunk)']['sub']:.0f}, top-level outside any chunk ${unattr:.0f})")
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
