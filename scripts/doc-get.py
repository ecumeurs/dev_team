#!/usr/bin/env python3
"""doc-get: print exactly one targeted piece of a project's documents.

The reading side of the conventions in references/doc-tree-conventions.md,
references/build-plan-model.md, references/atd-atoms.md and
references/intent-register.md. An agent asks this command for a chunk, a spec
section, a register entry, an atom or a design item instead of grepping a tree
and reading a window of lines around the hit: the extract starts at the
target's own heading or entry and stops where the next one at the same level
begins, so nothing beside the target enters the reader's context.

Commands:
  chunk     a build plan's chunk, or some of its fields
  spec      a master spec section (D7.1, §C5.16.1, 4.1, an anchor, a title), or items of a numbered list
  section   any Markdown file's section by heading (number, anchor or title)
  decision  a register entry: D (spec or ux), O (spec), Q (ux), live or archived
  question  the same, for O and Q
  intent    an ATD atom or an intent-register entry, whole or by section (alias: atom)
  ui        a UI/UX document's section or labelled item ("Seventh chord symbols")
  toc       a document's headings (and, for UI/UX documents, item labels) with line ranges
  pack      a chunk and everything its Spec sections, Design docs and Atoms lines point to
  lint      ui: the UI/UX tier documents against references/ui-ux-docs.md;
            plan: every reference a build plan's chunks make resolves

Every extract starts with a marker line, `==> path:first-last · what <==`, so
the reader can cite it. Nothing is printed when the target is missing or
ambiguous: the command exits 1 and lists the candidates on stderr.

Run from anywhere inside the project (a worktree reads its own files); `-C DIR`
picks another one. Standard library only.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MAX_FILE = 5_000_000


class Missing(Exception):
    """A target that is absent or ambiguous; the message lists the candidates."""


def die(msg: str, code: int = 2) -> None:
    print(f"doc-get: {msg}", file=sys.stderr)
    sys.exit(code)


def note(msg: str) -> None:
    print(f"doc-get: {msg}", file=sys.stderr)


# --------------------------------------------------------------------------- documents

@dataclass
class Doc:
    path: Path
    root: Path
    lines: list[str]
    fence: list[bool] = field(default_factory=list)

    @property
    def rel(self) -> str:
        try:
            return str(self.path.relative_to(self.root))
        except ValueError:
            return str(self.path)


_DOCS: dict[Path, Doc] = {}


def load(path: Path, root: Path) -> Doc:
    path = path.resolve()
    if path in _DOCS:
        return _DOCS[path]
    if not path.is_file():
        raise Missing(f"no such file: {path}")
    if path.stat().st_size > MAX_FILE:
        raise Missing(f"{path} is larger than {MAX_FILE} bytes")
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    fence, inside = [], False
    for line in lines:
        if re.match(r"^\s*(```|~~~)", line):
            fence.append(True)
            inside = not inside
        else:
            fence.append(inside)
    doc = Doc(path, root, lines, fence)
    _DOCS[path] = doc
    return doc


@dataclass
class Span:
    doc: Doc
    start: int   # 0-based, inclusive
    end: int     # 0-based, exclusive
    what: str

    def text(self) -> str:
        return "\n".join(self.doc.lines[self.start:self.end])

    def render(self) -> str:
        return f"==> {self.doc.rel}:{self.start + 1}-{self.end} · {self.what} <==\n{self.text()}"


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def headings(doc: Doc) -> list[tuple[int, int, str]]:
    out = []
    for i, line in enumerate(doc.lines):
        if doc.fence[i]:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def trim(doc: Doc, start: int, end: int) -> int:
    while end > start + 1 and doc.lines[end - 1].strip() == "":
        end -= 1
    return end


def section_end(doc: Doc, start: int, level: int, shallow: bool = False) -> int:
    for i, lvl, _ in headings(doc):
        if i > start and (shallow or lvl <= level):
            return trim(doc, start, i)
    return trim(doc, start, len(doc.lines))


def block_end(doc: Doc, start: int, limit: int | None = None) -> int:
    """A top-level list item or register entry: its first line, then every blank or
    indented line, up to the next line that starts at column 0."""
    limit = len(doc.lines) if limit is None else limit
    i = start + 1
    while i < limit:
        line = doc.lines[i]
        if line.strip() and not line[0].isspace() and not doc.fence[i]:
            break
        i += 1
    return trim(doc, start, i)


def slug(text: str) -> str:
    """GitHub's heading anchor."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


MARKER_RE = re.compile(r"\*\*\[[^\]]*\]\*\*|\[v\d[^\]]*\]|_v\d[^_]*_:?")


