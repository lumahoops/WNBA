# LUMA WNBA Stint and Lineup Data

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21972004.svg)](https://doi.org/10.5281/zenodo.21972004)

LUMA is an open-source project measuring basketball player impact. This repository holds WNBA
lineup-stint data and the ratings derived from it.

Stints are intervals during which both teams' five-player lineups remain unchanged, reconstructed
here from play-by-play substitution events. They are the input to on/off and regularised
plus-minus estimation.

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
| Size | 171 files, 85.6 MB |
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
data/metrics/od/                      offence and defence components
data/metrics/channels/                on/off decomposition, shot profile, Box+ inputs
loaders/python/luma_wnba.py
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

```python
from luma_wnba import load_stints, load_crosswalk, player_seconds

games = load_stints(2026)               # regular season
games = load_stints(2024, kind="po")    # postseason
seconds = player_seconds(games)         # {luma_id: seconds on court}
```

Standard library only. `sample/` holds five games and a twenty-row rating board.

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
