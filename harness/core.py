"""Scoring engine for contributed metrics.

A contributed metric is any callable that turns training data into one rating
per player. The harness does not care how it is computed. It cares that the
same function, given the same training window, produces ratings that carry
information about outcomes it never saw.

    def metric(ctx) -> dict[luma_id, float]

`ctx` is a TrainContext. Everything a metric may read comes through it, so a
submission cannot accidentally see the holdout.
"""
import json
import os

TALLY_POSS = (0, 2, 4, 6, 8, 9)


def possessions(tally):
    """Oliver's possession estimate from a 16-slot tally."""
    t = tally
    return t[0] + t[2] + t[4] + 0.44 * t[6] + t[8] - t[9]


class TrainContext(object):
    """Read-only view of the training seasons.

    Attributes:
        seasons   list of int, the seasons a metric may learn from
        loader    the luma_wnba module, for load_stints and friends
    """

    def __init__(self, seasons, loader, data_dir=None):
        self.seasons = list(seasons)
        self.loader = loader
        self._data_dir = data_dir
        self._cache = {}

    def stints(self, season=None, kind="rs"):
        """Return stint data for one training season, or all of them merged."""
        if season is None:
            merged = {}
            for s in self.seasons:
                merged.update(self.stints(s, kind))
            return merged
        if season not in self.seasons:
            raise ValueError(
                "season %d is not in the training window %r" % (season, self.seasons))
        key = (season, kind)
        if key not in self._cache:
            self._cache[key] = self.loader.load_stints(
                season, kind=kind, source="local", data_dir=self._data_dir)
        return self._cache[key]

    def crosswalk(self):
        """Player identity rows."""
        return self.loader.load_crosswalk(source="local", data_dir=self._data_dir)

    def iter_stints(self, season=None, kind="rs"):
        """Yield (game_id, date, stint) across the training window."""
        return self.loader.iter_stints(self.stints(season, kind))


def holdout_outcomes(loader, season, data_dir=None, min_minutes=200):
    """Build the target every metric is scored against.

    For each stint in the holdout season, credit the home five with the
    possession-normalised margin and the away five with its negative. A player's
    outcome is their possession-weighted average. This is what actually happened
    while they were on the floor, computed without reference to any metric.
    """
    games = loader.load_stints(season, kind="rs", source="local", data_dir=data_dir)
    num = {}
    den = {}
    secs = {}
    for _gid, _date, s in loader.iter_stints(games):
        home, away, sec, hp, ap, ht, at = s
        if sec <= 0:
            continue
        p = possessions(ht) + possessions(at)
        if p <= 0:
            continue
        margin = (hp - ap) * 100.0 / p
        for pid in home:
            num[pid] = num.get(pid, 0.0) + margin * p
            den[pid] = den.get(pid, 0.0) + p
            secs[pid] = secs.get(pid, 0.0) + sec
        for pid in away:
            num[pid] = num.get(pid, 0.0) - margin * p
            den[pid] = den.get(pid, 0.0) + p
            secs[pid] = secs.get(pid, 0.0) + sec
    out = {}
    for pid, d in den.items():
        if d > 0 and secs.get(pid, 0) / 60.0 >= min_minutes:
            out[pid] = num[pid] / d
    return out


def _rank(values):
    """Average-rank transform, ties shared."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / (sxx * syy) ** 0.5


def score(ratings, outcomes):
    """Compare a metric's ratings to what happened in the holdout season.

    Only players present in both are scored, so a metric is never penalised for
    players it declines to rate, but coverage is reported so that declining to
    rate most of the league is visible.
    """
    shared = [pid for pid in ratings if pid in outcomes]
    if len(shared) < 3:
        return {"error": "only %d players overlap the holdout" % len(shared)}
    xs = [float(ratings[p]) for p in shared]
    ys = [float(outcomes[p]) for p in shared]
    rx, ry = _rank(xs), _rank(ys)
    n = len(shared)
    mean_y = sum(ys) / n
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    # scale-free: rate the ordering, then the linear fit after standardising
    r = _pearson(xs, ys)
    return {
        "n_scored": n,
        "coverage": round(n / float(len(outcomes)), 3),
        "pearson": round(r, 4) if r == r else None,
        "spearman": round(_pearson(rx, ry), 4),
        "r2": round(r * r, 4) if r == r else None,
    }