def norm(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = MARKER_RE.sub("", text)
    text = re.sub(r"[*_`]", "", text)
    text = text.replace("’", "'").replace("§", "").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text.rstrip(".:;, ")


NUM_RE = re.compile(r"^(?:part\s+)?§?([A-Za-z]?\d+(?:\.\d+)*)\.?(?=\s|$)")


def sec_number(title: str) -> str | None:
    m = NUM_RE.match(norm(title))
    return m.group(1).lower() if m else None


def pick(ref: str, cands: list[tuple[str, object]], kind: str, where: str, show=None, exact: bool = False):
    """Choose one candidate by name: exact (case and punctuation aside), then, unless
    `exact`, by prefix, then by substring, saying so on stderr. A citation is resolved
    with `exact`: a near name is a different name, not a guess to make. `cands` holds
    (normalized name, value); several names may point to one value."""
    r = norm(ref)
    tests = [("exact", lambda n: n == r)]
    if not exact:
        tests += [("prefix", lambda n: n.startswith(r)), ("substring", lambda n: r in n)]
    for how, test in tests:
        hits, names = [], []
        for n, v in cands:
            if test(n) and v not in hits:
                hits.append(v)
                names.append(n)
        if len(hits) == 1:
            if how != "exact":
                note(f"{kind} {ref!r} matched {names[0]!r} by {how}; cite it by that name")
            return hits[0]
        if len(hits) > 1:
            names = [show(v) for v in hits] if show else sorted({n for n, v in cands if test(n)})
            more = f"; and {len(names) - 12} more" if len(names) > 12 else ""
            raise Missing(f"{kind} {ref!r} is ambiguous in {where}: " + "; ".join(names[:12]) + more)
    close = difflib.get_close_matches(r, [n for n, _ in cands], n=6, cutoff=0.5)
    hint = f"; closest: {'; '.join(close)}" if close else ""
    raise Missing(f"no {kind} {ref!r} in {where}{hint}")


def find_section(doc: Doc, ref: str, shallow: bool = False, exact: bool = False) -> Span:
    ref = ref.strip()
    if "#" in ref:
        ref = ref.split("#", 1)[1]
    hs = headings(doc)
    if not hs:
        raise Missing(f"{doc.rel} has no headings")
    num = NUM_RE.match(norm(ref))
    if num and norm(ref) == num.group(0).strip().rstrip("."):
        hits = [h for h in hs if sec_number(h[2]) == num.group(1).lower()]
        if len(hits) == 1:
            i, lvl, title = hits[0]
            return Span(doc, i, section_end(doc, i, lvl, shallow), title)
        if len(hits) > 1:
            raise Missing(f"section {ref!r} is numbered {len(hits)} times in {doc.rel}: "
                          + "; ".join(f"line {h[0] + 1}: {h[2]}" for h in hits))
    cands: list[tuple[str, object]] = []
    for h in hs:
        cands.append((slug(h[2]), h))
        cands.append((norm(h[2]), h))
    anchor = [h for h in hs if slug(h[2]) == ref.lower()]
    if len(anchor) == 1:
        h = anchor[0]
    else:
        h = pick(ref, cands, "section", doc.rel, show=lambda h: f"{norm(h[2])} (line {h[0] + 1})", exact=exact)
    i, lvl, title = h
    return Span(doc, i, section_end(doc, i, lvl, shallow), title)


# A list item with a bold label, at any depth, after an optional change tag:
# "- **[v3.3 new]** **Seventh chord symbols.** …", "  - **Fit.** …". A tag alone
# is no label.
LABEL_RE = re.compile(r"^(\s*)[-*]\s+(?:\*\*\[[^\]]*\]\*\*\s*)?\*\*(?!\[)(.+?)\*\*")


def labelled_items(doc: Doc, lo: int = 0, hi: int | None = None) -> list[tuple[int, str, int]]:
    """(line, label, indent) of every labelled list item in [lo, hi)."""
    hi = len(doc.lines) if hi is None else hi
    out = []
    for i in range(lo, hi):
        if doc.fence[i]:
            continue
        m = LABEL_RE.match(doc.lines[i])
        if m:
            out.append((i, m.group(2), len(m.group(1).expandtabs(4))))
    return out


def item_end(doc: Doc, start: int, indent: int, limit: int | None = None) -> int:
    """A list item: its first line and every following line indented deeper, blank
    lines included, up to the first non-blank line at its own indent or less."""
    limit = len(doc.lines) if limit is None else limit
    i = start + 1
    while i < limit:
        line = doc.lines[i]
        if line.strip() and not doc.fence[i] and len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip()) <= indent:
            break
        i += 1
    return trim(doc, start, i)


def find_item(doc: Doc, ref: str, exact: bool = False) -> Span:
    """A heading, or a list item by its bold label. "Scope: label" looks inside the
    scope first, a heading or another item ("Jam's controls: Foundation")."""
    lo, hi, scope = 0, len(doc.lines), ""
    if ":" in ref:
        head, rest = ref.rsplit(":", 1)
        try:
            s = find_item(doc, head.strip(), exact)
            lo, hi, scope, ref = s.start, s.end, s.what + ": ", rest.strip()
        except Missing:
            pass
    cands: list[tuple[str, object]] = []
    for i, lvl, title in headings(doc):
        if lo <= i < hi:
            cands.append((norm(title), ("h", i, lvl, title)))
    for i, label, indent in labelled_items(doc, lo, hi):
        if scope and i == lo:
            continue
        cands.append((norm(label), ("item", i, indent, label)))
    kind, i, lvl, title = pick(ref, cands, "heading or item", doc.rel + (f" ({scope.rstrip(': ')})" if scope else ""),
                               show=lambda v: f"{norm(v[3])} (line {v[1] + 1})", exact=exact)
    if kind == "h":
        return Span(doc, i, min(section_end(doc, i, lvl), hi), scope + title)
    return Span(doc, i, item_end(doc, i, lvl, hi), scope + norm(title))


def numbered_items(span: Span, wanted: list[int]) -> list[Span]:
    doc, out = span.doc, []
    found = {}
    for i in range(span.start, span.end):
        m = re.match(r"^(\d+)\.\s", doc.lines[i])
        if m and not doc.fence[i]:
            found.setdefault(int(m.group(1)), i)
    for n in wanted:
        if n not in found:
            raise Missing(f"no item {n} in {span.what} ({doc.rel}:{span.start + 1}-{span.end})")
        i = found[n]
        out.append(Span(doc, i, block_end(doc, i, span.end), f"{span.what}, item {n}"))
    return out


# --------------------------------------------------------------------------- the project

def project_root(start: Path) -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 else start.resolve()


def version_key(text: str) -> tuple:
    m = re.search(r"v(\d+(?:\.\d+)*)", text)
    return tuple(int(x) for x in m.group(1).split(".")) if m else (0,)


def plan_path(root: Path, plan: str | None, release: str | None) -> Path:
    if plan:
        p = Path(plan)
        return p if p.is_absolute() else root / p
    plans = sorted((root / "specs").glob("versions/*/build-plan*.md")) + sorted((root / "specs").glob("build-plan*.md"))
    if not plans:
        raise Missing(f"no build plan under {root}/specs (use --plan)")

    def key(p: Path) -> tuple:
        own = p.stem[len("build-plan"):].lstrip("-")
        return version_key(own) if own else version_key(p.parent.name)
    if release:
        r = version_key(release)
        hits = [p for p in plans if key(p) == r]
        if not hits:
            raise Missing(f"no build plan for {release}: " + ", ".join(str(p.relative_to(root)) for p in plans))
        return hits[0]
    return max(plans, key=key)


