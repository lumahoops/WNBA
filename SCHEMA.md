# SCHEMA

Field definitions for the LUMA WNBA Stint and Lineup Data. Schema version `luma_stints_v2`.

- [Files](#files)
- [Stint record](#stint-record)
- [Tally vector](#tally-vector)
- [Identities](#identities)
- [Derived quantities](#derived-quantities)
- [Coverage](#coverage)
- [quality.json](#qualityjson)
- [Stability](#stability)

## Files

| Path | Contents |
|---|---|
| `data/stints/rs_{season}.json` | Regular season, 2003–2026 |
| `data/stints/po_{season}.json` | Postseason, 2003–2025 |
| `data/crosswalk.csv` | Player identifiers |
| `data/quality.json` | Per-season reconstruction diagnostics |
| `data/manifest.json` | SHA-256, row count and schema version per file |

`season` is the calendar year of play. Regular-season and postseason files share no games.
Encoding is UTF-8 throughout.

Each file is a JSON object keyed by ESPN game identifier:

```json
{"1022600001": {"date": "2026-05-08", "stints": [ ... ]}}
```

| Field | Type | Description |
|---|---|---|
| `date` | string or null | Game date, `YYYY-MM-DD`. Null for 111 games, mostly 2003–2005. |
| `stints` | array | Stint records in chronological order. |

## Stint record

A stint is an interval during which both five-player lineups remain unchanged. Each record is a
seven-element array.

| Index | Field | Type | Description |
|---|---|---|---|
| 0 | `home_five` | array | Five player identifiers, home side, sorted |
| 1 | `away_five` | array | Five player identifiers, away side, sorted |
| 2 | `seconds` | float | Elapsed game time |
| 3 | `home_points` | int | Points scored by the home side |
| 4 | `away_points` | int | Points scored by the away side |
| 5 | `home_tally` | array | Sixteen integers, home offence |
| 6 | `away_tally` | array | Sixteen integers, away offence |

Position denotes venue, not franchise. A player appears on both the home and away side across a
season; in 2026, 212 of 226 players do. Join on the game identifier to recover team.

Lineups carry no positional information. Stints are cut at substitutions and at period
boundaries, so a period never spans two stints. Overtime periods are included; 761 games run past
regulation, the longest to 3,728 seconds.

Records with fewer than five identifiers per side are retained rather than padded. Four such
slots exist in 534,586. Filter on `len(row[0]) == 5` where strict lineups are required.

## Tally vector

Sixteen integers counting the events produced by that team's offence during the stint. The layout
matches the NBA dataset, so one reader serves both.

| Index | Field | Description |
|---|---|---|
| 0 | `fga_rim` | Two-point attempts within 4 ft of the basket |
| 1 | `pts_rim` | Points from rim attempts |
| 2 | `fga_mid` | Two-point attempts beyond 4 ft |
| 3 | `pts_mid` | Points from non-rim two-point attempts |
| 4 | `fga_three` | Three-point attempts |
| 5 | `pts_three` | Points from three-point attempts |
| 6 | `fta` | Free-throw attempts |
| 7 | `pts_ft` | Points from free throws |
| 8 | `tov` | Turnovers, all types |
| 9 | `oreb` | Offensive rebounds |
| 10 | `fb_att` | Fastbreak attempts. Always zero. |
| 11 | `fb_pts` | Fastbreak points. Always zero. |
| 12 | `ast_pts` | Points from assisted field goals |
| 13 | `tov_pass` | Turnovers on a bad pass |
| 14 | `tov_handle` | Turnovers on ball handling |
| 15 | `tov_sys` | Turnovers on clock and team violations |

Shot location is taken from the event coordinates carried by the source feed. Three-point
attempts are identified by scoring value rather than distance. Where coordinates are absent, the
classification falls back to the play-type description.

Slots 10 and 11 are zero because neither source feed carries a fastbreak qualifier. They are
retained for index compatibility with the NBA dataset.

Slot 8 is the authoritative turnover count. Slots 13 to 15 partition it; unclassified turnovers
are assigned to `tov_handle`, matching the NBA dataset.

Offensive rebounds exclude team and deadball rebounds. Free-throw attempts count every shot taken,
made or missed. Assisted points are credited to the scoring team.

### Identities

Two identities hold within each record:

```
home_points == t[1] + t[3] + t[5] + t[7]      98.11% of records
t[8]        == t[13] + t[14] + t[15]         100.00% of records
```

The scoring identity fails where an event's team attribution or timestamp falls outside the stint
window. Fields 3 and 4 are authoritative for score.

### Row-level artefacts

| Artefact | Rate | Origin |
|---|---|---|
| Negative `seconds` | 145 records | Clock deltas across a period boundary |
| Negative points | 1,541 records | Score deltas across a period boundary |
| Lineups of four | 4 slots of 534,586 | Incomplete substitution sequence |

Game totals reconcile; these offset within a game. Median game duration is 2,400 seconds, with
86.1% of games within 5% of that figure. For per-stint work, filter `seconds > 0`.

## Identities

Player identifiers take the form `LUMA-W-#######`, assigned once and never reused or renumbered.
The prefix namespaces the league.

`crosswalk.csv` carries one row per identifier:

| Column | Description |
|---|---|
| `luma_id` | LUMA identifier |
| `display_name` | Name as published by the source feed |
| `wnba_stats_id` | WNBA Stats identifier, where resolved |
| `espn_id` | ESPN identifier, where resolved |
| `first_season`, `last_season` | Observed season span |
| `n_seasons` | Distinct seasons with recorded time |
| `source_scheme` | `both`, `wnba_stats`, or `espn` |

224 of 975 players resolve to both source identifiers. An identifier found to be invalid is
retired: removed from the crosswalk and from every export, with its number never reissued. One
retirement to date, `LUMA-W-0000228`, a cross-league identifier collision. Ledger numbering
therefore contains a gap.

## Derived quantities

Possessions, following Oliver:

```python
poss = t[0] + t[2] + t[4] + 0.44 * t[6] + t[8] - t[9]
```

The 0.44 coefficient holds for the WNBA. Solving against 2026 league totals gives 0.4396; against
2010 totals, 0.4402. Derived pace is 81.7 possessions per team per 40 minutes in 2024 and 80.5 in
2010.

Offensive rating follows as `100 * points / poss`, using fields 3 and 4 for points.

## Coverage

| | |
|---|---|
| Games | 5,623 |
| Stints | 267,293 |
| Players | 975 |
| Lineups of exactly five | 534,582 of 534,586 |

Tallies for 2003–2025 derive from ESPN play-by-play. The 2026 season derives from the WNBA Stats
feed, which records 3.3% less clock time per game; per-second rates for that season are affected,
counting statistics are not.

Team-game aggregates were compared against an independently sourced box-score feed for the 2024
regular season, 528 team-games: points +0.02%, field-goal attempts +0.01%, free-throw attempts
+0.00%, offensive rebounds +0.00%.

## quality.json

Per-file reconstruction diagnostics, keyed as `rs_{season}` and `po_{season}`:

| Field | Description |
|---|---|
| `games` | Games in the season |
| `dated` | Games carrying a date |
| `stints` | Stint records |
| `lineup_exact5_pct` | Share of lineup slots holding exactly five players |
| `slots_over5`, `slots_under5` | Counts of slots holding more or fewer |
| `points_checksum_pct` | Share of records satisfying the scoring identity |
| `tov_checksum_pct` | Share satisfying the turnover identity |
| `tally_slots` | Tally vector length |

## Stability

Field names and positions in `luma_stints_v2` do not change meaning. New information arrives as
new slots appended to the tally or as new files, never by redefining an existing slot.

Identifiers are permanent. Completed seasons are frozen; the current season is refreshed during
the year. `manifest.json` carries a SHA-256 per file, so any change is detectable.
