"""Run a contributed metric: validate it, test it, or score it.

    python harness/run.py --metric metrics/contrib/luma_arc --test
    python harness/run.py --metric metrics/contrib/luma_arc --holdout 2026
    python harness/run.py --all --holdout 2026 --json results.json

Three modes, because a contributor needs to iterate long before they care about
a leaderboard:

  --validate  does it load, declare itself, and return the right shape
  --test      run it on a tiny slice and show the ratings, no scoring
  --holdout   score it against a season it never saw

Dependencies are declared in meta.yml. The harness reports what a metric needs
and refuses to run if something is missing, rather than failing obscurely deep
inside somebody else's code.
"""
import argparse
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)

import luma_wnba  # noqa: E402
from harness import core  # noqa: E402

DATA = os.path.join(ROOT, "data")


def read_meta(path):
    """Parse meta.yml without a yaml dependency: flat key: value pairs and
    simple lists written as '- item' under a key."""
    meta = {}
    key = None
    if not os.path.exists(path):
        return meta
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip()
            if not line.strip() or line.strip().startswith("#"):
                continue
            if line.lstrip().startswith("- ") and key:
                meta.setdefault(key, [])
                if not isinstance(meta[key], list):
                    meta[key] = []
                meta[key].append(line.split("- ", 1)[1].strip())
            elif ":" in line:
                k, v = line.split(":", 1)
                key = k.strip()
                v = v.strip()
                meta[key] = v if v else []
    return meta


def check_requirements(meta):
    """Return the list of declared imports that are not importable."""
    missing = []
    reqs = meta.get("requires") or []
    if isinstance(reqs, str):
        reqs = [r.strip() for r in reqs.split(",") if r.strip()]
    for r in reqs:
        mod = r.split("==")[0].split(">=")[0].split("[")[0].strip()
        mod = {"scikit-learn": "sklearn", "pyyaml": "yaml"}.get(mod, mod)
        try:
            __import__(mod)
        except ImportError:
            missing.append(r)
    return missing