def spec_path(root: Path, spec: str | None, release: str | None) -> Path:
    if spec:
        p = Path(spec)
        return p if p.is_absolute() else root / p
    try:
        p = plan_path(root, None, release).parent / "master-spec.md"
        if p.is_file():
            return p
    except Missing:
        pass
    for p in [root / "specs" / "master-spec.md", *sorted((root / "specs").glob("versions/*/master-spec.md"),
                                                          key=lambda p: version_key(p.parent.name), reverse=True)]:
        if p.is_file():
            return p
    raise Missing(f"no master spec under {root}/specs (use --spec)")


def resolve_keyword(root: Path, name: str, args) -> Path:
    """`plan`, `spec`, `wave-log`, `decisions`, `questions`, or a path."""
    if name == "plan":
        return plan_path(root, args.plan, args.release)
    if name == "spec":
        return spec_path(root, args.spec, args.release)
    if name == "wave-log":
        p = plan_path(root, args.plan, args.release)
        log = p.with_name(p.name.replace("build-plan", "wave-log"))
        if log.is_file():
            return log
        raise Missing(f"no wave log beside {p.relative_to(root)}")
    p = Path(name)
    if not p.is_absolute():
        p = (Path.cwd() / p) if (Path.cwd() / p).exists() else root / p
    return p


# --------------------------------------------------------------------------- chunks

# The chunk template of references/build-plan-model.md: header lines, then one
# list item per field, its name plain ("- Goal:") or bold ("- **Goal:**").
CHUNK_RE = re.compile(r"^(#{2,4})\s+Chunk\s+([0-9]+[a-z]?)\b(?:\s*[—–-]\s*(.*))?", re.I)
HEADER_FIELDS = ("Status", "Wave", "Depends on", "Architecture capture", "Record")
CHUNK_FIELDS = ("Goal", "Scope", "Files", "Spec sections / Design docs", "Spec sections", "Design docs",
                "Atoms", "Intent entries", "Atoms (or intent entries)", "Data", "Revisions", "Done when",
                "Verification", "Split rule")
HEADER_FIELD_RE = re.compile(r"^([A-Z][A-Za-z ]{1,40}):(?:\s|$)")
BULLET_FIELD_RE = re.compile(r"^-\s+(?:\*\*([^*]{1,60}?):\*\*|(" + "|".join(re.escape(f) for f in CHUNK_FIELDS) + r"):(?=\s|$))")


def find_chunk(doc: Doc, cid: str) -> Span:
    cid = cid.lower().removeprefix("chunk").strip()
    found = {}
    for i, lvl, title in headings(doc):
        m = CHUNK_RE.match(doc.lines[i])
        if m:
            found[m.group(2).lower()] = (i, lvl, title)
    if cid not in found:
        base = re.match(r"^(\d+)[a-z]$", cid)
        if base and base.group(1) in found:
            note(f"chunk {cid} is a split half; printing chunk {base.group(1)}, which holds its split rule")
            cid = base.group(1)
        else:
            raise Missing(f"no chunk {cid} in {doc.rel}; chunks: " + ", ".join(sorted(found, key=lambda c: (int(re.sub(r'\D', '', c)), c))))
    i, lvl, title = found[cid]
    return Span(doc, i, section_end(doc, i, lvl), title)


def chunk_fields(span: Span, header_names: tuple[str, ...] | None = HEADER_FIELDS) -> list[tuple[str, Span]]:
    """A chunk's fields (header lines and field items), or, with header_names=None,
    any `Name: value` lines (an intent-register entry)."""
    doc, out, i = span.doc, [], span.start + 1
    while i < span.end:
        line = doc.lines[i]
        m = BULLET_FIELD_RE.match(line)
        if m and not doc.fence[i]:
            end = block_end(doc, i, span.end)
            name = m.group(1) or m.group(2)
            out.append((name, Span(doc, i, end, name)))
            i = end
            continue
        m = HEADER_FIELD_RE.match(line)
        if m and not doc.fence[i] and (header_names is None or m.group(1) in header_names):
            j = i + 1
            while j < span.end and doc.lines[j].strip() and not HEADER_FIELD_RE.match(doc.lines[j]) \
                    and not BULLET_FIELD_RE.match(doc.lines[j]):
                j += 1
            out.append((m.group(1), Span(doc, i, j, m.group(1))))
            i = j
            continue
        i += 1
    return out


def pick_field(span: Span, name: str) -> Span:
    fields = chunk_fields(span)
    f = pick(name, [(norm(n), (n, s)) for n, s in fields], "field", f"{span.what} ({span.doc.rel})")
    n, s = f
    return Span(s.doc, s.start, s.end, f"{span.what} › {n}")


# --------------------------------------------------------------------------- registers

DEF_RE = re.compile(r"^(?:[-*]\s+\*\*|#{1,6}\s+(?:\*\*)?)([DOQ])(\d+)(?!\w|\s*[-–—]\s*[DOQ]?\d)")
TREES = {"spec": ("specs", {"D": "decisions", "O": "open-questions"}),
         "ux": ("ui_ux", {"D": "decisions", "Q": "open-questions"})}


def register_files(root: Path, tree: str, kind: str) -> list[Path]:
    d, kinds = TREES[tree]
    stem = kinds[kind]
    live = root / d / f"{stem}.md"
    files = [live] if live.is_file() else []
    archived = sorted((root / d / "archive").rglob(f"{stem}*.md")) if (root / d / "archive").is_dir() else []

    def covers(p: Path) -> int:
        m = re.search(rf"{kind}(\d+)(?:-{kind}(\d+))?$", p.stem)
        return 0 if m else 1
    return files + sorted(archived, key=covers)


