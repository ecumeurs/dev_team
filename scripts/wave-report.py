#!/usr/bin/env python3
"""Per-wave cost of a version's build, cut at the waves' merge commits (git).

    wave-report.py --repo REPO --version v3.1 --sessions PATH [PATH...] [--json out.json]

A wave ends at its merge into the repo's HEAD branch ("Merge <version>-w<n>: ...",
first parent) and opens at the previous wave's merge; the version's first wave
opens at its "<version> wave <n> started" wave-log commit. Calls before that are
reported as "before", calls after the last merge as the open wave. Per wave: cost
by agent type, the top level's share, its turns and context per turn (the
driver's cost, what a scripted driver would remove), and what the wave merged
($ per 100 added code+test lines).
"""
import argparse, importlib.util, json, os, re, subprocess
from collections import defaultdict
from datetime import datetime, timezone

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("tr", os.path.join(here, "token-report.py"))
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

# a chunk commit ("v3.1 chunk 9b: ...", "Chunk 12: ...") or a chunk branch's merge ("Merge v3.1-c3-...")
GIT_CHUNK = re.compile(r"(?:v\d+(?:\.\d+)+\s+)?[Cc]hunk\s+(\d+)[a-z]?\b|Merge v\d+(?:\.\d+)+-c(\d+)\b")
COLS = 6  # agent types shown as columns; the rest go to "other"


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout


def utc(iso):
    """Git's %aI -> the UTC 'YYYY-MM-DDTHH:MM:SS' that call timestamps compare against."""
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def waves(repo, version):
    """The version's merged waves in order, each with its window, chunks and merged lines."""
    out = []
    for line in git(repo, "log", "--first-parent", "--merges", "--format=%H|%aI|%s").splitlines():
        h, d, s = line.split("|", 2)
        m = re.match(rf"Merge {re.escape(version)}-w(\d+):", s)
        if m:
            out.append(dict(name=f"w{m.group(1)}", merge=h, end=utc(d)))
    out.sort(key=lambda w: w["end"])
    start = ""
    if out:
        pat = rf"{re.escape(version)} wave {out[0]['name'][1:]} started"
        for line in git(repo, "log", "--all", "--format=%aI|%s").splitlines():
            d, s = line.split("|", 1)
            if re.search(pat, s):
                start = min(start or utc(d), utc(d))
    prev = start
    for w in out:
        w["start"], prev = prev, w["end"]
        lines = defaultdict(int)
        for l in git(repo, "diff", "--numstat", "--no-renames", f"{w['merge']}^1", w["merge"]).splitlines():
            parts = l.split("\t")
            if len(parts) == 3 and parts[0].isdigit():
                lines[tr.classify(parts[2])] += int(parts[0])
        w["lines"] = dict(lines)
        subjects = git(repo, "log", "--format=%s", f"{w['merge']}^1..{w['merge']}^2").splitlines()
        w["chunks"] = sorted({m.group(1) or m.group(2) for m in map(GIT_CHUNK.match, subjects) if m}, key=int)
    return out


def bucket(t, ws):
    if not ws or (ws[0]["start"] and t < ws[0]["start"]):
        return "before"
    for w in ws:
        if t <= w["end"]:
            return w["name"]
    return f"w{int(ws[-1]['name'][1:]) + 1} (open)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--version", required=True, help="as the wave branches name it, e.g. v3.1")
    ap.add_argument("--sessions", nargs="+", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    ws = waves(a.repo, a.version)
    agents = tr.collect(a.sessions)

    cost = defaultdict(lambda: defaultdict(float))
    top = defaultdict(lambda: dict(turns=0, ctx=0, peak=0))
    for x in agents:
        for c in x["calls"]:
            b = bucket(c["ts"][:19], ws)
            cs = tr.cost_of(c) or 0
            cost[b][x["type"]] += cs
            cost[b]["_total"] += cs
            if x["type"] == "top-level":
                ctx = c["input"] + c["read"] + c["w5"] + c["w1"]
                t = top[b]
                t["turns"] += 1
                t["ctx"] += ctx
                t["peak"] = max(t["peak"], ctx)

    by_type = defaultdict(float)
    for b in cost.values():
        for k, v in b.items():
            if k not in ("_total", "top-level"):
                by_type[k] += v
    cols = sorted(by_type, key=by_type.get, reverse=True)[:COLS]
    order = ["before"] + [w["name"] for w in ws] + sorted(k for k in cost if k.endswith("(open)"))
    info = {w["name"]: w for w in ws}

    print(f"{a.version}: waves cut at their merge commits")
    print(f"{'wave':>9} {'$':>7} | " + " ".join(f"{c[:11]:>11}" for c in cols) + f" {'other':>7} | "
          f"{'top $':>6} {'top%':>5} {'turns':>5} {'ctx/turn':>8} {'peak':>6} | {'chunks':>6} {'code':>5} {'tests':>5} {'$/100':>6}")
    rows = []
    for b in order:
        c = cost.get(b)
        if not c:
            continue
        other = max(0.0, c["_total"] - c.get("top-level", 0) - sum(c.get(k, 0) for k in cols))
        t = top[b]
        w = info.get(b, {})
        code, tests = w.get("lines", {}).get("code", 0), w.get("lines", {}).get("tests", 0)
        per = c["_total"] / (code + tests) * 100 if code + tests else 0
        print(f"{b:>9} {c['_total']:>7.2f} | " + " ".join(f"{c.get(k, 0):>11.2f}" for k in cols) + f" {other:>7.2f} | "
              f"{c.get('top-level', 0):>6.2f} {100 * c.get('top-level', 0) / (c['_total'] or 1):>4.0f}% {t['turns']:>5} "
              f"{tr.fmt(t['ctx'] / (t['turns'] or 1)):>8} {tr.fmt(t['peak']):>6} | "
              f"{len(w.get('chunks', [])) if w else '':>6} {code if w else '':>5} {tests if w else '':>5} {f'{per:.1f}' if w else '':>6}")
        rows.append(dict(wave=b, start=w.get("start"), end=w.get("end"), merge=w.get("merge"), chunks=w.get("chunks"),
                         lines=w.get("lines"), cost={k: v for k, v in c.items() if k != "_total"}, total=c["_total"],
                         top_turns=t["turns"], top_ctx_mean=t["ctx"] / (t["turns"] or 1), top_ctx_peak=t["peak"]))
    total = sum(c["_total"] for c in cost.values())
    print(f"\nTotal ${total:.2f} over {len(ws)} merged waves; top level ${sum(c.get('top-level', 0) for c in cost.values()):.2f}"
          " (ctx = input + cache read + cache write per top-level call)")
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
