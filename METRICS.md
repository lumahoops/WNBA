# METRICS.md — LUMA WNBA Stint and Lineup Data — Metric Boards

**Schema version:** `luma_metrics_v1` · **Rating version:** ARC v2
Companion to [SCHEMA.md](SCHEMA.md), which documents the stint data these are computed from.

All files key on `LUMA-W-#######` identifiers. See `crosswalk.csv` for the mapping to
WNBA Stats and ESPN identifiers.

---

## 1. Files

```
data/metrics/
  arc/alltime.json                    career board, 2003-2026, 525 players
  arc/season_{2003..2026}.json        24 single-season boards
  arc/playoffs.json                   postseason board, 2003-2025
  arc/windows/{n}yr_{y0}_{y1}.json    84 multi-year boards, 2 to 5-season spans
  arc/decay/{y0}_{y1}_asof{d}_hl{h}.json  26 time-decayed boards
  arc/playoffs_windows/{y0}_{y1}.json 12 postseason boards by span
  rapm/season_{2003..2026}.json       pure RAPM, no box prior, 24 seasons
  rapm/windows/{n}yr_{y0}_{y1}.json   86 multi-year pure-RAPM boards
  rapm/alltime.json                   pure RAPM, 2003-2026
  od/{2003..2026}.json                offence/defence split, 24 seasons
  od/windows/{n}yr_{y0}_{y1}.json     85 multi-year splits
  od/playoffs/                        12 postseason splits
  channels/leaffactor_{yr}.json       24 on/off channels per player
  channels/fingerprint_{yr}.json      shot-profile rates
  channels/boxfactors_{yr}.json       Box+ inputs
  channels/boxdecomp_{yr}.json        Box+ broken into contributing terms
  manifest.json                       SHA-256 per file, row counts, export timestamp
```

476 files.

## 2b. Pure RAPM

`rapm/` holds the ridge solve with no box-score prior. ARC's `impact` term folds a box-BPM prior
in at weight 0.25; setting that weight to zero leaves the estimate the stint data alone supports.

```json
{"luma_id": "LUMA-W-0000059", "rapm": 3.99, "poss": 2109.0}
```

| Field | Meaning |
|---|---|
| `rapm` | Ridge-regularised plus-minus, points per 100 possessions, alpha 3000 |
| `poss` | Possessions the player was on court for, the weight behind the estimate |

Board metadata records `alpha`, the seasons pooled, and `prior: null`.

Pure RAPM correlates 0.917 with ARC's `impact` on the 2026 board and carries a smaller spread
(SD 1.21 against 1.54), which is the prior's contribution removed. Use `rapm/` where a
prior-free estimate is wanted; use `arc/` where the box component is wanted.

### Windows

A board covering more than one season pools the stints of those seasons into a single fit rather
than averaging separate season boards. Spans of 2, 3, 4 and 5 seasons are provided, along with the
full 2003-2026 board in `arc/alltime.json`. Longer spans carry more possessions per player and
therefore narrower intervals, at the cost of treating a player as constant across the window.

### Time decay

Files under `arc/decay/` weight each possession by recency: a possession `d` days before the
as-of date carries weight `0.5 ** (d / halflife)`. The half-life is 45 days and is recorded in
the filename and in the board's `halflife` field. These boards answer what a player's rating was
at a point in the season rather than at its end, so they are the ones to use for in-season
tracking. The `asof` field states the evaluation date.

---

## 2. ARC v2 boards

**ARC** (Adjusted Rating Contribution) combines a ridge-regularised on/off impact estimate with
a Box+ component.

```json
{"rank": 1, "name": "A'ja Wilson", "team": "LV", "arc": 12.11,
 "imp_arc": 9.64, "box_arc": 2.47, "impact": 6.53, "boxplus": 15.8,
 "gp": 32, "luma_id": "LUMA-W-0000059"}
```