def find_entry(root: Path, ident: str, tree: str | None) -> list[Span]:
    m = re.match(r"^(?:(spec|ux)\s+)?([DOQ])(\d+)$", ident.strip(), re.I)
    if not m:
        raise Missing(f"not a register ID: {ident!r} (D12, O40, Q7, or 'ux D45')")
    tree = (m.group(1) or tree or "").lower() or None
    kind, num = m.group(2).upper(), int(m.group(3))
    if tree is None:
        tree = "ux" if kind == "Q" else "spec"
    if kind not in TREES[tree][1]:
        raise Missing(f"the {tree} tree has no {kind} register")
    hits: list[Span] = []
    for p in register_files(root, tree, kind):
        m2 = re.search(rf"{kind}(\d+)(?:-{kind}(\d+))?$", p.stem)
        if m2 and not (int(m2.group(1)) <= num <= int(m2.group(2) or m2.group(1))):
            continue
        doc = load(p, root)
        for i, line in enumerate(doc.lines):
            if doc.fence[i]:
                continue
            d = DEF_RE.match(line)
            if d and d.group(1) == kind and int(d.group(2)) == num:
                h = HEADING_RE.match(line)
                end = section_end(doc, i, len(h.group(1))) if h else block_end(doc, i)
                hits.append(Span(doc, i, end, f"{tree} {kind}{num}"))
        if hits:
            break
    if not hits:
        raise Missing(f"no {tree} {kind}{num} in {TREES[tree][0]}/ (live register or archive)")
    return hits


# --------------------------------------------------------------------------- intent

ATOM_SECTIONS = {"intent": "INTENT", "rule": "RULE", "logic": "RULE", "interface": "INTERFACE",
                 "technical": "INTERFACE", "expectation": "EXPECTATION", "expectations": "EXPECTATION"}


def atd_docs(root: Path) -> Path | None:
    cfg = root / ".atd"
    if not cfg.is_file():
        return None
    try:
        return root / json.loads(cfg.read_text()).get("docs_path", "docs/")
    except (ValueError, OSError):
        return root / "docs"


def atom_file(docs: Path, ident: str) -> Path:
    p = docs / f"{ident}.atom.md"
    if p.is_file():
        return p
    for q in docs.rglob("*.atom.md"):
        with q.open(encoding="utf-8", errors="replace") as fh:
            for _, line in zip(range(30), fh):
                if re.match(rf"^id:\s*{re.escape(ident)}\s*$", line):
                    return q
    names = [q.name[:-len(".atom.md")] for q in docs.rglob("*.atom.md")]
    close = difflib.get_close_matches(ident, names, n=6, cutoff=0.6)
    raise Missing(f"no atom {ident} in {docs}" + (f"; closest: {', '.join(close)}" if close else ""))


def atom_meta(doc: Doc) -> tuple[int, dict]:
    """End line (exclusive) of the front matter, and its scalar fields."""
    if not doc.lines or doc.lines[0].strip() != "---":
        return 0, {}
    meta = {}
    for i in range(1, len(doc.lines)):
        if doc.lines[i].strip() == "---":
            return i + 1, meta
        m = re.match(r"^([a-z_]+):\s*(\S.*)$", doc.lines[i])
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return 0, {}


def intent_spans(root: Path, ident: str, sections: list[str]) -> list[Span]:
    docs = atd_docs(root)
    if docs is not None:
        doc = load(atom_file(docs, ident), root)
        fm_end, meta = atom_meta(doc)
        tag = f"{ident} ({meta.get('status', '?')} {meta.get('version', '')})".replace(" )", ")")
        if not sections:
            return [Span(doc, 0, trim(doc, 0, len(doc.lines)), tag)]
        out = []
        hs = [(i, lvl, t) for i, lvl, t in headings(doc) if lvl == 2 and i >= fm_end]
        for s in sections:
            key = s.lower()
            if key in ("meta", "frontmatter", "front-matter"):
                out.append(Span(doc, 0, fm_end, f"{tag} › front matter"))
                continue
            want = ATOM_SECTIONS.get(key, s.upper())
            hits = [h for h in hs if want in h[2].upper()]
            if len(hits) != 1:
                raise Missing(f"atom {ident} has {'no' if not hits else 'several'} section {s!r}; sections: "
                              + "; ".join(h[2] for h in hs))
            i, lvl, t = hits[0]
            out.append(Span(doc, i, section_end(doc, i, lvl), f"{tag} › {t}"))
        merged: list[Span] = []
        for sp in sorted(out, key=lambda x: x.start):
            prev = merged[-1] if merged else None
            if prev and all(not ln.strip() for ln in doc.lines[prev.end:sp.start]):
                merged[-1] = Span(doc, prev.start, sp.end, prev.what + " + " + sp.what.split(" › ", 1)[1])
            else:
                merged.append(sp)
        return merged
    reg = root / "intent"
    if (reg / "README.md").is_file():
        for p in sorted(reg.glob("*.md")):
            doc = load(p, root)
            for i, lvl, t in headings(doc):
                if lvl == 2 and t.strip() == ident:
                    span = Span(doc, i, section_end(doc, i, 2), ident)
                    if not sections:
                        return [span]
                    fields = chunk_fields(span, None)
                    return [Span(f.doc, f.start, f.end, f"{ident} › {n}") for s in sections
                            for n, f in [pick(s, [(norm(n), (n, f)) for n, f in fields], "field", ident)]]
        raise Missing(f"no intent entry {ident} in intent/")
    raise Missing(f"{root} declares no intent (no .atd, no intent/README.md)")


# --------------------------------------------------------------------------- UI/UX

