#!/usr/bin/env python3
"""agent-stats: what a build-plan chunk or wave cost, read from the Claude Code
transcripts.

  agent-stats chunk <id> [--release v3.3]   one chunk: its owner(s) and every agent they started
  agent-stats wave <n>  [--release v3.3]    one wave: its tagged agents, the driver's turns
                                            in the wave's window, and untagged agents there
  agent-stats list [--release v3.3]         the releases, waves and chunks the briefs name

Options: --md (markdown tables, for the wave log), --line (one line, for a chunk's
Record), --json, --project DIR (the repo; default: the current one), --top N.

Where the numbers come from. Claude Code writes each session to
~/.claude/projects/<path>/<session>.jsonl and each subagent to
<session>/subagents/agent-*.jsonl with a .meta.json (role, the tool call that
started it, its depth). Every model turn carries its token usage. A turn split
over several lines repeats its usage, so turns are counted once by message id,
and tool calls once by tool-use id.

How agents are attributed. The git branch stamped on transcript lines is the
session's starting branch, not where an agent worked, so it can't be used.
Instead a top-level agent is tagged from its brief, as wave-execution writes it:
"Chunk mode. Build chunk 23 ... of v3.2, wave 6" (or "Resume chunk"), a chunk
branch or worktree (v3.2-c30), a wave branch or worktree (v3.2-w6), or
"v3.2 wave 6". Agents it starts inherit its tag. A wave's window runs from its
first tagged agent to its merge into main (from git), or to its last tagged
agent when not merged yet.

Cost is at Anthropic API list prices (PRICES below, with the date they were
checked): on a subscription it is the API-equivalent, for comparing runs.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

# $ per million tokens: input, output, cache read. Cache writes are 1.25x input
# (5-minute) and 2x input (1-hour). Fast mode doubles the rates.
# Checked 2026-11-12 against the Claude API pricing (models cached 2026-11-03).
PRICES_CHECKED = "2026-11-12"
PRICES = {
    "claude-fable-5-2": (8.00, 40.00, 0.20),
    "claude-mythos-5-2": (8.00, 40.00, 0.20),
    "claude-fable-5-1": (10.00, 50.00, 0.25),
    "claude-mythos-5-1": (10.00, 50.00, 0.25),
    "claude-fable-5": (10.00, 50.00, 1.00),
    "claude-mythos-5": (10.00, 50.00, 1.00),
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-opus-5": (5.00, 25.00, 0.50),
    "claude-opus-4-8": (5.00, 25.00, 0.50),
    "claude-opus-4-7": (5.00, 25.00, 0.50),
    "claude-opus-4-6": (5.00, 25.00, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-sonnet-5": (2.00, 10.00, 0.20),
    "claude-sonnet-4-6": (3.00, 15.00, 0.30),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-haiku-4-5": (1.00, 5.00, 0.10),
}

CONTEXT_WARN = 300_000   # the size the owner objects to; marked in the agent list

REL = r"v\d+(?:\.\d+)+"             # a release in prose is dotted: v3.3 ("plan v12" is a plan version)
BREL = r"v\d+(?:\.\d+)*"            # in a branch or worktree name it may not be: v1-w2
CHUNK_HEAD_RE = re.compile(r"Chunk mode\.\s+(?:Build|Resume)\s+chunk\s+(\d+[a-z]?)\b.*?\bof\s+(" + REL + r")\W{1,3}wave\s+(\d+)", re.S)
CHUNK_BRANCH_RE = re.compile(r"\b(" + BREL + r")-c(\d+[a-z]?)\b")
WAVE_BRANCH_RE = re.compile(r"\b(" + BREL + r")-w(\d+)\b")
WAVE_TEXT_RE = re.compile(r"\b(" + REL + r")\W{1,3}wave\s+(\d+)\b", re.I)
WAVE_ONLY_RE = re.compile(r"\bwave\s+(\d+)\b", re.I)
REL_RE = re.compile(r"\b(" + REL + r")\b")
BRIEF_HEAD = 700          # characters of a brief read for its tags


# ---------------------------------------------------------------- transcripts

def project_dirs(repo):
    """The transcript directories of a repo and of its worktrees' sessions."""
    base = os.path.expanduser("~/.claude/projects")
    key = re.sub(r"[^A-Za-z0-9]", "-", repo)
    dirs = [os.path.join(base, key)] + sorted(glob.glob(os.path.join(base, key + "-*")))
    return [d for d in dirs if os.path.isdir(d)]


