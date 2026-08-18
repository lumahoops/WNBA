"""Loader for the LUMA WNBA lineup-stint corpus. Stdlib only.

  pip install luma-wnba
  from luma_wnba import load_stints
  games = load_stints(2026)
"""

import collections
import json
import os
import csv
import io
import shutil
import urllib.request
import urllib.error

__version__ = "1.0.1"
DEFAULT_REF = "main"
BASE_URL = "https://raw.githubusercontent.com/lumahoops/WNBA/{ref}/data"
TALLY = (
    "fga_rim", "pts_rim", "fga_mid", "pts_mid", "fga_3", "pts_3",
    "fta", "pts_ft", "tov", "oreb", "fb_att", "fb_pts", "ast_pts",
    "tov_pass", "tov_handle", "tov_sys"
)
RS_SEASONS = list(range(2003, 2027))
PO_SEASONS = list(range(2003, 2026))


def cache_dir(ref=DEFAULT_REF):
    """Return cache directory path, creating it if necessary."""
    env_cache = os.environ.get("LUMA_WNBA_CACHE")
    if env_cache:
        base = env_cache
    else:
        base = os.path.join(os.path.expanduser("~"), ".cache", "luma-wnba")
    path = os.path.join(base, ref)
    os.makedirs(path, exist_ok=True)
    return path


def clear_cache():
    """Remove the entire ~/.cache/luma-wnba directory and return its path."""
    cache_path = os.path.join(os.path.expanduser("~"), ".cache", "luma-wnba")
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    return cache_path


def _local_root():
    """Return local data directory from env or relative to this file."""
    env_data = os.environ.get("LUMA_WNBA_DATA")
    if env_data and os.path.isdir(env_data):
        return env_data
    current = os.path.abspath(__file__)
    for _ in range(5):
        current = os.path.dirname(current)
        candidate = os.path.join(current, "data")
        if os.path.isdir(candidate):
            return candidate
    return None


def _fetch(relpath, ref):
    """Fetch a file from the remote repository and cache it."""
    cached = os.path.join(cache_dir(ref), relpath.replace("/", os.sep))
    if os.path.exists(cached):
        with open(cached, "rb") as f:
            return f.read()
    url = BASE_URL.format(ref=ref) + "/" + relpath
    req = urllib.request.Request(
        url, headers={"User-Agent": f"luma-wnba/{__version__}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e.reason}") from e
    os.makedirs(os.path.dirname(cached), exist_ok=True)
    with open(cached, "wb") as f:
        f.write(data)
    return data


def _read(relpath, source="auto", data_dir=None, ref=DEFAULT_REF):
    """Read a data file from local or remote source."""
    if source not in ("auto", "local", "remote"):
        raise ValueError("source must be 'auto', 'local', or 'remote'")
    root = data_dir or _local_root()
    if source == "remote":
        return _fetch(relpath, ref)
    relpath_os = relpath.replace("/", os.sep)
    p = os.path.join(root, relpath_os) if root else None
    if source == "local":
        if p is None or not os.path.isfile(p):
            raise FileNotFoundError(
                "Local data not found. Pass source='remote' or set "
                "LUMA_WNBA_DATA environment variable."
            )
        with open(p, "rb") as f:
            return f.read()
    # auto
    if p is not None and os.path.isfile(p):
        with open(p, "rb") as f:
            return f.read()
    return _fetch(relpath, ref)


def load_stints(season, kind="rs", source="auto", data_dir=None, ref=DEFAULT_REF):
    """Return {game_id: {"date":..., "stints":[...]}} for one season."""
    if kind not in ("rs", "po"):
        raise ValueError("kind must be 'rs' or 'po'")
    relpath = "stints/%s_%d.json" % (kind, season)
    return json.loads(_read(relpath, source, data_dir, ref).decode("utf-8"))

def load_crosswalk(source="auto", data_dir=None, ref=DEFAULT_REF):
    """Return {luma_id: row dict} of player identity rows."""
    text = _read("crosswalk.csv", source, data_dir, ref).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return {row["luma_id"]: row for row in reader}

def load_metric(name, source="auto", data_dir=None, ref=DEFAULT_REF):
    """Load a metric board by path, e.g. 'arc/arc_2026' (no .json)."""
    relpath = "metrics/" + name + ".json"
    return json.loads(_read(relpath, source, data_dir, ref).decode("utf-8"))

def seasons(kind="rs"):
    """Return the list of available seasons for 'rs' or 'po'."""
    if kind not in ("rs", "po"):
        raise ValueError("kind must be 'rs' or 'po'")
    return list(RS_SEASONS) if kind == "rs" else list(PO_SEASONS)

def iter_stints(games):
    """Yield (game_id, date, stint) for every stint in a loaded season."""
    for game_id, info in games.items():
        date = info.get("date")
        for stint in info["stints"]:
            yield (game_id, date, stint)

def player_seconds(games):
    """Return {luma_id: seconds on court}; non-positive stints skipped."""
    result = collections.defaultdict(float)
    for _gid, _date, stint in iter_stints(games):
        home, away, secs, _hp, _ap, _ht, _at = stint
        if secs <= 0:
            continue
        for pid in home:
            result[pid] += secs
        for pid in away:
            result[pid] += secs
    return dict(result)

def tally_dict(tally):
    """Turn a 16-slot tally list into a named dict."""
    return dict(zip(TALLY, tally))


def load_arc(season=None, source="auto", data_dir=None, ref=DEFAULT_REF):
    """Load an ARC rating board. season=None gives the all-time board."""
    name = "arc/alltime" if season is None else "arc/season_%d" % season
    return load_metric(name, source, data_dir, ref)


def load_rapm(season=None, source="auto", data_dir=None, ref=DEFAULT_REF):
    """Load a pure-RAPM board (no box prior). season=None gives all-time."""
    name = "rapm/alltime" if season is None else "rapm/season_%d" % season
    return load_metric(name, source, data_dir, ref)


def load_od(season, source="auto", data_dir=None, ref=DEFAULT_REF):
    """Load the offence/defence split for one season."""
    return load_metric("od/%d" % season, source, data_dir, ref)


def load_quality(source="auto", data_dir=None, ref=DEFAULT_REF):
    """Load per-season data-quality diagnostics."""
    return json.loads(_read("quality.json", source, data_dir, ref).decode("utf-8"))


def seconds_to_minutes(secs):
    """Convert seconds to minutes, rounded to one decimal."""
    return round(secs / 60.0, 1)


# MAINTENANCE
# __all__ below is the documented public surface. It is read by
# scripts/sync_docs.py, which regenerates the API listing in llms.txt,
# README.md and AGENTS.md. If you add, remove or rename anything here, run
#     python scripts/sync_docs.py
# CI (.github/workflows/verify.yml, job docs-in-sync) fails the build if the
# docs do not match this module.

__all__ = [
    "load_stints", "load_crosswalk", "load_metric", "seasons",
    "iter_stints", "player_seconds", "tally_dict", "seconds_to_minutes",
    "load_arc", "load_rapm", "load_od", "load_quality",
    "cache_dir", "clear_cache", "TALLY",
    "RS_SEASONS", "PO_SEASONS", "DEFAULT_REF", "__version__",
]
