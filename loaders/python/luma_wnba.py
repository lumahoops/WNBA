"""Minimal loader for the LUMA WNBA lineup-stint corpus.

No dependencies beyond the standard library.

    from luma_wnba import load_stints, load_crosswalk, player_seconds

    games = load_stints(2026)                 # regular season
    games = load_stints(2024, kind="po")      # playoffs
    names = load_crosswalk()
    secs  = player_seconds(games)
"""
import json
import os
import csv
from collections import defaultdict

# loaders/python/luma_wnba.py -> repo root is two levels up.
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(_HERE, "..", "..", "data"))

# Tally slot names, in order. Both team tallies use this layout.
TALLY = ("fga_rim", "pts_rim", "fga_mid", "pts_mid", "fga_3", "pts_3",
         "fta", "pts_ft", "tov", "oreb", "fb_att", "fb_pts", "ast_pts",
         "tov_pass", "tov_handle", "tov_sys")


def load_stints(season, kind="rs", data_dir=None):
    """Return {game_id: {"date": str|None, "stints": [...]}} for one season.

    kind is "rs" (regular season) or "po" (playoffs). The two never share a
    game, so summing across both is safe.
    """
    if kind not in ("rs", "po"):
        raise ValueError("kind must be 'rs' or 'po'")
    root = data_dir or DATA
    path = os.path.join(root, "stints", "%s_%d.json" % (kind, season))
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_crosswalk(data_dir=None):
    """Return {luma_id: {...}} of player identity rows."""
    root = data_dir or DATA
    out = {}
    with open(os.path.join(root, "crosswalk.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["luma_id"]] = row
    return out


def iter_stints(games):
    """Yield (game_id, date, stint) for every stint in a loaded season."""
    for gid, game in games.items():
        date = game.get("date")
        for stint in game["stints"]:
            yield gid, date, stint


def player_seconds(games):
    """Return {luma_id: seconds on court}. Negative durations are skipped;
    see SCHEMA.md section 4b for why a small number exist."""
    out = defaultdict(float)
    for _, _, (home, away, secs, _hp, _ap, _ht, _at) in iter_stints(games):
        if secs <= 0:
            continue
        for pid in home:
            out[pid] += secs
        for pid in away:
            out[pid] += secs
    return dict(out)


def tally_dict(tally):
    """Turn a 16-slot tally list into a named dict."""
    return dict(zip(TALLY, tally))


if __name__ == "__main__":
    games = load_stints(2026)
    names = load_crosswalk()
    secs = player_seconds(games)
    top = sorted(secs.items(), key=lambda kv: -kv[1])[:10]
    print("2026 regular season, minutes leaders")
    for pid, s in top:
        print("  %-24s %7.1f" % (names[pid]["display_name"], s / 60))
