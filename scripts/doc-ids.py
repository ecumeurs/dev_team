#!/usr/bin/env python3
"""doc-ids: the numbered IDs of the spec and UI/UX trees' registers.

The mechanical side of the ID rules in references/doc-tree-conventions.md.
`spec-writer` numbers the spec tree's decisions (D) and open questions (O),
`ux-writer` the UI/UX tree's decisions (D) and open questions (Q). An agent
asks this command for the next number instead of reading a log for it, and
checks with it that no two entries share one, inside a branch or across two
branches about to merge.

Commands:
  next      the next free ID of a register, reserved for every worktree of the repo
  lint      IDs defined twice, citations past the highest ID, stale "continues from" lines
  compare   IDs two branches or worktrees defined independently, before they merge
  renumber  give an issued ID a new number, with its citations, across one branch

A branch checked out in a worktree is read from that worktree, uncommitted
changes included (`--committed` reads the branch instead); any other branch is
read as committed. Reservations live in the repository's common git directory,
which all its worktrees share and nothing commits, so two worktrees on one
machine never get the same number. Separate clones (a cloud session) don't
share it: `compare` and `lint` catch what they collide on.

Standard library only.
"""

from __future__ import annotations

import argparse
import bisect
import contextlib
import fcntl
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Tree:
    name: str               # the qualifier used outside the tree: "spec D104", "ux Q7"
    dir: str
    kinds: dict             # kind letter -> register file stem


TREES = {
    "spec": Tree("spec", "specs", {"D": "decisions", "O": "open-questions"}),
    "ux": Tree("ux", "ui_ux", {"D": "decisions", "Q": "open-questions"}),
}

# An entry starts a line: "- **D410 (2026-10-21): …", "- **Q16 — …", "## D12 …".
# A bold range ("- **D339–D341** …") is a summary, not an entry.
DEF_RE = re.compile(r"^(?:[-*]\s+\*\*|#{1,6}\s+(?:\*\*)?)([DOQ])(\d+)(?!\w|\s*[-–—]\s*[DOQ]?\d)")
MENTION_RE = re.compile(r"(?<!\w)(?:((?i:spec|ux))\s+)?([DOQ])(\d+)(?!\w)")
RANGE_RE = re.compile(r"(?<!\w)(?:((?i:spec|ux))\s+)?([DOQ])(\d+)\s*[-–—]\s*([DOQ])?(\d+)(?!\w)")
# "Numbering continues from **D410**", "New questions take IDs from **O270**"
FLOOR_RE = re.compile(r"(?i:continues from|take IDs from|next ID(?: is)?:?)\s*\**\s*([DOQ])(\d+)")
# A line that declares numbers instead of citing entries.
UNUSED_RE = re.compile(r"(?i)\b(?:unused|never used|not used|reserved|(?:stays?|left|kept|next) free"
                       r"|continues from|take IDs from)\b")
# What may sit between two IDs of one list, so a qualifier carries over: "spec D411, D412", "spec D400–D408".
LIST_SEP_RE = re.compile(r"\s*(?:,\s*(?:and\s+|or\s+)?|and\s+|or\s+|[-–—/]\s*)")
DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})")
MAX_FILE = 2_000_000


def die(msg: str, code: int = 2) -> None:
    print(f"doc-ids: {msg}", file=sys.stderr)
    sys.exit(code)


