#!/usr/bin/env python3
"""Regenerate the parts of the docs that are derived from the code.

The public API appears in several places. Keeping them in step by hand does not
work, so this script is the single writer for every generated block.

    python scripts/sync_docs.py           rewrite the generated blocks
    python scripts/sync_docs.py --check   fail if anything is out of date (CI)

A generated block is delimited by markers so the surrounding prose is preserved:

    <!-- BEGIN GENERATED: api -->  ...  <!-- END GENERATED: api -->

Blocks maintained here:
    llms.txt    api          the complete public API surface
    llms.txt    coverage     season ranges and corpus counts
    README.md   api          the same API surface
    AGENTS.md   api          the same API surface
"""
import argparse
import inspect
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import luma_wnba as luma  # noqa: E402


def api_block():
    """Render the public API exactly as the code defines it."""
    lines = []
    for name in luma.__all__:
        obj = getattr(luma, name, None)
        if callable(obj):
            try:
                lines.append("%s%s" % (name, inspect.signature(obj)))
            except (TypeError, ValueError):
                lines.append(name + "(...)")
    consts = [
        "",
        "TALLY = (" + ", ".join(repr(t) for t in luma.TALLY[:8]) + ",",
        "         " + ", ".join(repr(t) for t in luma.TALLY[8:]) + ")",
        "RS_SEASONS = %d..%d" % (min(luma.RS_SEASONS), max(luma.RS_SEASONS)),
        "PO_SEASONS = %d..%d" % (min(luma.PO_SEASONS), max(luma.PO_SEASONS)),
        "__version__ = %r" % luma.__version__,
    ]
    return "```python\n" + "\n".join(lines + consts) + "\n```"


def coverage_block():
    """Render corpus coverage counted from the data on disk."""
    data = os.path.join(ROOT, "data")
    stints = os.path.join(data, "stints")
    rs, po = [], []
    n_games = n_stints = 0
    for fn in sorted(os.listdir(stints)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(stints, fn), encoding="utf-8") as fh:
            games = json.load(fh)
        n_games += len(games)
        n_stints += sum(len(g["stints"]) for g in games.values())
        if not games:
            continue          # empty placeholder for a season not yet played
        (rs if fn.startswith("rs_") else po).append(int(fn[3:7]))
    rs, po = sorted(rs), sorted(po)
    with open(os.path.join(data, "crosswalk.csv"), encoding="utf-8") as fh:
        n_players = sum(1 for _ in fh) - 1
    return (
        "| | |\n|---|---|\n"
        "| Regular season | %d-%d |\n"
        "| Postseason | %d-%d |\n"
        "| Games | %s |\n"
        "| Stints | %s |\n"
        "| Players | %s |\n"
        % (min(rs), max(rs), min(po), max(po),
           format(n_games, ","), format(n_stints, ","), format(n_players, ","))
    )


BLOCKS = {"api": api_block, "coverage": coverage_block}

TARGETS = [
    ("llms.txt", ["api", "coverage"]),
    ("README.md", ["api"]),
    ("AGENTS.md", ["api"]),
]


def apply(path, names, check):
    """Rewrite or verify every generated block in one file."""
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        return []
    with open(full, encoding="utf-8") as fh:
        text = original = fh.read()
    problems = []
    for name in names:
        begin = "<!-- BEGIN GENERATED: %s -->" % name
        end = "<!-- END GENERATED: %s -->" % name
        pattern = re.compile(
            re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
        if not pattern.search(text):
            problems.append("%s: missing marker for '%s'" % (path, name))
            continue
        body = BLOCKS[name]()
        text = pattern.sub(begin + "\n" + body + "\n" + end, text)
    if text != original:
        if check:
            problems.append("%s: generated block is out of date" % path)
        else:
            with open(full, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print("updated", path)
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if anything is stale")
    args = ap.parse_args(argv)

    problems = []
    for path, names in TARGETS:
        problems.extend(apply(path, names, args.check))

    if problems:
        for p in problems:
            print("ERROR:", p, file=sys.stderr)
        if args.check:
            print("\nRun: python scripts/sync_docs.py", file=sys.stderr)
        return 1
    print("docs in sync" if args.check else "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