| Field | Meaning |
|---|---|
| `luma_id` | Player identifier |
| `rank` | Position on this board |
| `name` | Display name at time of export |
| `team` | Team abbreviation. **Season boards only** — omitted from `alltime` and `playoffs`, where a single team value would be misleading |
| `arc` | Total rating. `arc = imp_arc + box_arc` exactly |
| `imp_arc` | On/off component after ridge regularisation and scaling |
| `box_arc` | Box+ component after scaling |
| `impact` | Raw regularised on/off estimate, before scaling |
| `boxplus` | Raw Box+ estimate, before scaling |
| `gp` | Games played in the window |

Units are points per 100 possessions relative to a league-average player. The additive identity `arc == imp_arc + box_arc` holds in **100.00% of 4,998 rows** across all
26 boards, to rounding (worst absolute difference 0.010). It is the check to run first.

### Estimation

ARC v2. Ridge regression on the stint data, alpha 3000, with a Box+ prior weighted 0.25.
Regular-season boards weight the on/off and Box+ components 0.80/0.20. The playoff board inverts
toward the Box+ side, since a postseason contains too few possessions for a regularised on/off
estimate to stand alone.

The 0.80/0.20 weighting is applied to the raw components. Because the two axes have different
spreads — Box+ has a standard deviation of 4.15 against Impact's 1.80 across 3,225 qualified
player-seasons — the nominal weights do not describe the information split. In variance terms:

| nominal | Impact share | Box+ share | shared |
|---|---|---|---|
| 0.90 / 0.10 | 69.9% | 4.6% | 25.5% |
| **0.80 / 0.20** | **46.4%** | **15.4%** | **38.2%** |
| 0.70 / 0.30 | 29.5% | 28.8% | 41.6% |
| 0.50 / 0.50 | 10.4% | 55.3% | 34.2% |

Expressed on a standardised scale, the published 0.80/0.20 is a 0.63/0.37 split. A true
equal-variance blend falls at approximately 0.70/0.30 nominal.

The two axes correlate at 0.713, so 49% of Box+ variance is independent of Impact. Neither axis
subsumes the other.

Three measurements of the weighting on WNBA data.

Same-season reconstruction of team net rating, 266 team-seasons:

| configuration | r | R² | MAE |
|---|---|---|---|
| Impact alone | 0.944 | 0.891 | 1.29 |
| 0.90 / 0.10 | 0.940 | 0.884 | 1.34 |
| **0.80 / 0.20** | **0.933** | **0.870** | **1.44** |
| 0.65 / 0.35 | 0.914 | 0.835 | 1.65 |
| Box+ alone | 0.777 | 0.604 | 2.68 |

Out of sample, rating from one season scored against the next, 252 team-seasons:

| configuration | r | R² |
|---|---|---|
| Impact alone | 0.590 | 0.348 |
| **0.90 / 0.10** | **0.592** | **0.350** |
| 0.80 / 0.20 | 0.587 | 0.345 |
| 0.65 / 0.35 | 0.570 | 0.325 |
| Box+ alone | 0.457 | 0.208 |

Out of sample at single-game resolution, 2,151 games, the optimum moves to 0.70/0.30 (r 0.255),
with both single-axis configurations lower — Impact alone 0.245, Box+ alone 0.225. Single-game
margin is dominated by noise and R² there is 0.065, but the ordering shows the blend carrying
information neither axis holds alone.

The differences between adjacent weightings are inside sampling error. Bootstrapping the
season-level out-of-sample correlation over 252 team-seasons gives 0.5917 for 0.90/0.10 against
0.5869 for 0.80/0.20, with 95% intervals of [0.511, 0.663] and [0.504, 0.664]. In paired
resampling 0.90/0.10 ranks higher in 80% of draws, short of a decisive separation.

The Box+ weight does not improve accuracy for players with limited samples. Scoring each player's
rating against that player's own on-court margin the following season:

| games played | n | 1.00/0.00 | 0.90/0.10 | 0.80/0.20 | 0.70/0.30 |
|---|---|---|---|---|---|
| under 15 | 141 | 0.213 | 0.206 | 0.197 | 0.189 |
| 15 to 25 | 345 | 0.253 | 0.251 | 0.244 | 0.236 |
| over 25 | 1,877 | 0.391 | 0.390 | 0.381 | 0.369 |