def git(args: list[str], cwd: Path, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        die(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout if r.returncode == 0 else ""


def toplevel(path: Path) -> Path:
    out = git(["rev-parse", "--show-toplevel"], path, check=False).strip()
    if not out:
        die(f"{path} is not inside a git repository")
    return Path(out)


def parse_id(text: str) -> tuple[str, int]:
    m = re.fullmatch(r"([DOQ])(\d+)", text.strip())
    if not m:
        die(f"{text!r} is not an ID like D339, O270 or Q88")
    return m.group(1), int(m.group(2))


def check_kind(tree: Tree, kind: str) -> None:
    if kind not in tree.kinds:
        die(f"the {tree.name} tree has no {kind} register (it has {', '.join(tree.kinds)})")


# --- where the trees are read from -----------------------------------------

@dataclass
class Worktree:
    path: Path
    branch: str | None


def worktrees(repo: Path) -> list[Worktree]:
    out, cur = [], None
    for line in git(["worktree", "list", "--porcelain"], repo).splitlines():
        if line.startswith("worktree "):
            cur = Worktree(Path(line[9:]), None)
            out.append(cur)
        elif line.startswith("branch refs/heads/") and cur:
            cur.branch = line[len("branch refs/heads/"):]
    return [w for w in out if w.path.is_dir()]


class FsSource:
    """A worktree, read from disk: uncommitted changes included."""

    def __init__(self, root: Path):
        self.root = root
        self.repo = root
        self.head = git(["rev-parse", "--verify", "--quiet", "HEAD"], root, check=False).strip() or None
        self.branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root, check=False).strip() or "?"
        if self.branch == "HEAD":
            self.branch = (self.head or "?")[:8]
        self.label = f"{root} [{self.branch}]"

    def tree_files(self, tree: Tree) -> list[str]:
        out = []
        for dirpath, dirnames, filenames in os.walk(self.root / tree.dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            out += [Path(dirpath, f).relative_to(self.root).as_posix() for f in filenames if f.endswith(".md")]
        return sorted(out)

    def repo_files(self) -> list[str]:
        out = git(["ls-files", "-z", "-co", "--exclude-standard"], self.root)
        return sorted({p for p in out.split("\0") if p})

    def read_many(self, paths: list[str]) -> dict[str, str]:
        res = {}
        for p in paths:
            f = self.root / p
            try:
                if f.is_symlink() or not f.is_file() or f.stat().st_size > MAX_FILE:
                    continue
                data = f.read_bytes()
            except OSError:
                continue
            if b"\0" not in data[:8192]:
                res[p] = data.decode("utf-8", "replace")
        return res


class RefSource:
    """A commit, read from the object store: what is committed only."""

    def __init__(self, repo: Path, ref: str, label: str | None = None):
        self.repo = repo
        self.head = git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], repo, check=False).strip()
        if not self.head:
            die(f"{ref!r} is neither a directory nor a commit of {repo}")
        self.branch = ref
        self.label = label or ref

    def tree_files(self, tree: Tree) -> list[str]:
        out = git(["ls-tree", "-r", "-z", "--name-only", self.head, "--", tree.dir], self.repo)
        return sorted(p for p in out.split("\0") if p.endswith(".md"))

    def read_many(self, paths: list[str]) -> dict[str, str]:
        if not paths:
            return {}
        inp = "".join(f"{self.head}:{p}\n" for p in paths).encode()
        out = subprocess.run(["git", "cat-file", "--batch"], cwd=self.repo, input=inp,
                             capture_output=True).stdout
        res, pos = {}, 0
        for p in paths:
            nl = out.index(b"\n", pos)
            header = out[pos:nl].split()
            pos = nl + 1
            if header and header[-1] != b"missing" and len(header) == 3 and header[1] == b"blob":
                size = int(header[2])
                res[p] = out[pos:pos + size].decode("utf-8", "replace")
                pos += size + 1
        return res


def resolve(repo: Path, arg: str, committed: bool):
    p = Path(arg).expanduser()
    if p.is_dir():
        return FsSource(toplevel(p))
    if not committed:
        for wt in worktrees(repo):
            if wt.branch == arg:
                return FsSource(wt.path)
    return RefSource(repo, arg)


# --- reading a tree ----------------------------------------------------------

def context(path: str) -> str | None:
    for name, t in TREES.items():
        if path.startswith(t.dir + "/"):
            return name
    return None


def owner(qual: str | None, kind: str, ctx: str | None) -> str | None:
    """The tree an ID belongs to, or None for a bare D outside both trees."""
    if qual:
        t = qual.lower()
        return t if kind in TREES[t].kinds else None
    if ctx and kind in TREES[ctx].kinds:
        return ctx
    owners = [n for n, t in TREES.items() if kind in t.kinds]
    return owners[0] if len(owners) == 1 and ctx else None


