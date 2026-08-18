"""Possession-weighted on/off margin, the simplest honest baseline.

Every contributed metric looks like this: one function, takes a TrainContext,
returns {luma_id: rating}. Nothing else is required.
"""
from harness.core import possessions


def metric(ctx):
    """Average point margin per 100 possessions while the player was on court."""
    num, den = {}, {}
    for _gid, _date, s in ctx.iter_stints():
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
        for pid in away:
            num[pid] = num.get(pid, 0.0) - margin * p
            den[pid] = den.get(pid, 0.0) + p
    # 300 possessions of regularisation toward zero, so tiny samples do not top the board
    return {pid: num[pid] / (den[pid] + 300.0) for pid in num if den[pid] > 0}