def repo_root(start):
    try:
        common = subprocess.run(["git", "-C", start, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.path.abspath(start)
    return os.path.dirname(common) if common.endswith("/.git") else os.path.abspath(start)


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def result_size(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(b.get("text", "")) for b in content if isinstance(b, dict))
    return 0


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


class Agent:
    def __init__(self, path, session, meta):
        self.path = path
        self.session = session
        self.meta = meta or {}
        self.role = self.meta.get("agentType") or "driver"
        self.depth = self.meta.get("spawnDepth", 0)
        self.description = self.meta.get("description", "")
        self.parent = None
        self.brief = ""
        self.turns = {}          # message id -> (timestamp, model, usage)
        self.calls = {}          # tool-use id -> (name, input, timestamp)
        self.results = {}        # tool-use id -> result size
        self.tag = None          # (release, wave or None, chunk or None)
        self.top = self          # its depth-1 ancestor (itself for the driver and depth 1)

    @property
    def is_driver(self):
        return self.depth == 0


def load(dirs):
    agents = []
    owner_of_call = {}
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
            agents.append(read_agent(f, os.path.basename(f)[:-6], None))
        for f in sorted(glob.glob(os.path.join(d, "*", "subagents", "*.jsonl"))):
            m = f[:-6] + ".meta.json"
            meta = json.load(open(m)) if os.path.exists(m) else {"agentType": "unknown", "spawnDepth": 1}
            agents.append(read_agent(f, f.split(os.sep)[-3], meta))
    for a in agents:
        for cid in a.calls:
            owner_of_call[cid] = a
    for a in agents:
        if not a.is_driver:
            a.parent = owner_of_call.get(a.meta.get("toolUseId"))
    for a in agents:
        t = a
        while t.parent is not None and not t.parent.is_driver and t.depth > 1:
            t = t.parent
        a.top = t
    return agents


def read_agent(path, session, meta):
    a = Agent(path, session, meta)
    with open(path) as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            kind = d.get("type")
            if kind == "user":
                msg = d.get("message") or {}
                content = msg.get("content")
                if not a.brief and meta is not None and not d.get("isMeta"):
                    a.brief = text_of(content)
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            a.results[b.get("tool_use_id")] = result_size(b.get("content"))
            elif kind == "assistant":
                msg = d.get("message") or {}
                model = msg.get("model")
                if model and model != "<synthetic>" and msg.get("usage"):
                    a.turns[msg.get("id") or d.get("uuid")] = (d.get("timestamp"), model, msg["usage"])
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        a.calls.setdefault(b["id"], (b.get("name", ""), b.get("input") or {}, d.get("timestamp")))
    return a


# ---------------------------------------------------------------- attribution

BRIEF_FILE_RE = re.compile(r"brief is in\s+`?(/\S+?\.md)`?[\s.,]")
DESC_CHUNK_RE = re.compile(r"\b(" + REL + r")\s+chunk\s+(\d+[a-z]?)\b", re.I)
LOOSE_CHUNK_RE = re.compile(r"^Chunk mode\b[^\n]*?\bchunk\W+(\d+[a-z]?)\b", re.I)


def brief_text(a):
    """The brief, or the head of the file it points to when the driver kept it in one."""
    m = BRIEF_FILE_RE.search(a.brief[:BRIEF_HEAD])
    if m and os.path.exists(m.group(1)):
        try:
            with open(m.group(1)) as fh:
                return fh.read(BRIEF_HEAD) + "\n" + a.brief
        except OSError:
            pass
    return a.brief


def tag_brief(brief, description=""):
    """(release, wave, chunk) from a brief's opening, any part None."""
    head = brief[:BRIEF_HEAD]
    m = CHUNK_HEAD_RE.search(head)
    if m:
        return (m.group(2), int(m.group(3)), m.group(1))
    rel = wave = chunk = None
    m = LOOSE_CHUNK_RE.search(head)
    if m:
        chunk = m.group(1)
    m = CHUNK_BRANCH_RE.search(head) or DESC_CHUNK_RE.search(description)
    if m:
        rel, chunk = m.group(1), chunk or m.group(2)
    if rel is None and chunk is None:
        m = WAVE_BRANCH_RE.search(description) or WAVE_TEXT_RE.search(description)
        if not m:
            w, r = WAVE_ONLY_RE.search(description), REL_RE.search(description)
            if w and r:
                rel, wave = r.group(1), int(w.group(1))
        else:
            rel, wave = m.group(1), int(m.group(2))
    m = WAVE_BRANCH_RE.search(head) or WAVE_TEXT_RE.search(head)
    if m:
        rel, wave = rel or m.group(1), int(m.group(2))
    elif rel is None or wave is None:
        rels = set(REL_RE.findall(head))
        w = WAVE_ONLY_RE.search(head)
        if w and len(rels) == 1:
            rel, wave = rel or rels.pop(), int(w.group(1))
    if rel is None:
        return None
    return (rel, wave, chunk)


def attribute(agents, repo):
    for a in agents:
        if a.depth == 1:
            a.tag = tag_brief(brief_text(a), a.description)
    # A chunk tagged without its wave takes the wave other briefs give that chunk,
    # else the chunk's Wave field in the plan.
    known = defaultdict(lambda: defaultdict(int))
    for a in agents:
        if a.depth == 1 and a.tag and a.tag[1] is not None and a.tag[2]:
            known[(a.tag[0], chunk_base(a.tag[2]))][a.tag[1]] += 1
    for a in agents:
        if a.depth == 1 and a.tag and a.tag[1] is None and a.tag[2]:
            votes = known.get((a.tag[0], chunk_base(a.tag[2])))
            wave = max(votes, key=votes.get) if votes else plan_wave(repo, a.tag[0], a.tag[2])
            a.tag = (a.tag[0], wave, a.tag[2])
    for a in agents:
        if a.depth > 1:
            a.tag = a.top.tag or tag_brief(a.brief, a.description)


_plan_waves = {}


def plan_wave(repo, release, chunk):
    """The chunk's Wave field, from the live plan when it is this release's."""
    key = (release, chunk_base(chunk))
    if key not in _plan_waves:
        wave = None
        try:
            r = subprocess.run(["doc-get", "chunk", chunk_base(chunk), "-f", "wave"], cwd=repo,
                               capture_output=True, text=True, timeout=20)
            head, _, body = r.stdout.partition("\n")
            m = re.search(r"Wave:\s*(\d+)", body)
            if r.returncode == 0 and f"build-plan-{release}." in head and m:
                wave = int(m.group(1))
        except (OSError, subprocess.SubprocessError):
            pass
        _plan_waves[key] = wave
    return _plan_waves[key]


def chunk_base(c):
    return re.match(r"\d+", c).group(0) if c else None


def chunk_matches(tag_chunk, wanted):
    if tag_chunk is None:
        return False
    return tag_chunk == wanted or (wanted.isdigit() and chunk_base(tag_chunk) == wanted)


def latest_release(agents):
    seen = [(min_time(a), a.tag[0]) for a in agents if a.tag and a.turns]
    seen = [s for s in seen if s[0]]
    return max(seen)[1] if seen else None


def min_time(a):
    times = [t for t, _, _ in a.turns.values() if t]
    return min(times) if times else None


def max_time(a):
    times = [t for t, _, _ in a.turns.values() if t]
    return max(times) if times else None


def merge_time(repo, release, wave):
    branch = f"{release}-w{wave}"
    try:
        out = subprocess.run(["git", "-C", repo, "log", "main", "--merges", "--format=%cI",
                              "--grep", f"^Merge {re.escape(branch)}\\b", "-1"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return ts(out) if out else None


# ---------------------------------------------------------------- activity

def area_of(path):
    p = path or ""
    if re.search(r"build-plan|wave-log", p):
        return "plan"
    if re.search(r"(^|/)specs/", p):
        return "spec"
    if re.search(r"(^|/)ui_ux/", p):
        return "design"
    if re.search(r"\.atom\.md|(^|/)intent/", p):
        return "intent"
    if re.search(r"\.md\b|data-register/|\.tech\b|SECURITY_TODO", p):
        return "other docs"
    if re.search(r"(^|/)(src|tests?|e2e|scripts|public)/|\.(ts|tsx|js|mjs|vue|css|json|html|py)\b", p):
        return "source"
    return None


CHECK_RE = re.compile(r"\b(vitest|playwright|vue-tsc|tsc|eslint|stylelint|prettier|pytest)\b|"
                      r"\b(npm|pnpm|yarn|npx|bun)\s+(run\s+)?[\w:-]*(test|lint|build|check|typecheck|e2e|bench|measure)")
WRITE_SHELL_RE = re.compile(r"(cat|tee)\s+>{1,2}?\s*\S+|>\s*\S+\.\w+|\bsed\s+-i\b|\bperl\s+-p?i\b|python3?\s+-\s*<<")
SHELL_PATH_RE = re.compile(r"[\w./~-]*(?:/[\w.@-]+)+|\b[\w.-]+\.(?:md|ts|vue|js|css|json|py)\b")


def strip_cd(cmd):
    return re.sub(r"^\s*(cd\s+\S+\s*(&&|;)\s*)+", "", cmd.strip())


def activity(name, inp):
    """(activity, is_write) for one tool call."""
    if name in ("Agent", "Task", "SendMessage", "TaskCreate", "TaskUpdate", "TaskGet", "TaskList", "TaskStop", "Workflow"):
        return ("dispatch", False)
    if name in ("Read", "Edit", "Write", "NotebookEdit", "MultiEdit"):
        area = area_of(inp.get("file_path") or inp.get("notebook_path", "")) or "other files"
        return (area, name != "Read")
    if name in ("Grep", "Glob"):
        area = area_of(" ".join(str(inp.get(k, "")) for k in ("path", "glob", "pattern"))) or "source"
        return (area, False)
    if name == "Skill":
        return ("skills", False)
    if name != "Bash":
        return ("other tools", False)
    cmd = strip_cd(inp.get("command", ""))
    first = cmd.split()[0] if cmd.split() else ""
    if first in ("doc-get", "doc-get.py") or cmd.startswith("doc-get "):
        return ("doc-get", False)
    if first == "atd":
        return ("intent", False)
    if first == "git" or first == "gh":
        return ("git", False)
    if CHECK_RE.search(cmd):
        return ("checks", False)
    write = bool(WRITE_SHELL_RE.search(cmd))
    areas = [area_of(p) for p in SHELL_PATH_RE.findall(cmd)]
    areas = [x for x in areas if x]
    if areas:
        for pref in ("plan", "spec", "design", "intent", "other docs", "source"):
            if pref in areas:
                return (pref, write)
    return ("shell other", write)


ACTIVITY_ORDER = ["dispatch", "doc-get", "plan", "spec", "design", "intent", "other docs",
                  "source", "checks", "git", "shell other", "skills", "other files", "other tools"]


# ---------------------------------------------------------------- figures

class Sum:
    def __init__(self):
        self.agents = 0
        self.turns = 0
        self.calls = 0
        self.fresh = self.write5 = self.write1h = self.read = self.out = 0
        self.cost = 0.0
        self.unpriced = set()
        self.max_ctx = 0
        self.max_ctx_agent = None
        self.first = self.last = None

    def add_turn(self, when, model, u, agent):
        self.turns += 1
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
        wtot = u.get("cache_creation_input_tokens", 0) or 0
        w5 = cc.get("ephemeral_5m_input_tokens", wtot - w1h) if cc else wtot
        fresh = u.get("input_tokens", 0) or 0
        rd = u.get("cache_read_input_tokens", 0) or 0
        out = u.get("output_tokens", 0) or 0
        self.fresh += fresh
        self.write5 += w5
        self.write1h += w1h
        self.read += rd
        self.out += out
        price = PRICES.get(model)
        if price is None:
            self.unpriced.add(model)
        else:
            pin, pout, pread = price
            mult = 2.0 if u.get("speed") == "fast" else 1.0
            self.cost += mult * (fresh * pin + w5 * pin * 1.25 + w1h * pin * 2 + rd * pread + out * pout) / 1e6
        ctx = fresh + wtot + rd
        if ctx > self.max_ctx:
            self.max_ctx, self.max_ctx_agent = ctx, agent
        t = ts(when)
        if t:
            self.first = t if self.first is None or t < self.first else self.first
            self.last = t if self.last is None or t > self.last else self.last

    @property
    def tokens_in(self):
        return self.fresh + self.write5 + self.write1h + self.read


def measure(selection):
    """selection: list of (agent, turn filter or None). Returns the figures."""
    total = Sum()
    by_role = defaultdict(Sum)
    by_chunk = defaultdict(Sum)
    by_agent = []
    acts = defaultdict(lambda: [0, 0, 0])   # calls, writes, result bytes
    for a, keep in selection:
        s = Sum()
        kept_turns = [(k, v) for k, v in a.turns.items() if keep is None or keep(v[0])]
        if not kept_turns:
            continue
        for _, (when, model, u) in kept_turns:
            for target in (total, by_role[role_label(a)], s):
                target.add_turn(when, model, u, a)
            if a.tag and a.tag[2]:
                by_chunk[a.tag[2]].add_turn(when, model, u, a)
        calls = a.calls if keep is None else {k: v for k, v in a.calls.items() if keep(v[2])}
        n = len(calls)
        s.calls = n
        total.calls += n
        by_role[role_label(a)].calls += n
        if a.tag and a.tag[2]:
            by_chunk[a.tag[2]].calls += n
        for cid, (name, inp, _) in calls.items():
            act, w = activity(name, inp)
            acts[act][0] += 1
            acts[act][1] += int(w)
            acts[act][2] += a.results.get(cid, 0)
        for target in (total, by_role[role_label(a)], s):
            target.agents += 1
        if a.tag and a.tag[2]:
            by_chunk[a.tag[2]].agents += 1
        by_agent.append((a, s))
    return total, by_role, by_chunk, acts, by_agent


def role_label(a):
    return "driver (top level)" if a.is_driver else a.role


# ---------------------------------------------------------------- selection

def select_chunk(agents, release, chunk):
    owners = [a for a in agents if a.depth == 1 and a.tag and a.tag[0] == release and chunk_matches(a.tag[2], chunk)]
    tops = set(id(a) for a in owners)
    chosen = [a for a in agents if not a.is_driver and id(a.top) in tops]
    return [(a, None) for a in chosen], owners


def select_wave(agents, release, wave, repo):
    tagged_tops = [a for a in agents if a.depth == 1 and a.tag and a.tag[0] == release and a.tag[1] == wave]
    if not tagged_tops:
        return [], [], None, None, [], []
    tops = set(id(a) for a in tagged_tops)
    sessions = set(a.session for a in tagged_tops)
    starts = [min_time(a) for a in tagged_tops if min_time(a)]
    ends = [max_time(a) for a in tagged_tops if max_time(a)]
    lo = ts(min(starts))
    hi = merge_time(repo, release, wave) or ts(max(ends))
    within = lambda when: when is not None and lo <= ts(when) <= hi
    # The driver's own turns count from the previous wave's merge (starting the wave:
    # reading the plan, cutting the branch), or from the first tagged agent.
    prev = merge_time(repo, release, wave - 1)
    d_lo = prev if prev and prev < lo else lo
    d_within = lambda when: when is not None and d_lo <= ts(when) <= hi
    selection = []
    untagged = []
    others = []
    for a in agents:
        if a.is_driver:
            if not any(d_within(t) for t, _, _ in a.turns.values()):
                continue
            if a.session in sessions:
                selection.append((a, d_within))
            else:
                others.append(a)
            continue
        if id(a.top) in tops:
            selection.append((a, None))
        elif a.top.tag is None and a.top.session in sessions and min_time(a.top) and within(min_time(a.top)):
            selection.append((a, None))
            if a.depth == 1:
                untagged.append(a)
    return selection, tagged_tops, lo, hi, untagged, others


# ---------------------------------------------------------------- output

def k(n):
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}k"
    return str(n)


def money(x):
    return f"${x:,.2f}"


def span(lo, hi):
    if not lo or not hi:
        return "-"
    secs = int((hi - lo).total_seconds())
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    dur = (f"{d}d " if d else "") + f"{h}h{m:02d}"
    return f"{lo.astimezone():%Y-%m-%d %H:%M} → {hi.astimezone():%Y-%m-%d %H:%M} ({dur})"


def table(headers, rows, md):
    if md:
        out = ["| " + " | ".join(headers) + " |",
               "|" + "|".join("---" if i == 0 else "---:" for i in range(len(headers))) + "|"]
        out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
        return "\n".join(out)
    widths = [max(len(str(x)) for x in [h] + [r[i] for r in rows]) for i, h in enumerate(headers)]
    fmt = lambda r: "  ".join(str(c).ljust(widths[i]) if i == 0 else str(c).rjust(widths[i]) for i, c in enumerate(r))
    return "\n".join([fmt(headers), fmt(["-" * w for w in widths])] + [fmt(r) for r in rows])


def describe(a):
    if a.is_driver:
        return f"driver session {a.session[:8]}"
    d = a.description or a.brief.split("\n")[0]
    return (d[:60] + "…") if len(d) > 61 else d


def report(title, total, by_role, by_chunk, acts, by_agent, args, extra_lines=()):
    md = args.md
    pct = lambda x: f"{100 * x / total.cost:.0f}%" if total.cost else "-"
    lines = []
    h = "### " if md else ""
    lines.append(f"{h}{title}")
    lines.append("")
    lines.append(f"- Time: {span(total.first, total.last)}")
    lines.append(f"- Agents: {total.agents} · tool calls: {total.calls:,} · model turns: {total.turns:,}")
    lines.append(f"- Tokens in: {k(total.tokens_in)} (fresh {k(total.fresh)}, cache write {k(total.write5 + total.write1h)}, "
                 f"cache read {k(total.read)}) · out: {k(total.out)}")
    if total.max_ctx_agent is not None:
        lines.append(f"- Max context: {k(total.max_ctx)} ({role_label(total.max_ctx_agent)}: {describe(total.max_ctx_agent)})")
    lines.append(f"- Cost: {money(total.cost)} at API list prices (checked {PRICES_CHECKED})"
                 + (f"; not priced: {', '.join(sorted(total.unpriced))}" if total.unpriced else ""))
    lines.extend(extra_lines)

    rows = [[r, s.agents, f"{s.calls:,}", k(s.tokens_in), k(s.out), money(s.cost), pct(s.cost), k(s.max_ctx)]
            for r, s in sorted(by_role.items(), key=lambda x: -x[1].cost)]
    lines += ["", f"{h}By role" if md else "By role",
              table(["role", "agents", "calls", "tokens in", "out", "cost", "share", "max ctx"], rows, md)]

    if by_chunk and len(by_chunk) > 1 or (by_chunk and args.kind == "wave"):
        key = lambda c: (int(chunk_base(c)), c)
        rows = [[c, s.agents, f"{s.calls:,}", k(s.tokens_in), k(s.out), money(s.cost), pct(s.cost), k(s.max_ctx)]
                for c, s in sorted(by_chunk.items(), key=lambda x: key(x[0]))]
        rest = total.cost - sum(s.cost for s in by_chunk.values())
        rows.append(["outside chunks", "", "", "", "", money(rest), pct(rest), ""])
        lines += ["", f"{h}By chunk" if md else "By chunk",
                  table(["chunk", "agents", "calls", "tokens in", "out", "cost", "share", "max ctx"], rows, md)]

    ncalls = sum(v[0] for v in acts.values()) or 1
    rows = [[a, f"{acts[a][0]:,}", f"{100 * acts[a][0] / ncalls:.0f}%", acts[a][1] or "", k(acts[a][2])]
            for a in ACTIVITY_ORDER if a in acts]
    lines += ["", f"{h}By activity (tool calls)" if md else "By activity (tool calls)",
              table(["activity", "calls", "share", "writes", "results"], rows, md)]

    top = sorted(by_agent, key=lambda x: -x[1].max_ctx)[:args.top]
    rows = [[("! " if s.max_ctx >= CONTEXT_WARN else "") + role_label(a), describe(a), s.calls, k(s.max_ctx), money(s.cost)]
            for a, s in top]
    lines += ["", f"{h}Largest contexts" if md else "Largest contexts",
              table(["agent", "task", "calls", "max ctx", "cost"], rows, md)]
    if any(s.max_ctx >= CONTEXT_WARN for _, s in top):
        lines.append(f"(! = over {k(CONTEXT_WARN)} tokens of context)")
    return "\n".join(lines)


def one_line(total):
    return (f"{total.agents} agents, {total.calls:,} tool calls, {k(total.tokens_in)} tokens in / {k(total.out)} out, "
            f"max context {k(total.max_ctx)}, {money(total.cost)} at API prices")


def as_json(title, total, by_role, by_chunk, acts, by_agent):
    def s2d(s):
        return {"agents": s.agents, "calls": s.calls, "turns": s.turns, "tokens_fresh": s.fresh,
                "cache_write_5m": s.write5, "cache_write_1h": s.write1h, "cache_read": s.read,
                "output": s.out, "cost_usd": round(s.cost, 4), "max_context": s.max_ctx,
                "first": s.first.isoformat() if s.first else None, "last": s.last.isoformat() if s.last else None}
    return json.dumps({
        "title": title, "prices_checked": PRICES_CHECKED, "total": s2d(total),
        "by_role": {r: s2d(s) for r, s in by_role.items()},
        "by_chunk": {c: s2d(s) for c, s in by_chunk.items()},
        "by_activity": {a: {"calls": v[0], "writes": v[1], "returned_bytes": v[2]} for a, v in acts.items()},
        "agents": [{"role": role_label(a), "task": describe(a), "session": a.session, **s2d(s)} for a, s in by_agent],
    }, indent=1)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(prog="agent-stats", description=__doc__.split("\n\n")[0])
    ap.add_argument("kind", choices=["chunk", "wave", "list"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--release")
    ap.add_argument("--project", default=".")
    out = ap.add_mutually_exclusive_group()
    out.add_argument("--md", action="store_true", help="markdown tables")
    out.add_argument("--line", action="store_true", help="one line, for a chunk's Record")
    out.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=5, help="agents in the largest-contexts list")
    args = ap.parse_args()
    if args.kind != "list" and not args.id:
        ap.error(f"{args.kind} needs an id")

    repo = repo_root(args.project)
    dirs = project_dirs(repo)
    if not dirs:
        sys.exit(f"agent-stats: no Claude Code transcripts for {repo}")
    agents = load(dirs)
    attribute(agents, repo)
    release = args.release or latest_release(agents)
    if not release:
        sys.exit("agent-stats: no brief names a release; pass --release")

    if args.kind == "list":
        waves = defaultdict(set)
        for a in agents:
            if a.depth == 1 and a.tag and a.tag[0] == release:
                waves[a.tag[1]].add(a.tag[2])
        for w in sorted(waves, key=lambda x: (x is None, x or 0)):
            chunks = sorted((c for c in waves[w] if c), key=lambda c: (int(chunk_base(c)), c))
            print(f"{release} wave {w if w is not None else '?'}: chunks {', '.join(chunks) or '-'}")
        return

    if args.kind == "chunk":
        selection, owners = select_chunk(agents, release, args.id)
        if not owners:
            sys.exit(f"agent-stats: no brief for chunk {args.id} of {release} (try: agent-stats list --release {release})")
        waves = sorted(set(o.tag[1] for o in owners if o.tag[1] is not None))
        title = f"{release} chunk {args.id}" + (f" (wave {', '.join(map(str, waves))})" if waves else "")
        extra = [f"- Owners: {len(owners)} ({', '.join(describe(o) for o in owners)})"] if len(owners) > 1 else []
    else:
        selection, tagged, lo, hi, untagged, others = select_wave(agents, release, int(args.id), repo)
        if not selection:
            sys.exit(f"agent-stats: no brief names {release} wave {args.id}")
        merged = merge_time(repo, release, int(args.id))
        title = f"{release} wave {args.id}"
        extra = [f"- Ends: {'at its merge into main' if merged else 'at its last tagged agent (not merged yet)'}"]
        if untagged:
            extra.append(f"- Counted, but their brief names no wave: " + "; ".join(f"{a.role}: {describe(a)}" for a in untagged))
        if others:
            extra.append("- Not counted: other top-level sessions active in the window, with no agent of this wave: "
                         + ", ".join(a.session[:8] for a in others))

    total, by_role, by_chunk, acts, by_agent = measure(selection)
    if args.json:
        print(as_json(title, total, by_role, by_chunk, acts, by_agent))
    elif args.line:
        print(one_line(total))
    else:
        print(report(title, total, by_role, by_chunk, acts, by_agent, args, extra))


if __name__ == "__main__":
    main()