@dataclass
class Mention:
    owner: str | None
    qual: str | None
    kind: str
    n: int
    start: int          # offset of the kind letter
    end: int
    line: int
    text: str           # the whole line
    col: int


@dataclass
class Range:
    owner: str | None
    kind: str
    a: int
    b: int
    start: int
    end: int
    line: int
    text: str
    col: int


def parse_text(text: str, path: str):
    """Every ID mention and ID range in a file."""
    ctx = context(path)
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    lines = text.split("\n")

    def at(pos):
        i = bisect.bisect_right(starts, pos) - 1
        return i + 1, lines[i], pos - starts[i]

    mentions, prev = [], None
    for m in MENTION_RE.finditer(text):
        qual, kind, n = m.group(1), m.group(2), int(m.group(3))
        if not qual and prev and prev.qual and prev.kind == kind and LIST_SEP_RE.fullmatch(text, prev.end, m.start()):
            qual = prev.qual
        line, ltext, col = at(m.start(2))
        prev = Mention(owner(qual, kind, ctx), qual, kind, n, m.start(2), m.end(), line, ltext, col)
        mentions.append(prev)
    ranges = []
    for m in RANGE_RE.finditer(text):
        qual, kind, a, kind2, b = m.group(1), m.group(2), int(m.group(3)), m.group(4), int(m.group(5))
        if (kind2 and kind2 != kind) or a >= b:
            continue
        line, ltext, col = at(m.start(2))
        ranges.append(Range(owner(qual, kind, ctx), kind, a, b, m.start(), m.end(), line, ltext, col))
    return mentions, ranges


@dataclass
class Entry:
    path: str
    line: int
    first: str          # its first line, as written
    text: str           # the whole entry, whitespace collapsed

    @property
    def where(self) -> str:
        return f"{self.path}:{self.line}"

    @property
    def date(self) -> str:
        m = DATE_RE.search(self.first)
        return m.group(1) if m else ""


@dataclass
class Index:
    tree: Tree
    defs: dict = field(default_factory=dict)        # (kind, n) -> [Entry]
    cited: dict = field(default_factory=dict)       # kind -> highest number cited in the trees
    floors: dict = field(default_factory=dict)      # kind -> (n, "path:line")
    citations: list = field(default_factory=list)  # [Mention], definitions excluded

    def max_def(self, kind: str) -> int:
        return max((n for k, n in self.defs if k == kind), default=0)

    def highest(self, kind: str) -> int:
        floor = self.floors.get(kind, (1, ""))[0]
        return max(self.max_def(kind), self.cited.get(kind, 0), floor - 1)


def register_kind(tree: Tree, path: str) -> str | None:
    p = Path(path)
    if not (p.parent.as_posix() == tree.dir or path.startswith(f"{tree.dir}/archive/")):
        return None
    for kind, stem in tree.kinds.items():
        if p.name == f"{stem}.md" or p.name.startswith(f"{stem}-"):
            return kind
    return None


def entry_text(lines: list[str], i: int) -> str:
    j = i + 1
    while j < len(lines) and (not lines[j].strip() or lines[j][0].isspace()):
        j += 1
    return " ".join(" ".join(lines[i:j]).split())


