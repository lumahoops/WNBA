# LUMA WNBA Stint and Lineup Data

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21972004.svg)](https://doi.org/10.5281/zenodo.21972004)

LUMA is an open-source project measuring basketball player impact. This repository holds WNBA
lineup-stint data and the ratings derived from it.

Site: https://court-share.com/luma


## Contents

- [Overview](#overview)
- [Files](#files)
- [Record layout](#record-layout)
- [Usage](#usage)
- [Identifiers](#identifiers)
- [Ratings](#ratings)
- [Limitations](#limitations)
- [Licence and citation](#licence-and-citation)

## Overview

| | |
|---|---|
| Coverage | 2003–2026 regular season, 2003–2025 postseason |
| Games | 5,623 |
| Stints | 267,293 |
| Players | 975 |
| Size | 542 files, 96.7 MB |
| Schema | `luma_stints_v2` |

Version 1.0.0, current through 2026-08-15.

## Files

```
data/stints/rs_{2003..2026}.json      regular season
data/stints/po_{2003..2025}.json      postseason
data/crosswalk.csv                    player identifiers
data/quality.json                     per-season diagnostics
data/manifest.json                    SHA-256 per file
data/metrics/arc/                     ratings, per season and career
data/metrics/arc/windows/             multi-year boards, 2 to 5-season spans
data/metrics/rapm/                    pure RAPM, no box prior, all spans
data/metrics/arc/decay/               time-decayed boards, 45-day half-life
data/metrics/od/                      offence and defence components, incl. windows
data/metrics/channels/                on/off decomposition, shot profile, Box+ inputs
src/luma_wnba/           pip-installable loader
llms.txt                 briefing for AI assistants
AGENTS.md                conventions for coding agents
notebooks/quickstart.ipynb
sample/
```

Regular-season and postseason files share no games. Fields are defined in [SCHEMA.md](SCHEMA.md)
and [METRICS.md](METRICS.md).

## Record layout

Each file is an object keyed by game identifier. Each stint is a seven-element array.

```
[home_five, away_five, seconds, home_points, away_points, home_tally, away_tally]
```

```json
{"1022600001": {"date": "2026-05-08", "stints": [
  [["LUMA-W-0000030","LUMA-W-0000033","LUMA-W-0000035","LUMA-W-0000075","LUMA-W-0000120"],
   ["LUMA-W-0000010","LUMA-W-0000078","LUMA-W-0000124","LUMA-W-0000167","LUMA-W-0000172"],
   268.0, 16, 6,
   [3,4,2,2,5,9,1,1,1,2,0,0,6,1,0,0],
   [1,2,4,4,2,0,0,0,4,1,0,0,2,2,1,1]]
]}}
```

The tally counts that team's offensive events during the stint:

```
fga_rim  pts_rim  fga_mid  pts_mid  fga_three  pts_three  fta  pts_ft
tov  oreb  fb_att  fb_pts  ast_pts  tov_pass  tov_handle  tov_sys
```

Positions denote venue, not franchise.

## Usage

### No install — run it in the browser

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lumahoops/WNBA/blob/main/notebooks/quickstart.ipynb)

Click the badge. Nothing to download, no GitHub account, no clone.

### Python

```bash
pip install luma-wnba          # once released on PyPI
pip install https://github.com/lumahoops/WNBA/archive/refs/heads/main.tar.gz   # works today
```

```python
import luma_wnba as luma

games   = luma.load_stints(2026)          # regular season, fetched and cached
games   = luma.load_stints(2024, kind="po")
seconds = luma.player_seconds(games)      # {luma_id: seconds on court}
names   = luma.load_crosswalk()           # {luma_id: identity row}
arc     = luma.load_arc(2026)             # rating board
```

Data is fetched over the network on first use and cached under `~/.cache/luma-wnba`, so no
clone is required. Standard library only — no pandas, no requests. If you have cloned the
repository, local files are used automatically.

Pin a tag for reproducibility:

```python
games = luma.load_stints(2026, ref="v1.0.0")
```

### Full API

<!-- BEGIN GENERATED: api -->
```python
load_stints(season, kind='rs', source='auto', data_dir=None, ref='main')
load_crosswalk(source='auto', data_dir=None, ref='main')
load_metric(name, source='auto', data_dir=None, ref='main')
seasons(kind='rs')
iter_stints(games)
player_seconds(games)
tally_dict(tally)
seconds_to_minutes(secs)
load_arc(season=None, source='auto', data_dir=None, ref='main')
load_rapm(season=None, source='auto', data_dir=None, ref='main')
load_od(season, source='auto', data_dir=None, ref='main')
load_quality(source='auto', data_dir=None, ref='main')
cache_dir(ref='main')
clear_cache()

TALLY = ('fga_rim', 'pts_rim', 'fga_mid', 'pts_mid', 'fga_3', 'pts_3', 'fta', 'pts_ft',
         'tov', 'oreb', 'fb_att', 'fb_pts', 'ast_pts', 'tov_pass', 'tov_handle', 'tov_sys')
RS_SEASONS = 2003..2026
PO_SEASONS = 2003..2025
__version__ = '1.0.0'
```
<!-- END GENERATED: api -->

### Terminal

```bash
luma-wnba top 2026            # minutes leaders
luma-wnba fetch 2025 --kind po
luma-wnba seasons
luma-wnba cache --clear
```

### With ChatGPT or any AI agent

[`llms.txt`](llms.txt) is a briefing you can paste into an assistant so it writes correct code
against this dataset instead of guessing. It lists the complete API, the record shapes and the
rules that matter.

Either paste the file, or give the assistant the URL:

```
Read https://raw.githubusercontent.com/lumahoops/WNBA/main/llms.txt and use it to answer
questions about WNBA lineup data.
```

### R

No R package; the files are plain JSON.

```r
library(jsonlite)
games <- fromJSON("https://raw.githubusercontent.com/lumahoops/WNBA/main/data/stints/rs_2026.json")
```

`sample/` holds five games and a twenty-row rating board.

Possessions, following Oliver:

```python
poss = t[0] + t[2] + t[4] + 0.44 * t[6] + t[8] - t[9]
```

## Identifiers

`LUMA-W-#######`, assigned once and never reused. `crosswalk.csv` maps each to WNBA Stats and
ESPN identifiers, with season span and source scheme.

## Ratings

`data/metrics/` holds ARC, a rating combining a ridge-regularised on/off estimate with a
Box+ component, in points per 100 possessions relative to league average, where
`arc = imp_arc + box_arc`. Channel files decompose the on/off component by shot and possession
category.

## Limitations

- Records carry no team identifier.
- Slots 10 and 11 are zero; the source feeds carry no fastbreak qualifier.
- `home_points` equals the sum of tally scoring slots in 98.1% of records. Where a scoring event
  spans a stint boundary, fields 3 and 4 are authoritative.
- 111 games carry a null date.
- 0.6% of records carry negative `seconds` or points from period-boundary deltas. Game totals
  reconcile; median game duration is 2,400 seconds.
- 2026 derives from a feed with 3.3% less recorded clock time, affecting per-second rates.

## Licence and citation

Data under `data/` is [CC BY 4.0](LICENSE); code is [MIT](CODE-LICENSE.txt). Sources are documented in
[SOURCES.md](SOURCES.md). Not affiliated with the WNBA or ESPN.

```
Awoyemi, A. (2026). LUMA WNBA Stint and Lineup Data (Version 1.0.0) [Data set].
Zenodo. https://doi.org/10.5281/zenodo.21972004
```

[CITATION.cff](CITATION.cff) · aayoawoyemi@gmail.com