def ui_path(root: Path, name: str, version: str | None, which: str) -> Path:
    p = Path(name)
    if p.suffix == ".md":
        return p if p.is_absolute() else ((Path.cwd() / p) if (Path.cwd() / p).exists() else root / p)
    base = root / "ui_ux" / ("versions/" + version if version else "")
    name = name.strip("/")
    if name.endswith(("/handoff", "/intent")):
        name, which = name.rsplit("/", 1)
    for cand in ([base / name] if "/" in name else [base / "screens" / name, base / "flows" / name]):
        if (cand / f"{which}.md").is_file():
            return cand / f"{which}.md"
    have = sorted(str(q.parent.relative_to(base)) for q in base.glob("*/*/handoff.md"))
    close = difflib.get_close_matches(name, have + [h.split("/")[-1] for h in have], n=6, cutoff=0.5)
    raise Missing(f"no {which}.md for {name!r} under {base.relative_to(root)}"
                  + (f"; closest: {', '.join(close)}" if close else ""))


# --------------------------------------------------------------------------- toc

def toc(doc: Doc, labels: bool) -> str:
    hs = headings(doc)
    out = [f"==> {doc.rel} · {len(doc.lines)} lines <=="]
    items = labelled_items(doc) if labels else []
    first = hs[0][0] if hs else len(doc.lines)
    for j, label, indent in items:
        if j < first:
            out.append(f"{' ' * indent}• {norm(label)}  [{j + 1}]")
    for n, (i, lvl, title) in enumerate(hs):
        end = section_end(doc, i, lvl)
        size = sum(len(x) + 1 for x in doc.lines[i:end])
        out.append(f"{'  ' * (lvl - 1)}{title}  [{i + 1}-{end}, {size // 1024 or '<1'} KB]")
        nxt = hs[n + 1][0] if n + 1 < len(hs) else len(doc.lines)
        for j, label, indent in items:
            if i < j < nxt:
                out.append(f"{'  ' * lvl}{' ' * indent}• {norm(label)}  [{j + 1}]")
    return "\n".join(out)


# --------------------------------------------------------------------------- pack

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def link_target(base: Path, href: str) -> tuple[Path | None, str]:
    path, _, anchor = href.partition("#")
    if re.match(r"^[a-z]+:", path):
        return None, ""
    return ((base / path).resolve() if path else None), anchor


def items_in(text: str) -> list[int]:
    text = re.sub(r"\([^()]*\)", "", re.sub(r"\s+", " ", text))
    out: list[int] = []
    for m in re.finditer(r"\bitems?\s+((?:\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*|\s+and\s+)?)+)", text):
        for part in re.finditer(r"(\d+)(?:\s*[–-]\s*(\d+))?", m.group(1)):
            a, b = int(part.group(1)), int(part.group(2) or part.group(1))
            out += [n for n in range(a, b + 1) if n not in out]
    return out


def dod_section(plan: Doc) -> tuple[Path, str] | None:
    seen = set()
    for line in plan.lines:
        for m in LINK_RE.finditer(line):
            p, anchor = link_target(plan.path.parent, m.group(2))
            if p and "definition-of-done" in anchor:
                seen.add((p, anchor))
    return seen.pop() if len(seen) == 1 else None


def design_refs(doc: Doc, ref: str) -> list[tuple[Span | None, str, str]]:
    """One reference from a plan's Design docs parenthesis: "label", "Heading: label",
    or a comma list of either under one heading ("Heading: a, b, c")."""
    try:
        return [(find_item(doc, ref, exact=True), ref, "")]
    except Missing as e:
        first = str(e)
    if "," not in ref:
        return [(None, ref, first)]
    head, sep, rest = ref.rpartition(":") if ":" in ref else ("", "", ref)
    out = []
    for part in (x.strip() for x in rest.split(",")):
        if not part:
            continue
        r = f"{head}: {part}" if sep else part
        try:
            out.append((find_item(doc, r, exact=True), r, ""))
        except Missing as e:
            out.append((None, r, str(e)))
    return out


