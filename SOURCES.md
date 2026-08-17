# Sources

## Upstream sources

The underlying records come from two feeds.

| Source | Provides | Coverage |
|---|---|---|
| [WNBA Stats API](https://stats.wnba.com) | `playbyplayv3`, `scoreboardv2` | Play-by-play and schedule, current season |
| [ESPN](https://site.api.espn.com/apis/site/v2/sports/basketball/wnba) | scoreboard, summary, `sports.core.api` plays | Play-by-play and box scores, 2003–2025; substitution events carry both participants |

## Retrieval tooling

Bulk historical retrieval from those feeds used the mirrors maintained by the
sportsdataverse project. Those repositories are ESPN and WNBA Stats mirrors, not
independent sources; the same records are reachable from the endpoints above.

| Project | Used for |
|---|---|
| [wehoop-wnba-data](https://github.com/sportsdataverse/wehoop-wnba-data) | `player_box` parquet, mirrored play-by-play |
| [sportsdataverse-data](https://github.com/sportsdataverse/sportsdataverse-data) | `wnba_stats_pbp` releases |

The `wehoop` package is by Saiem Gilani and Geoffery Hutchinson. Their requested
citation:

```bibtex
@misc{hutchinson_gilani_2021_wehoop,
  title     = {wehoop: Access Women's Basketball Play by Play Data},
  author    = {Gilani, Saiem and Hutchinson, Geoffery},
  url       = {http://doi.org/10.32614/CRAN.package.wehoop},
  DOI       = {10.32614/cran.package.wehoop},
  journal   = {CRAN: Contributed Packages},
  publisher = {The R Foundation},
  year      = {2021},
  month     = nov
}
```

## Derivation

Substitution events are replayed within each period to recover the five players on court for each
team. Period-opening lineups are seeded from box-score starter flags where present. Shot,
rebound, turnover and assist events are attributed to the stint containing them. Player
identifiers from both feeds are reconciled to a single identifier per person.

## Related work

| Project | Scope |
|---|---|
| [dblackrun/pbpstats](https://github.com/dblackrun/pbpstats) | Possession parser for NBA, WNBA and G-League play-by-play. |
| [sportsdataverse/hoopR](https://github.com/sportsdataverse/hoopR), [wehoop](https://github.com/sportsdataverse/wehoop) | R packages for NBA and WNBA data access. |
| [swar/nba_api](https://github.com/swar/nba_api) | Python client for the NBA Stats API. |
| [shufinskiy/nba_data](https://github.com/shufinskiy/nba_data) | Bulk NBA play-by-play, 1996–2025. |
| [SCORE Sports Data Repository](https://data.scorenetwork.org) | NBA stint dataset, 2022–23 season. |
| [Dianjeol/nba-stint-data](https://github.com/Dianjeol/nba-stint-data) | NBA stint pipeline, 2024 season. |
| [Historical RAPM Project](https://squared2020.com) (Justin Jacobs) | Possession-level database reconstructed from video, 1969–1996. |

Stint datasets for the WNBA covering multiple seasons were not located during a survey conducted
2026-08-16. The datasets above cover the NBA, single seasons, or the pre-play-by-play era.

## Legal

Factual records of sporting events are not subject to copyright in the United States
(*Feist Publications v. Rural Telephone Service Co.*, 499 U.S. 340 (1991);
*NBA v. Motorola*, 105 F.3d 841 (2d Cir. 1997)).

This dataset is a derived work. It contains lineup segments and ratings computed from the source
records; no feed response, mirror archive, or third-party file is redistributed. No logos or
trademarks are included. Not affiliated with, endorsed by, or sponsored by the WNBA, ESPN, or any team.

## Licence and citation

Data are released under CC BY 4.0; code under MIT. See [LICENSE](LICENSE).
Cite using [CITATION.cff](CITATION.cff).
