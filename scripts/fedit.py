#!/usr/bin/env python3
"""fedit: replace exact text in files, and fail loudly when it doesn't match.

The editing counterpart of doc-get. An agent that read a file through Bash
(doc-get, sed -n, grep) can't use Claude Code's Edit tool without reading the
whole file again through Read, so it used to write a python `.replace()` or a
`sed -i`, which report success when nothing matched. fedit takes the same
old/new pairs as Edit and checks every one before it writes anything.

Usage:
  fedit FILE <<'EOF'
  @@@ old
  text to find, exactly as it is in the file
  @@@ new
  text to put in its place
  @@@ old
  a second replacement in the same file
  @@@ new
  ...
  EOF

  fedit <<'EOF'            several files in one call
  @@@ file a/b.md
  @@@ old
  ...
  @@@ new
  ...
  @@@ file c/d.ts
  ...
  EOF

Rules:
  - Each `@@@ old` must occur exactly once in the file. `@@@ old all`
    replaces every occurrence (at least one). A miss or a double match
    changes nothing anywhere: fedit exits 1, names the block and shows the
    file's closest lines with their numbers, so the old text can be fixed
    without reading the file again.
  - A block's text is every line between its marker and the next one, blank
    lines included (so don't leave a blank line between blocks unless you
    mean it), joined by newlines without the newline that ends the last
    one, the same as Edit's old_string/new_string. To delete
    lines, include a neighbouring line in old and keep it in new. An empty
    new deletes the old text.
  - Blocks apply in order, each to the result of the previous ones.
  - Files are written only when every block of every file matched, each
    atomically, keeping its mode; a symlink's target is edited. A file with
    CRLF line endings is matched and written with CRLF.
  - Marker lines are `@@@ old`, `@@@ old all`, `@@@ new` and `@@@ file PATH`,
    alone on their line. If the text itself has such a line, pick another
    marker with `-m`, e.g. `-m '%%%'`.

Options:
  -n, --dry-run   check every block and report, write nothing
  -d, --diff      also print a unified diff of each change
  -m, --marker M  marker instead of @@@

Output: one line per block, `path:first-last  replaced (n lines -> m lines)`,
line numbers in the file as written. Exit 0 when every block applied, 1 when
a block failed to match (nothing written), 2 on a usage or input error.
Standard library only.
"""

import argparse
import difflib
import os
import sys
import tempfile


class InputError(Exception):
    pass


class MatchError(Exception):
    pass


def parse(stream, marker, default_file):
    """Return [(path, [block, ...]), ...]; a block is a dict."""
    files = []
    current = None
    block = None
    part = None  # 'old' or 'new'
    buf = []
    lineno = 0

    def flush():
        nonlocal buf
        if block is not None and part is not None:
            block[part] = "\n".join(buf)
        buf = []

    def need_file():
        nonlocal current
        if current is None:
            if default_file is None:
                raise InputError(
                    f"line {lineno}: `{marker} old` before any `{marker} file PATH` "
                    "and no FILE argument")
            current = (default_file, [])
            files.append(current)
        return current

    for lineno, raw in enumerate(stream, 1):
        line = raw[:-1] if raw.endswith("\n") else raw
        stripped = line.rstrip()
        if stripped.startswith(marker + " ") or stripped == marker:
            word = stripped[len(marker):].strip()
            flush()
            if word.startswith("file ") or word == "file":
                path = word[4:].strip()
                if not path:
                    raise InputError(f"line {lineno}: `{marker} file` needs a path")
                if block is not None and part == "old":
                    raise InputError(f"line {lineno}: block {block['n']} has no `{marker} new`")
                current = (path, [])
                files.append(current)
                block, part = None, None
            elif word in ("old", "old all"):
                if block is not None and part == "old":
                    raise InputError(f"line {lineno}: block {block['n']} has no `{marker} new`")
                f = need_file()
                block = {"n": len(f[1]) + 1, "all": word == "old all",
                         "line": lineno, "old": None, "new": None}
                f[1].append(block)
                part = "old"
            elif word == "new":
                if block is None or part != "old":
                    raise InputError(f"line {lineno}: `{marker} new` without a `{marker} old` before it")
                part = "new"
            else:
                raise InputError(
                    f"line {lineno}: unknown marker `{stripped}` "
                    f"(expected `{marker} old`, `{marker} old all`, `{marker} new`, `{marker} file PATH`; "
                    "use -m if the text itself has this line)")
            continue
        if part is None:
            if stripped:
                raise InputError(f"line {lineno}: text outside a block: {line[:80]!r}")
            continue
        buf.append(line)
    flush()

    if block is not None and part == "old":
        raise InputError(f"block {block['n']} (input line {block['line']}) has no `{marker} new`")
    if not files:
        raise InputError("no blocks on stdin")
    for path, blocks in files:
        if not blocks:
            raise InputError(f"{path}: no blocks")
        for b in blocks:
            if b["old"] == "":
                raise InputError(f"{path}: block {b['n']}: old text is empty")
            if b["old"] == b["new"]:
                raise InputError(f"{path}: block {b['n']}: old and new are identical")
    return files


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def closest(content, old, limit=3):
    """Lines of content that look like old's first non-blank line."""
    lines = content.split("\n")
    first = next((l for l in old.split("\n") if l.strip()), old)
    key = first.strip()
    exact = [i for i, l in enumerate(lines) if key and key in l]
    if exact:
        idx = exact[:limit]
        why = "first line found at"
    else:
        scored = []
        for i, l in enumerate(lines):
            if not l.strip():
                continue
            r = difflib.SequenceMatcher(None, key, l.strip(), autojunk=False).quick_ratio()
            if r >= 0.6:
                scored.append((r, i))
        scored.sort(reverse=True)
        cand = []
        for _, i in scored[:50]:
            r = difflib.SequenceMatcher(None, key, lines[i].strip(), autojunk=False).ratio()
            if r >= 0.6:
                cand.append((r, i))
        cand.sort(reverse=True)
        idx = sorted(i for _, i in cand[:limit])
        why = "closest lines"
    if not idx:
        return "  no similar line in the file"
    out = [f"  {why}:"]
    for i in idx:
        out.append(f"  {i + 1:>6}: {lines[i][:160]}")
    if exact and len(old.split("\n")) > 1:
        out.append("  (the first line matches; a later line of the old text differs)")
    return "\n".join(out)