def gather(root: Path, plan: Doc, chunk: Span, args) -> tuple[list[tuple[str, Span]], list[str], list[str]]:
    """What a chunk's Spec sections, Design docs and Atoms lines point to, as
    (blocks within the budget, pointers to the rest, references that don't resolve)."""
    fields = {norm(n): s for n, s in chunk_fields(chunk)}
    budget = args.max_bytes
    blocks: list[tuple[str, Span]] = []
    pointers: list[str] = []
    problems: list[str] = []
    used: set[tuple] = set()

    def add(group: str, span: Span, cmd: str) -> None:
        nonlocal budget
        key = (span.doc.path, span.start, span.end)
        if any(d == key[0] and a <= key[1] and key[2] <= b for d, a, b in used):
            return          # already printed, whole or inside a larger block
        used.add(key)
        size = len(span.text().encode()) + 1
        if size > budget:
            pointers.append(f"{span.what} ({span.doc.rel}:{span.start + 1}-{span.end}, {size // 1024} KB, over the budget): {cmd}")
            return
        budget -= size
        blocks.append((group, span))

    def rel(p: Path) -> str:
        try:
            return str(p.relative_to(root))
        except ValueError:
            return str(p)

    resolved_links: set[str] = set()

    # The Spec sections and Design docs fields (one field or two, per the model): a link
    # into ui_ux/ is a design document, read for the sections the parenthesis after it
    # names; any other link with an anchor is a spec section; "items N" are numbered
    # items of the definition of done the plan links.
    ref_fields = [s for n, s in fields.items() if n.startswith("spec section") or n.startswith("design doc")]
    ui_root = (root / "ui_ux").resolve()
    for f in ref_fields:
        text = re.sub(r"\s+", " ", f.text())
        links = list(LINK_RE.finditer(text))
        for k, m in enumerate(links):
            p, anchor = link_target(plan.path.parent, m.group(2))
            resolved_links.add(m.group(2))
            if p is None:
                continue
            if ui_root in p.parents:
                if args.no_design:
                    continue
                tail = text[m.end():links[k + 1].start() if k + 1 < len(links) else len(text)]
                paren = re.match(r"\s*\(([^()]*)\)", tail)
                refs = [r.strip() for r in paren.group(1).split(";")] if paren else []
                if anchor:
                    refs.insert(0, anchor)
                if not refs:
                    pointers.append(f"{m.group(1)}: no section named in the plan: doc-get toc {rel(p)}")
                    continue
                try:
                    doc = load(p, root)
                except Missing as e:
                    problems.append(str(e))
                    continue
                for r in refs:
                    for span, ref, err in design_refs(doc, r):
                        if err:
                            problems.append(err)
                        else:
                            add("Design docs", span, f"doc-get ui {rel(p)} {ref!r}")
            elif anchor:
                try:
                    add("Spec sections", find_section(load(p, root), anchor, exact=True), f"doc-get section {rel(p)} {anchor}")
                except Missing as e:
                    problems.append(str(e))
            else:
                pointers.append(f"{m.group(1)}: whole file, not packed: doc-get toc {rel(p)}")
        wanted = items_in(text) if not re.match(r"(?i)design", f.what) else []
        if wanted:
            dod = dod_section(plan)
            if dod is None:
                problems.append(f"items {wanted}: the plan links no single definition-of-done section to read them from")
            else:
                try:
                    sec = find_section(load(dod[0], root), dod[1], exact=True)
                    for span in numbered_items(sec, wanted):
                        add("Spec items", span, f"doc-get spec {dod[1]} --item {span.what.rsplit(' ', 1)[-1]}")
                except Missing as e:
                    problems.append(str(e))

    atoms_f = next((s for n, s in fields.items() if n.startswith("atoms") or n.startswith("intent")), None)
    if atoms_f and not args.no_intent:
        parts = re.split(r"(?i)drift checks?:", atoms_f.text(), maxsplit=1)
        main, drift = parts[0], (parts[1] if len(parts) > 1 else "")
        # An ID is a slug with an underscore (ATD) or a hyphen (intent register);
        # other code spans on the line (an agent's name, a command) are not IDs.
        ids = list(dict.fromkeys(re.findall(r"`([a-z][a-z0-9]*[_-][a-z0-9_-]+)`", main)))
        sections = [s.strip() for s in args.atom_sections.split(",")] if args.atom_sections != "all" else []
        for ident in ids:
            try:
                for span in intent_spans(root, ident, sections):
                    add("Intent", span, f"doc-get intent {ident}")
            except Missing as e:
                problems.append(str(e))
        for ident in dict.fromkeys(re.findall(r"`([a-z][a-z0-9_]+)`", drift)):
            pointers.append(f"{ident} (drift check only): doc-get intent {ident}")

    for name in args.plan_section or []:
        try:
            add("Plan sections", find_section(plan, name), f"doc-get section plan {name!r}")
        except Missing as e:
            problems.append(str(e))

    for m in LINK_RE.finditer(chunk.text()):
        href = m.group(2)
        if href in resolved_links:
            continue
        p, anchor = link_target(plan.path.parent, href)
        resolved_links.add(href)
        if p is None and anchor.startswith("chunk-"):
            cid = re.match(r"chunk-(\d+[a-z]?)", anchor)
            pointers.append(f"{m.group(1)}: doc-get chunk {cid.group(1) if cid else anchor}")
        elif p == plan.path.resolve() or (p is None and anchor):
            pointers.append(f"{m.group(1)}: doc-get section plan {anchor}")
        elif p is not None:
            pointers.append(f"{m.group(1)}: " + (f"doc-get section {rel(p)} {anchor}" if anchor else f"doc-get toc {rel(p)}"))

    return blocks, pointers, problems


def pack(root: Path, args) -> int:
    plan = load(plan_path(root, args.plan, args.release), root)
    chunk = find_chunk(plan, args.id)
    blocks, pointers, problems = gather(root, plan, chunk, args)
    print(f"# Pack: {chunk.what}")
    print(f"\nFrom {plan.rel}. Each block below is printed verbatim from the file and lines its marker names.")
    if not args.refs_only:
        print()
        print(chunk.render())
    group = None
    for g, span in blocks:
        if g != group:
            print(f"\n# {g}\n")
            group = g
        else:
            print()
        print(span.render())
    if pointers:
        print("\n# Not packed (read on demand)\n")
        for p in pointers:
            print(f"- {p}")
    if problems:
        print("\n# Unresolved references (report them; don't guess)\n")
        for p in problems:
            print(f"- {p}")
    return 0


# --------------------------------------------------------------------------- lint ui

# references/ui-ux-docs.md: the sections each handoff holds, in order. None
# stands for the screen-specific sections, which sit at that place.
SCREEN_SECTIONS = ["Layout Tree", "Components and Content", None, "Focus and Keyboard", "Responsive Behavior", "States"]
SCREEN_REQUIRED = {"Layout Tree", "Components and Content", "Responsive Behavior", "States"}
FLOW_SECTIONS = ["Flow", None, "Routing Rules"]
FLOW_REQUIRED = {"Flow", "Routing Rules"}
REGISTERS = {"decisions.md", "open-questions.md", "todo.md"}
REG_ID_RE = re.compile(r"(?<![\w§./#-])(?:(?:spec|ux) )?[DOQ]\d{2,}(?![\w.])")
ITEM_RE = re.compile(r"^(\s*)[-*]\s+")


def tier_kind(rel: str) -> str | None:
    parts = rel.split("/")
    if parts[0] != "ui_ux" or len(parts) < 2 or parts[1] in ("versions", "archive"):
        return None
    if len(parts) == 4 and parts[1] in ("screens", "flows") and parts[3] in ("handoff.md", "intent.md"):
        return f"{parts[1][:-1]}-{parts[3][:-3]}"
    if len(parts) == 2 and parts[1].endswith(".md") and parts[1] not in REGISTERS:
        return "root"
    return None