def load_metric(path):
    """Import metric.py from a submission directory and return (fn, meta)."""
    meta = read_meta(os.path.join(path, "meta.yml"))
    src = os.path.join(path, "metric.py")
    if not os.path.exists(src):
        raise SystemExit("no metric.py in %s" % path)
    import importlib.util
    name = "contrib_" + os.path.basename(path.rstrip("/\\"))
    spec = importlib.util.spec_from_file_location(name, src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    fn = getattr(mod, "metric", None)
    if not callable(fn):
        raise SystemExit("%s/metric.py defines no callable named 'metric'" % path)
    return fn, meta


def validate_shape(ratings):
    """A metric must return {luma_id: number} and nothing stranger."""
    if not isinstance(ratings, dict):
        return "metric returned %s, expected a dict" % type(ratings).__name__
    if not ratings:
        return "metric returned an empty dict"
    for k, v in list(ratings.items())[:2000]:
        if not isinstance(k, str) or not k.startswith("LUMA-"):
            return "key %r is not a LUMA player id" % (k,)
        try:
            f = float(v)
        except (TypeError, ValueError):
            return "value for %s is %r, not a number" % (k, v)
        if f != f:
            return "value for %s is NaN" % k
    return None


def run_one(path, holdout, train_years, mode):
    """Validate, test or score a single submission."""
    name = os.path.basename(path.rstrip("/\\"))
    result = {"metric": name, "path": path}
    fn, meta = load_metric(path)
    result["meta"] = meta

    missing = check_requirements(meta)
    if missing:
        result["error"] = "missing declared dependencies: %s" % ", ".join(missing)
        return result

    seasons = [y for y in luma_wnba.seasons("rs") if y < holdout]
    if train_years:
        seasons = seasons[-train_years:]
    if mode == "test":
        seasons = seasons[-2:]        # small slice, fast feedback
    result["train_seasons"] = [seasons[0], seasons[-1]] if seasons else []

    ctx = core.TrainContext(seasons, luma_wnba, data_dir=DATA)
    t0 = time.time()
    try:
        ratings = fn(ctx)
    except Exception:
        result["error"] = "metric raised:\n" + traceback.format_exc(limit=6)
        return result
    result["seconds"] = round(time.time() - t0, 2)

    problem = validate_shape(ratings)
    if problem:
        result["error"] = problem
        return result
    result["n_rated"] = len(ratings)

    if mode in ("validate", "test"):
        cw = luma_wnba.load_crosswalk(source="local", data_dir=DATA)
        top = sorted(ratings.items(), key=lambda kv: -kv[1])[:10]
        result["sample"] = [
            {"player": cw.get(p, {}).get("display_name", p), "rating": round(float(v), 3)}
            for p, v in top]
        return result

    outcomes = core.holdout_outcomes(luma_wnba, holdout, data_dir=DATA)
    result["holdout"] = holdout
    result["holdout_players"] = len(outcomes)
    result.update(core.score(ratings, outcomes))
    return result


def discover(root):
    """Every submission directory under metrics/contrib."""
    base = os.path.join(ROOT, root)
    if not os.path.isdir(base):
        return []
    return [os.path.join(base, d) for d in sorted(os.listdir(base))
            if os.path.isdir(os.path.join(base, d))]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metric", help="path to a submission directory")
    ap.add_argument("--all", action="store_true", help="run every submission")
    ap.add_argument("--holdout", type=int, default=2026,
                    help="season held out from training and scored against")
    ap.add_argument("--train-years", type=int, default=0,
                    help="limit training to the most recent N seasons, 0 for all")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--json", help="write results to this file")
    args = ap.parse_args(argv)

    mode = "test" if args.test else ("validate" if args.validate else "score")
    paths = discover("metrics/contrib") if args.all else ([args.metric] if args.metric else [])
    if not paths:
        ap.error("pass --metric PATH or --all")

    results = []
    for p in paths:
        try:
            results.append(run_one(p, args.holdout, args.train_years, mode))
        except SystemExit as e:
            results.append({"metric": os.path.basename(p), "error": str(e)})

    report(results, mode)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
        print("\nwrote", args.json)
    return 1 if any("error" in r for r in results) else 0


def report(results, mode):
    """Print a human-readable summary, and a leaderboard when scoring."""
    for r in results:
        print("\n=== %s ===" % r["metric"])
        meta = r.get("meta") or {}
        if meta.get("measures"):
            print("measures :", meta["measures"])
        if meta.get("author"):
            print("author   :", meta["author"])
        if r.get("train_seasons"):
            print("trained  : %s-%s" % tuple(r["train_seasons"]))
        if "error" in r:
            print("ERROR    :", r["error"])
            continue
        print("rated    : %d players in %ss" % (r["n_rated"], r.get("seconds")))
        if r.get("sample"):
            for s in r["sample"][:5]:
                print("    %-24s %8.3f" % (s["player"], s["rating"]))
        if mode == "score" and "spearman" in r:
            print("holdout  : %d, %d qualified players" % (r["holdout"], r["holdout_players"]))
            print("coverage : %.1f%%" % (100 * r["coverage"]))
            print("spearman : %s   pearson: %s" % (r["spearman"], r["pearson"]))

    scored = [r for r in results if r.get("spearman") is not None and "error" not in r]
    if mode == "score" and len(scored) > 1:
        print("\n=== leaderboard, holdout %d ===" % scored[0]["holdout"])
        print("%-28s %9s %9s %9s" % ("metric", "spearman", "pearson", "coverage"))
        for r in sorted(scored, key=lambda r: -(r["spearman"] or -9)):
            print("%-28s %9.4f %9.4f %8.1f%%" % (
                r["metric"], r["spearman"], r["pearson"], 100 * r["coverage"]))


if __name__ == "__main__":
    sys.exit(main())