def scan(source) -> dict[str, Index]:
    """Both trees' definitions, citations and "continues from" lines."""
    idx = {name: Index(t) for name, t in TREES.items()}
    paths = [p for t in TREES.values() for p in source.tree_files(t)]
    for path, text in source.read_many(paths).items():
        ctx = context(path)
        tree = TREES[ctx]
        lines = text.split("\n")
        rk = register_kind(tree, path)
        def_lines, floor_spans = set(), []
        if rk:
            for i, line in enumerate(lines):
                m = DEF_RE.match(line)
                if m and m.group(1) == rk:
                    idx[ctx].defs.setdefault((rk, int(m.group(2))), []).append(
                        Entry(path, i + 1, line, entry_text(lines, i)))
                    def_lines.add(i + 1)
            if path == f"{tree.dir}/{tree.kinds[rk]}.md":
                for m in FLOOR_RE.finditer(text):
                    floor_spans.append((m.start(1), m.end()))
                    if m.group(1) == rk:
                        line = text.count("\n", 0, m.start()) + 1
                        n = int(m.group(2))
                        if n >= idx[ctx].floors.get(rk, (0, ""))[0]:
                            idx[ctx].floors[rk] = (n, f"{path}:{line}")
        mentions, _ = parse_text(text, path)
        for mn in mentions:
            if mn.owner is None or any(a <= mn.start < b for a, b in floor_spans):
                continue
            if mn.line in def_lines and mn.text.lstrip("-*# ").startswith(f"{mn.kind}{mn.n}"):
                continue
            idx[mn.owner].citations.append((path, mn))
    for name, ix in idx.items():
        for _, mn in ix.citations:
            key = (mn.kind, mn.n)
            # A bare number only the other tree defines is that tree's ID, cited unqualified (lint says so).
            if not mn.qual and key not in ix.defs and any(key in idx[o].defs for o in idx if o != name):
                continue
            ix.cited[mn.kind] = max(ix.cited.get(mn.kind, 0), mn.n)
    return idx