def lint_doc(doc: Doc, kind: str) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    err = lambda i, m: out.append((i, "error", m))
    warn = lambda i, m: out.append((i, "warning", m))
    hs = headings(doc)
    size = sum(len(x) + 1 for x in doc.lines)
    h1 = [h for h in hs if h[1] == 1]
    if len(h1) > 1:
        err(h1[1][0], "a second '#' heading; the title is the only one")
    h2 = [h for h in hs if h[1] == 2]
    if not h2 and size > 2048:
        err(0, f"no '##' section in {size // 1024} KB: nothing in it can be addressed")
    seen: dict[str, int] = {}
    for i, lvl, title in hs:
        if lvl > 3:
            warn(i, f"'{'#' * lvl}' heading: sections go two levels deep; label a sub-item instead")
        key = slug(title)
        if key in seen:
            err(i, f"heading {title!r} repeats line {seen[key] + 1}; both share one anchor")
        else:
            seen[key] = i

    # Required sections and their order.
    if kind in ("screen-handoff", "flow-handoff"):
        order, required = (SCREEN_SECTIONS, SCREEN_REQUIRED) if kind == "screen-handoff" else (FLOW_SECTIONS, FLOW_REQUIRED)
        names = {norm(t): (i, t) for i, _, t in h2}
        for name in order:
            if name and norm(name) not in names:
                if name in required:
                    err(0, f"no '## {name}' section")
                elif name == "Focus and Keyboard":
                    warn(0, "no '## Focus and Keyboard' section (required when the screen has anything focusable)")
        rank = {norm(n): k for k, n in enumerate(order) if n}
        spot = order.index(None)
        ranks = [(rank.get(norm(t), spot), i, t) for i, _, t in h2]
        for (r1, _, t1), (r2, i2, t2) in zip(ranks, ranks[1:]):
            if r2 < r1:
                warn(i2, f"section {t2!r} comes after {t1!r}; the order is " + ", ".join(n or "<specific>" for n in order))

    # Section sizes.
    for i, lvl, title in h2:
        end = section_end(doc, i, 2)
        kb = sum(len(x) + 1 for x in doc.lines[i:end]) // 1024
        if kb > 20 and not any(l == 3 and i < j < end for j, l, _ in hs):
            warn(i, f"section {title!r} is {kb} KB with no '###' groups")

    # Items: labels, uniqueness among siblings, size.
    first = h2[0][0] if h2 else len(doc.lines)
    parents: list[tuple[int, int]] = []          # (indent, line) of the open items
    siblings: dict[tuple, dict[str, int]] = {}
    section = None
    for i in range(first, len(doc.lines)):
        if doc.fence[i]:
            continue
        line = doc.lines[i]
        h = HEADING_RE.match(line)
        if h:
            section, parents = i, []
            continue
        m = ITEM_RE.match(line)
        if not m:
            if line.strip() and not line[0].isspace():
                parents = []
            continue
        indent = len(m.group(1).expandtabs(4))
        while parents and parents[-1][0] >= indent:
            parents.pop()
        parent = parents[-1][1] if parents else None
        parents.append((indent, i))
        lab = LABEL_RE.match(line)
        if indent == 0 and not lab and kind.endswith("handoff"):
            err(i, "item with no bold label: nothing can point at it")
        if lab:
            name = norm(lab.group(2))
            group = siblings.setdefault((section, parent), {})
            if name in group:
                err(i, f"label {lab.group(2).strip()!r} repeats line {group[name] + 1} among its siblings")
            else:
                group[name] = i
        if indent == 0 and kind.endswith("handoff"):
            end = item_end(doc, i, 0)
            kb = sum(len(x) + 1 for x in doc.lines[i:end]) // 1024
            if kb >= 4 and not any(LABEL_RE.match(doc.lines[j]) for j in range(i + 1, end)):
                warn(i, f"item of {kb} KB with no labelled sub-items")

    # The change block: a line's "(link): label" must resolve.
    for i in range(0, first):
        line = doc.lines[i]
        if not line.startswith(">"):
            continue
        for m in re.finditer(r"\[([^\]]+)\]\(#([^)\s]+)\)(?::\s*([^;)]+))?", line):
            heading = next((t for _, _, t in hs if slug(t) == m.group(2)), None)
            if heading is None:
                warn(i, f"change line links #{m.group(2)}, which no heading has")
            elif m.group(3):
                try:
                    find_item(doc, f"{heading}: {m.group(3).strip()}", exact=True)
                except Missing:
                    warn(i, f"change line names {m.group(3).strip()!r} in {heading!r}, which isn't a label there")

    # The two-register rule.
    for i, line in enumerate(doc.lines):
        if not doc.fence[i]:
            for m in REG_ID_RE.finditer(line):
                warn(i, f"register ID {m.group(0)!r} in a tier document")
                break
    return out


def lint_plan(root: Path, args) -> int:
    """Every reference a build plan's chunks make that `pack` can't resolve."""
    plan = load(plan_path(root, args.plan, args.release), root)
    opts = argparse.Namespace(max_bytes=1 << 40, no_design=False, no_intent=False, atom_sections="intent",
                              plan_section=None)
    chunks = errors = 0
    for i, lvl, title in headings(plan):
        if not CHUNK_RE.match(plan.lines[i]):
            continue
        chunks += 1
        chunk = Span(plan, i, section_end(plan, i, lvl), title)
        _, pointers, problems = gather(root, plan, chunk, opts)
        for p in problems:
            print(f"{plan.rel}:{i + 1}: error: {title}: {p}")
        for p in pointers:
            if "no section named in the plan" in p:
                print(f"{plan.rel}:{i + 1}: warning: {title}: {p.split(': doc-get')[0]}")
        errors += len(problems)
    print(f"doc-get lint plan: {plan.rel}, {chunks} chunks, {errors} unresolved references", file=sys.stderr)
    return 1 if errors else 0


def lint_ui(root: Path, args) -> int:
    if args.paths:
        files = [resolve_keyword(root, x, args) for x in args.paths]
    else:
        files = sorted((root / "ui_ux").rglob("*.md")) if (root / "ui_ux").is_dir() else []
    findings: list[tuple[Doc, int, str, str]] = []
    checked = 0
    for f in files:
        doc = load(f, root)
        kind = tier_kind(doc.rel)
        if kind is None:
            if args.paths:
                note(f"{doc.rel} is not a root tier document; skipped")
            continue
        checked += 1
        findings += [(doc, i, sev, msg) for i, sev, msg in lint_doc(doc, kind)]
    for doc, i, sev, msg in findings:
        print(f"{doc.rel}:{i + 1}: {sev}: {msg}")
    errors = sum(1 for f in findings if f[2] == "error")
    warnings = len(findings) - errors
    print(f"doc-get lint ui: {checked} documents, {errors} errors, {warnings} warnings", file=sys.stderr)
    return 1 if errors else 0


