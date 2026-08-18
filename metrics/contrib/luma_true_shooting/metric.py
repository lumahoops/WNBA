"""True shooting, as an example of a metric that measures one skill.

This is deliberately not an impact metric. It scores scoring efficiency only,
so it should correlate weakly with on-court margin. That is the point: the
harness accepts metrics that measure different things, and the scoring makes
their scope visible instead of pretending everything is comparable.
"""
from harness.core import possessions   # noqa: F401  (kept for symmetry)


def metric(ctx):
    """Points per shooting possession, credited to the five on the floor.

    Stint tallies are team-level, not player-level, so this attributes team
    shooting to everyone on court. A better version would need box scores; the
    harness will happily score that too if a contributor brings it.
    """
    pts, att = {}, {}
    for _gid, _date, s in ctx.iter_stints():
        home, away, sec, _hp, _ap, ht, at = s
        if sec <= 0:
            continue
        for five, t in ((home, ht), (away, at)):
            made = t[1] + t[3] + t[5] + t[7]          # pts from rim, mid, three, ft
            shots = t[0] + t[2] + t[4] + 0.44 * t[6]  # true shooting attempts
            if shots <= 0:
                continue
            for pid in five:
                pts[pid] = pts.get(pid, 0.0) + made
                att[pid] = att.get(pid, 0.0) + shots
    return {pid: 100.0 * pts[pid] / (2.0 * att[pid])
            for pid in pts if att[pid] >= 100}