def snippet(line: str, col: int, width: int = 96) -> str:
    if len(line) <= width:
        return line.strip()
    a = max(0, col - width // 3)
    return ("…" if a else "") + line[a:a + width].strip() + ("…" if a + width < len(line) else "")


# --- reservations ------------------------------------------------------------

class Reservations:
    def __init__(self, repo: Path):
        common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], repo).strip()
        self.dir = Path(common) / "doc-ids"

    @contextlib.contextmanager
    def locked(self):
        self.dir.mkdir(exist_ok=True)
        with open(self.dir / ".lock", "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield

    def get(self, tree: str, kind: str) -> int:
        try:
            return int((self.dir / f"{tree}-{kind}").read_text().strip() or 0)
        except (OSError, ValueError):
            return 0

    def raise_to(self, tree: str, kind: str, n: int) -> None:
        if n > self.get(tree, kind):
            (self.dir / f"{tree}-{kind}").write_text(f"{n}\n")


def highest_everywhere(repo: Path, tree: Tree, kind: str, against: list[str]) -> list[tuple[str, int]]:
    """The highest number each place has used: this worktree, every other one, --against refs."""
    here = toplevel(repo)
    sources = [FsSource(here)]
    sources += [FsSource(w.path) for w in worktrees(here) if w.path.resolve() != here.resolve()]
    sources += [RefSource(here, r) for r in against]
    return [(s.label, scan(s)[tree.name].highest(kind)) for s in sources]


def allocate(repo: Path, tree: Tree, kind: str, against: list[str], count: int, reserve: bool):
    res = Reservations(repo)
    with res.locked() if reserve else contextlib.nullcontext():
        seen = highest_everywhere(repo, tree, kind, against)
        reserved = res.get(tree.name, kind)
        first = max([reserved] + [n for _, n in seen]) + 1
        if reserve:
            res.raise_to(tree.name, kind, first + count - 1)
    return first, seen + [("reserved in this repository", reserved)]


# --- next --------------------------------------------------------------------

def cmd_next(args) -> int:
    tree = TREES[args.tree]
    kind = args.kind.upper()
    check_kind(tree, kind)
    first, seen = allocate(args.repo, tree, kind, args.against, args.count, not args.peek)
    for n in range(first, first + args.count):
        print(f"{kind}{n}")
    if args.explain:
        for label, n in seen:
            print(f"  highest {kind} used: {kind}{n}  ({label})" if n else f"  none used  ({label})",
                  file=sys.stderr)
        print("  peeked, nothing reserved" if args.peek else "  reserved", file=sys.stderr)
    return 0


# --- lint --------------------------------------------------------------------

def main_branch(repo: Path, given: str | None) -> str | None:
    for b in ([given] if given else ["main", "master"]):
        if git(["rev-parse", "--verify", "--quiet", f"refs/heads/{b}"], repo, check=False).strip():
            return b
    return None


def origin(repo: Path, e: Entry, main: str | None) -> tuple[str, tuple]:
    """Who last wrote an entry's first line, and a sort key: on main, then oldest, keeps the ID."""
    out = git(["blame", "--porcelain", "-L", f"{e.line},{e.line}", "--", e.path], repo, check=False)
    if not out:
        return "uncommitted (untracked file)", (2, 0)
    sha = out.split()[0]
    if set(sha) == {"0"}:
        return "uncommitted", (2, 0)
    info = dict(l.split(" ", 1) for l in out.splitlines()[1:] if " " in l and not l.startswith("\t"))
    t = int(info.get("author-time", "0"))
    date = git(["log", "-1", "--format=%ad", "--date=short", sha], repo).strip()
    on_main = bool(main) and subprocess.run(["git", "merge-base", "--is-ancestor", sha, main],
                                            cwd=repo).returncode == 0
    branches = git(["branch", "--format=%(refname:short)", "--contains", sha], repo).split()
    where = f"on {main}" if on_main else ("on " + ", ".join(branches[:3]) if branches else "on no branch")
    return f"{sha[:8]} {date} \"{info.get('summary', '')}\", {where}", (0 if on_main else 1, t)


def cmd_lint(args) -> int:
    src = FsSource(toplevel(args.repo))
    idx = scan(src)
    main = main_branch(src.root, args.main)
    errors = warnings = 0
    for name in args.tree:
        if name not in TREES:
            die(f"unknown tree {name!r} (spec, ux)")
    for name in args.tree or list(TREES):
        ix, tree = idx[name], TREES[name]
        if not (src.root / tree.dir).is_dir():
            continue
        for (kind, n), entries in sorted(ix.defs.items()):
            if len(entries) < 2:
                continue
            errors += 1
            print(f"ERROR {name} {kind}{n} is defined {len(entries)} times:")
            ranked = []
            for i, e in enumerate(entries, 1):
                who, key = origin(src.root, e, main)
                ranked.append((key, i, e))
                print(f"  [{i}] {e.where}{'  ' + e.date if e.date else ''}")
                print(f"      {snippet(e.first, 0)}")
                print(f"      last written by {who}")
            cites = [(p, m) for p, m in ix.citations if (m.kind, m.n) == (kind, n)]
            if cites:
                print(f"  Cited {len(cites)} times in the trees; which entry each means is not recorded:")
                for p, m in cites[:25]:
                    print(f"      {p}:{m.line}: {snippet(m.text, m.col)}")
                if len(cites) > 25:
                    print(f"      … {len(cites) - 25} more")
            ranked.sort(key=lambda r: (r[0], r[1]))
            keep = ranked[0][1]
            print(f"  Suggested: [{keep}] keeps {kind}{n} ({'on ' + main if ranked[0][0][0] == 0 else 'written first'}).")
            for _, i, e in ranked[1:]:
                print(f"    [{i}]: doc-ids renumber {name} {kind}{n} --def {e.where}")
            print("    The dry run lists every citation; pass --take FILE[:LINE] for those that mean the renumbered one.")
        for kind, (n, where) in sorted(ix.floors.items()):
            top = ix.max_def(kind)
            if n <= top:
                warnings += 1
                print(f"WARN  {where}: says new {name} IDs start at {kind}{n}, but {kind}{top} is already "
                      f"defined. Take numbers from `doc-ids next {name} {kind}`.")
        dangling = {}
        for p, m in ix.citations:
            if m.n > ix.max_def(m.kind) and not UNUSED_RE.search(m.text):
                dangling.setdefault((m.kind, m.n), []).append(f"{p}:{m.line}")
        for (kind, n), wheres in sorted(dangling.items()):
            warnings += 1
            other = [o for o in TREES if o != name and (kind, n) in idx[o].defs]
            hint = f" The {other[0]} tree defines it: qualify it as `{other[0]} {kind}{n}`." if other else ""
            print(f"WARN  {name} {kind}{n} is cited but defined nowhere (highest is {kind}{ix.max_def(kind)}): "
                  + ", ".join(wheres[:5]) + (" …" if len(wheres) > 5 else "") + hint)
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


# --- compare -----------------------------------------------------------------

def introduced(src, base: str | None, tree: Tree, kind: str, n: int, defined_in_head: bool) -> str:
    if isinstance(src, FsSource) and not defined_in_head:
        return "uncommitted"
    rng = f"{base}..{src.head}" if base else src.head
    out = git(["log", "--reverse", "--format=%h %ad \"%s\"", "--date=short", "-S", f"**{kind}{n} ",
               rng, "--", tree.dir], src.repo, check=False).strip()
    return out.splitlines()[0] if out else "?"


def cmd_compare(args) -> int:
    repo = toplevel(args.repo)
    a = resolve(repo, args.target, args.committed)
    b = resolve(repo, args.incoming, args.committed)
    if not (a.head and b.head):
        die("both sides need at least one commit")
    base = git(["merge-base", a.head, b.head], repo, check=False).strip() or None
    ia, ib = scan(a), scan(b)
    ibase = scan(RefSource(repo, base)) if base else {n: Index(t) for n, t in TREES.items()}
    heads = {id(s): scan(RefSource(repo, s.head)) for s in (a, b) if isinstance(s, FsSource)}
    res = Reservations(repo)
    print(f"target:   {a.label}" + ("  (worktree, uncommitted changes included)" if isinstance(a, FsSource) else ""))
    print(f"incoming: {b.label}" + ("  (worktree, uncommitted changes included)" if isinstance(b, FsSource) else ""))
    print(f"base:     {base[:8] if base else 'none (unrelated histories)'}")
    collisions = warnings = 0
    for name, tree in TREES.items():
        ta, tb, tbase = ia[name], ib[name], ibase[name]
        for kind in tree.kinds:
            nxt = max(ta.highest(kind), tb.highest(kind), res.get(name, kind)) + 1
            keys = sorted(k for k in set(ta.defs) & set(tb.defs) if k[0] == kind)
            same = 0
            for key in keys:
                ea, eb = ta.defs[key][0], tb.defs[key][0]
                if key in tbase.defs:
                    eo = tbase.defs[key][0]
                    if ea.text != eo.text and eb.text != eo.text and ea.text != eb.text:
                        warnings += 1
                        print(f"WARN  {name} {key[0]}{key[1]} was edited on both sides "
                              f"({ea.where} / {eb.where}); git will ask which edit stands.")
                    continue
                if ea.text == eb.text:
                    same += 1
                    continue
                collisions += 1
                print(f"COLLISION {name} {key[0]}{key[1]}: both sides added a different entry.")
                for label, src, ix, e in (("target", a, ta, ea), ("incoming", b, tb, eb)):
                    in_head = key in heads[id(src)][name].defs if id(src) in heads else True
                    cites = sum(1 for _, m in ix.citations if (m.kind, m.n) == key)
                    print(f"  {label:8} {e.where}{'  ' + e.date if e.date else ''}, cited {cites} times in its trees")
                    print(f"           {snippet(e.first, 0)}")
                    print(f"           introduced by {introduced(src, base, tree, key[0], key[1], in_head)}")
                fix = f"doc-ids renumber {name} {key[0]}{key[1]} --to {key[0]}{nxt}"
                if isinstance(b, FsSource):
                    print(f"  Suggested: the incoming side renumbers, before the merge:\n"
                          f"    doc-ids -C {b.root} {fix}")
                else:
                    print(f"  Suggested: the incoming side renumbers, before the merge, in a worktree of {b.branch}:\n"
                          f"    {fix}")
                nxt += 1
            if same:
                print(f"note  {name}: {same} {kind} entr{'y' if same == 1 else 'ies'} added identically on both sides.")
            # The incoming side defines a number the target cites without defining:
            # a reserved or "never used" number, or a citation of an entry still on another branch.
            cited_a = {(m.kind, m.n): f"{p}:{m.line}" for p, m in ta.citations if m.kind == kind}
            for key in sorted(k for k in tb.defs if k[0] == kind and k not in ta.defs
                              and k not in tbase.defs and k in cited_a):
                warnings += 1
                print(f"WARN  {name} {key[0]}{key[1]} is new on the incoming side; the target cites it "
                      f"without defining it ({cited_a[key]}). Check the two mean the same thing.")
    print(f"{collisions} collision(s), {warnings} warning(s)")
    return 1 if collisions else 0


# --- renumber ----------------------------------------------------------------

def matches(sel: list[str], path: str, line: int) -> bool:
    return any(s == path or s == f"{path}:{line}" for s in sel)


def cmd_renumber(args) -> int:
    src = FsSource(toplevel(args.repo))
    tree = TREES[args.tree]
    kind, n = parse_id(args.id)
    check_kind(tree, kind)
    ix = scan(src)[tree.name]
    defs = ix.defs.get((kind, n))
    if not defs:
        die(f"{tree.name} {kind}{n} is defined nowhere in {tree.dir}/")
    if len(defs) > 1:
        chosen = [e for e in defs if args.defn == e.where]
        if not chosen:
            die(f"{tree.name} {kind}{n} is defined {len(defs)} times; say which one to renumber with "
                f"--def ({', '.join(e.where for e in defs)}). `doc-ids lint` shows where each came from.")
        target = chosen[0]
    else:
        target = defs[0]
    ambiguous = len(defs) > 1

    if args.to:
        k2, new = parse_id(args.to)
        if k2 != kind:
            die(f"--to must be a {kind} ID")
        others = [FsSource(w.path) for w in worktrees(src.root) if w.path.resolve() != src.root.resolve()]
        taken = [s.label for s in [src, *others, *(RefSource(src.root, r) for r in args.against)]
                 if (kind, new) in scan(s)[tree.name].defs]
        if taken:
            die(f"{kind}{new} is already defined in {', '.join(taken)}")
        if any((m.kind, m.n) == (kind, new) for _, m in ix.citations):
            die(f"{kind}{new} is already cited in {tree.dir}/ (declared unused, or reserved?); pick another")
    else:
        new, _ = allocate(src.root, tree, kind, args.against, 1, reserve=args.apply)

    plan = []   # (action, path, line, start, end, note, text, col)
    for path, text in src.read_many(src.repo_files()).items():
        if f"{kind}{n}" not in text:
            continue
        ctx = context(path)
        mentions, ranges = parse_text(text, path)
        in_range = []
        for r in ranges:
            if r.kind != kind or not (r.a <= n <= r.b):
                continue
            if r.owner not in (tree.name, None) or (r.owner is None and ctx is not None):
                continue
            in_range.append((r.start, r.end))
            plan.append(("check", path, r.line, 0, 0, f"inside the range {kind}{r.a}–{kind}{r.b}", r.text, r.col))
        for m in mentions:
            if (m.kind, m.n) != (kind, n) or any(a <= m.start < b for a, b in in_range):
                continue
            bare_outside = m.qual is None and ctx is None
            if not bare_outside and m.owner != tree.name:
                continue
            opens = DEF_RE.match(m.text)
            opens = bool(opens) and opens.start(1) == m.col
            is_def = opens and (path, m.line) == (target.path, target.line)
            other_def = opens and any((path, m.line) == (e.path, e.line) for e in defs if e is not target)
            act, note = "rewrite", ""
            if is_def:
                note = "the entry"
            elif other_def:
                act, note = "keep", "the other entry with this number"
            elif matches(args.exclude, path, m.line):
                act, note = "skip", "excluded"
            elif bare_outside and not args.bare_outside:
                act, note = "check", "unqualified, outside the trees (--bare-outside rewrites these)"
            elif ctx and "/archive/" in path and not args.include_archive:
                act, note = "check", "archived verbatim (--include-archive rewrites these)"
            elif ambiguous and not matches(args.take, path, m.line):
                act, note = "check", f"{kind}{n} has {len(defs)} entries; --take it if it means the renumbered one"
            plan.append((act, path, m.line, m.start, m.end, note, m.text, m.col))

    order = {"rewrite": 0, "check": 1, "keep": 2, "skip": 3}
    plan.sort(key=lambda p: (order[p[0]], p[1], p[2]))
    mode = "applying" if args.apply else "dry run; --apply writes it"
    print(f"renumber {tree.name} {kind}{n} -> {kind}{new}  ({target.where}; {mode})")
    for act, path, line, _, _, note, text, col in plan:
        print(f"  {act:8}{path}:{line}" + (f"  [{note}]" if note else ""))
        print(f"          {snippet(text, col)}")
    counts = {a: sum(1 for p in plan if p[0] == a) for a in order}
    print(f"{counts['rewrite']} to rewrite, {counts['check']} to check by hand, "
          f"{counts['keep']} kept, {counts['skip']} skipped")
    if not args.apply:
        if not args.to:
            print(f"(the number may move by the time you apply; pass --to {kind}{new} to pin it)")
        return 0

    edits = {}
    for act, path, _, start, end, *_ in plan:
        if act == "rewrite":
            edits.setdefault(path, []).append((start, end))
    for path, spans in edits.items():
        f = src.root / path
        text = f.read_bytes().decode("utf-8")
        for start, end in sorted(spans, reverse=True):
            text = text[:start] + f"{kind}{new}" + text[end:]
        f.write_bytes(text.encode("utf-8"))
    res = Reservations(src.root)
    with res.locked():
        res.raise_to(tree.name, kind, new)
    print(f"Rewrote {counts['rewrite']} mention(s) in {len(edits)} file(s). "
          f"Record the old number where readers look for it (the log's header: "
          f"\"{kind}{new} was {kind}{n} on branch {src.branch}\"), handle the 'check' lines, "
          f"then run `doc-ids lint`.")
    return 0


# --- command line ------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(prog="doc-ids", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-C", dest="repo", type=Path, default=Path.cwd(),
                    help="the repository or worktree to work in (default: the current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("next", help="the next free ID of a register, reserved")
    p.add_argument("tree", choices=TREES)
    p.add_argument("kind", help="D, O (spec) or Q (ux)")
    p.add_argument("--count", type=int, default=1, help="reserve this many consecutive IDs")
    p.add_argument("--peek", action="store_true", help="show the next ID without reserving it")
    p.add_argument("--against", action="append", default=[], metavar="REF",
                   help="also stay clear of a branch with no worktree here (repeatable)")
    p.add_argument("--explain", action="store_true", help="say on stderr where the highest numbers are")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("lint", help="IDs defined twice, dangling citations, stale headers")
    p.add_argument("tree", nargs="*", help="spec, ux (default: both)")
    p.add_argument("--main", help="the main branch, to say which duplicate is already there (default: main/master)")
    p.add_argument("--strict", action="store_true", help="fail on warnings too")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("compare", help="IDs two branches or worktrees both added, before they merge")
    p.add_argument("target", help="the branch merged into (keeps its numbers): a branch, commit or worktree path")
    p.add_argument("incoming", help="the branch being merged (renumbers): a branch, commit or worktree path")
    p.add_argument("--committed", action="store_true",
                   help="read branches as committed, even when a worktree has them checked out")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("renumber", help="give an issued ID a new number across this branch")
    p.add_argument("tree", choices=TREES)
    p.add_argument("id", help="the ID to renumber, e.g. D339")
    p.add_argument("--to", help="the new ID (default: the next free one, reserved on --apply)")
    p.add_argument("--def", dest="defn", metavar="FILE:LINE",
                   help="which entry to renumber, when the ID is defined more than once")
    p.add_argument("--take", action="append", default=[], metavar="FILE[:LINE]",
                   help="with --def: a citation that means the renumbered entry (repeatable)")
    p.add_argument("--exclude", action="append", default=[], metavar="FILE[:LINE]",
                   help="leave this citation alone (repeatable)")
    p.add_argument("--against", action="append", default=[], metavar="REF",
                   help="also keep the new number free of this branch (repeatable)")
    p.add_argument("--bare-outside", action="store_true",
                   help="also rewrite unqualified mentions outside specs/ and ui_ux/")
    p.add_argument("--include-archive", action="store_true", help="also rewrite mentions in archive/")
    p.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    p.set_defaults(func=cmd_renumber)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