Impact alone leads in every bucket, including the smallest samples.

What the Box+ weight buys is stability. Year-over-year self-consistency of a player's rating,
2,204 player-pairs with at least 15 games in both seasons:

| blend | r(Y, Y+1) |
|---|---|
| 1.00 / 0.00 | 0.540 |
| 0.90 / 0.10 | 0.610 |
| **0.80 / 0.20** | **0.664** |
| 0.70 / 0.30 | 0.702 |
| 0.50 / 0.50 | 0.743 |

The weighting therefore trades a small amount of accuracy for a substantial gain in consistency: a
rating that swings less between seasons at a cost of roughly 0.01 in correlation. 0.80/0.20 is
that trade. Users preferring maximum accuracy can recompute from `imp_arc` and `box_arc`, which
are published separately on every row.

Roster continuity bounds the out-of-sample figures: 82.9% of a season's minutes are played by
players carrying a rating from the prior season.

Schedule strength is not adjusted for. Across 300 team-seasons the standard deviation of
opponent quality faced is 0.95 points per 100 possessions against a team-quality standard
deviation of 5.80, a ratio of 0.16, with every team facing every other team. The regularised
on/off component absorbs the remainder.

### Versioning

The Box+ formula and the blend are versioned together as the rating version. This release is
ARC v2. The rating version is recorded in `manifest.json`. Successive versions are published as separate
releases; a board row never changes meaning within a version.

---

## 3. Offence / defence split

`od/{season}.json` keys on `luma_id` and separates the impact estimate into offensive and
defensive halves, estimated jointly rather than as two independent regressions.

---

## 4. Channel decompositions

### leaffactor — 24 channels per player

Attributes a player's on/off effect to specific shot and possession categories. Offensive
channels carry an `o` prefix, defensive a `d` — the defensive channels describe what the
player's defence allowed. Two summary fields, `O` and `D`, carry the offensive and defensive
totals.

```
oMake_rim   oSel_rim     Making, and shot selection, at the rim
oMake_mid   oSel_mid     Mid-range
oMake_thr   oSel_thr     Three-point
oMake_ft    oSel_ft      Free throws
oTOV        oREB         Turnovers, rebounding
oPACE                    Pace
dMake_rim   dSel_rim     Defensive mirror of each offensive channel
dMake_mid   dSel_mid
dMake_thr   dSel_thr
dMake_ft    dSel_ft
dTOV        dREB
dPACE
O           D            Offensive and defensive totals
```

**Make** channels separate shot-making from **Sel** (selection) channels, which capture where
shots were taken. A player who improves a team's rim rate without improving rim accuracy shows
up in `oSel_rim`, not `oMake_rim`.

Units match ARC — points per 100 possessions. Channels are additive within a season.

### fingerprint — shot profile

```json
{"rimRate": {"off": -0.641, "def_allowed": -0.564},
 "midRate": {"off": -0.637, "def_allowed": 1.342},
 "thrRate": {"off": 0.724,  "def_allowed": 0.378}, …}
```

Standardised rates, offence and defence-allowed, by zone. Describes tendency rather than value.

### boxfactors

Per-player box-score inputs feeding the Box+ prior in the regression: `ts`, `usg`, `tovp`, `orbp`, `drbp`,
`stlp`, `blkp`, `3par`, `ftr`, `obpm`, `dbpm`, `mins`, among others.

---

## 5. Interpretation

A board summarises what occurred while a player was on court, after regularisation to reduce the
influence of lineup context and sample size. Values are on the points-per-100-possessions scale
and are comparable within a season and across seasons.

Single-season boards for players below roughly 300 minutes carry wide intervals; `gp` is included
on every row so the reader can weight accordingly. Postseason boards weight the Box+ component
more heavily, since a postseason contains too few possessions for a regularised on/off estimate
to stand alone.

---

## 6. Stability

`luma_metrics_v1` field names will not change meaning. New information arrives as new fields or
new files. Boards are recomputed when the underlying stints change; `manifest.json` carries a
SHA-256 per file so a change is detectable.

Identifiers are permanent. A board row's `luma_id` refers to the same player in every release.