# --------------------------------------------------------------------------- CLI

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="doc-get", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:3]))
    ap.add_argument("-C", dest="dir", default=".", help="project directory (default: here)")
    ap.add_argument("--plan", help="build plan path (default: the highest-versioned build-plan*.md)")
    ap.add_argument("--release", help="pick the build plan of this release (v3.3)")
    ap.add_argument("--spec", help="master spec path (default: the one beside the build plan)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chunk", help="a chunk, or some of its fields")
    c.add_argument("id")
    c.add_argument("--field", "-f", action="append", help="Goal, Scope, Files, Spec sections, Atoms, Done when… (repeatable; prefix ok)")

    s = sub.add_parser("spec", help="a master spec section")
    s.add_argument("ref", nargs="+", help="D7.1, §C5.16.1, 4.1, an anchor, or title words")
    s.add_argument("--item", type=int, action="append", help="only these numbered items of the section (repeatable)")
    s.add_argument("--shallow", action="store_true", help="stop at the first subsection")

    se = sub.add_parser("section", help="any Markdown file's section")
    se.add_argument("file", help="a path, or plan / spec / wave-log")
    se.add_argument("ref", nargs="+")
    se.add_argument("--shallow", action="store_true")
    se.add_argument("--item", type=int, action="append")

    for name in ("decision", "question"):
        r = sub.add_parser(name, help="a register entry (D, O, Q), live or archived")
        r.add_argument("id", nargs="+", help="D527, O267, Q16, or 'ux D45'")
        r.add_argument("--tree", choices=["spec", "ux"])

    for name in ("intent", "atom"):
        i = sub.add_parser(name, help="an atom or intent-register entry")
        i.add_argument("id", nargs="+")
        i.add_argument("--section", "-s", action="append", help="intent, rule, interface, expectation, meta (ATD); a field name (register)")

    u = sub.add_parser("ui", help="a UI/UX document's section or labelled item")
    u.add_argument("doc", help="phrase-workspace, flows/jam, screens/x/intent, or a path")
    u.add_argument("ref", nargs="+", help="a heading, a bold item label, or 'Heading: label'")
    u.add_argument("--version", help="read ui_ux/versions/<version>/ (the frozen design)")
    u.add_argument("--intent", action="store_true", help="intent.md instead of handoff.md")

    t = sub.add_parser("toc", help="headings (and UI/UX item labels) with line ranges")
    t.add_argument("file", help="a path, plan, spec, wave-log, or a UI/UX name with --ui")
    t.add_argument("--ui", action="store_true", help="FILE is a UI/UX name (phrase-workspace, flows/jam)")
    t.add_argument("--version")
    t.add_argument("--labels", action="store_true", help="list bold item labels too (default for ui_ux/ files)")

    p = sub.add_parser("pack", help="a chunk with what its Spec sections, Design docs and Atoms lines point to")
    p.add_argument("id")
    p.add_argument("--max-bytes", type=int, default=60_000, help="budget for everything after the chunk (default 60000); the rest becomes pointers")
    p.add_argument("--atom-sections", default="intent,rule,expectation", help="comma list, or 'all' (default: intent,rule,expectation)")
    p.add_argument("--plan-section", action="append", help="also pack this section of the plan (repeatable), e.g. 'Workflow deltas'")
    p.add_argument("--refs-only", action="store_true", help="leave the chunk's own text out (the brief already carries it)")
    p.add_argument("--no-design", action="store_true")
    p.add_argument("--no-intent", action="store_true")

    li = sub.add_parser("lint", help="check the UI/UX documents' format, or a build plan's references")
    li.add_argument("what", choices=["ui", "plan"], help="ui: the UI/UX tier documents; plan: the build plan's references")
    li.add_argument("paths", nargs="*", help="ui only: these tier documents (default: every root tier document)")

    args = ap.parse_args(argv)
    root = project_root(Path(args.dir))
    try:
        if args.cmd == "chunk":
            span = find_chunk(load(plan_path(root, args.plan, args.release), root), args.id)
            spans = [pick_field(span, f) for f in args.field] if args.field else [span]
        elif args.cmd in ("spec", "section"):
            path = spec_path(root, args.spec, args.release) if args.cmd == "spec" else resolve_keyword(root, args.file, args)
            span = find_section(load(path, root), " ".join(args.ref), args.shallow)
            spans = numbered_items(span, args.item) if args.item else [span]
        elif args.cmd in ("decision", "question"):
            spans = find_entry(root, " ".join(args.id), args.tree)
            if len(spans) > 1:
                note(f"{spans[0].what} is defined {len(spans)} times; run `doc-ids lint`")
        elif args.cmd in ("intent", "atom"):
            spans = [s for ident in args.id for s in intent_spans(root, ident, args.section or [])]
        elif args.cmd == "ui":
            path = ui_path(root, args.doc, args.version, "intent" if args.intent else "handoff")
            spans = [find_item(load(path, root), " ".join(args.ref))]
        elif args.cmd == "toc":
            if args.ui:
                path = ui_path(root, args.file, args.version, "handoff")
            else:
                path = resolve_keyword(root, args.file, args)
            doc = load(path, root)
            print(toc(doc, args.labels or "ui_ux" in doc.rel.split("/")[0:1]))
            return 0
        elif args.cmd == "lint":
            return lint_ui(root, args) if args.what == "ui" else lint_plan(root, args)
        elif args.cmd == "pack":
            return pack(root, args)
        print("\n\n".join(s.render() for s in spans))
        return 0
    except Missing as e:
        note(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