def apply(path, blocks, show_diff):
    real = os.path.realpath(path)
    try:
        with open(real, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        raise InputError(f"{path}: no such file (fedit edits existing files; create one with Write or a heredoc)")
    except IsADirectoryError:
        raise InputError(f"{path}: is a directory")
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise InputError(f"{path}: not UTF-8 text ({e})")

    crlf = "\r\n" in content and content.count("\r\n") == content.count("\n")
    if crlf:
        content = content.replace("\r\n", "\n")
    original = content
    reports, errors = [], []

    for b in blocks:
        old, new = b["old"], b["new"]
        count = content.count(old)
        if count == 0:
            errors.append(f"{path}: block {b['n']} (input line {b['line']}): old text not found\n"
                          + closest(content, old))
            continue
        if count > 1 and not b["all"]:
            starts, pos = [], content.find(old)
            while pos != -1 and len(starts) < 10:
                starts.append(str(line_of(content, pos)))
                pos = content.find(old, pos + 1)
            errors.append(f"{path}: block {b['n']} (input line {b['line']}): old text matches "
                          f"{count} times (lines {', '.join(starts)}); add surrounding text to "
                          f"make it unique, or use `old all`")
            continue
        first = content.find(old)
        content = content.replace(old, new)
        start = line_of(content, first)
        n_new = new.count("\n") + 1 if new else 0
        span = f"{start}-{start + n_new - 1}" if n_new > 1 else f"{start}"
        what = (f"replaced x{count}" if count > 1 else "replaced") if new else "deleted"
        reports.append((b["n"], span, what, old.count("\n") + 1, n_new))

    if errors:
        raise MatchError("\n".join(errors))

    diff = ""
    if show_diff:
        diff = "".join(difflib.unified_diff(
            original.splitlines(True), content.splitlines(True),
            fromfile=f"a/{path}", tofile=f"b/{path}"))
    if crlf:
        content = content.replace("\n", "\r\n")
    return real, content.encode("utf-8"), reports, diff


def write_atomic(real, data):
    st = os.stat(real)
    d = os.path.dirname(real) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".fedit-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, st.st_mode & 0o7777)
        try:
            os.chown(tmp, st.st_uid, st.st_gid)
        except PermissionError:
            pass
        os.replace(tmp, real)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    ap = argparse.ArgumentParser(
        prog="fedit", usage="fedit [-n] [-d] [-m M] [FILE] <<'EOF' ... EOF",
        description=__doc__.split("\nOptions:")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="file to edit (or name files with `@@@ file PATH` lines)")
    ap.add_argument("-n", "--dry-run", action="store_true", help="check and report, write nothing")
    ap.add_argument("-d", "--diff", action="store_true", help="print a unified diff of each change")
    ap.add_argument("-m", "--marker", default="@@@", help="marker instead of @@@")
    args = ap.parse_args()

    if sys.stdin.isatty():
        print("fedit: give the blocks on stdin (a heredoc: fedit FILE <<'EOF' ... EOF)", file=sys.stderr)
        return 2
    try:
        files = parse(sys.stdin, args.marker, args.file)
        results, failures = [], []
        for path, blocks in files:
            try:
                results.append((path,) + apply(path, blocks, args.diff))
            except MatchError as e:
                failures.append(str(e))
        if failures:
            print("\n".join(failures), file=sys.stderr)
            print("fedit: nothing written", file=sys.stderr)
            return 1
        seen = {}
        for path, real, data, _, _ in results:
            if real in seen and seen[real] != path:
                raise InputError(f"{path} and {seen[real]} are the same file; put its blocks under one `file` line")
            seen[real] = path
        for path, real, data, reports, diff in results:
            if not args.dry_run:
                write_atomic(real, data)
            for n, span, what, a, b in reports:
                tag = "would be " if args.dry_run else ""
                print(f"{path}:{span}  block {n} {tag}{what} ({a} -> {b} lines)")
            if diff:
                sys.stdout.write(diff)
        if args.dry_run:
            print("fedit: dry run, nothing written")
        return 0
    except InputError as e:
        print(f"fedit: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
