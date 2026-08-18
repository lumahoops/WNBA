# Contributing a metric

The harness runs any function that turns training data into one rating per
player. It does not care how the rating is computed, only that the same
function, given seasons it has seen, says something about a season it has not.

## The contract

```python
def metric(ctx) -> dict[str, float]:
    ...
```

`ctx` is a `TrainContext`. It exposes only the training seasons, so a
submission cannot read the holdout even by accident. Attempting to
gives a clear error rather than a silently inflated score.

| what | how |
|---|---|
| stints for one season | `ctx.stints(2024)` |
| every training stint | `ctx.iter_stints()` |
| player identities | `ctx.crosswalk()` |
| which seasons you may use | `ctx.seasons` |

Return `{luma_id: number}`. Rate as many or as few players as you like;
coverage is reported alongside the score.

## Layout

```
metrics/contrib/<handle>_<name>/
    metric.py     defines metric(ctx)
    meta.yml      what it measures, who wrote it, what it needs
```

`meta.yml`:

```yaml
name: true_shooting
author: your-handle
measures: scoring efficiency
description: one line, what the number means
requires:
  - numpy
license: CC-BY-4.0
```

`requires` is checked before your code runs. A missing dependency is reported
by name instead of failing somewhere inside your imports.

## Running it

```bash
# does it load and return the right shape
python harness/run.py --metric metrics/contrib/your_metric --validate

# run on two seasons and print the top ten, no scoring
python harness/run.py --metric metrics/contrib/your_metric --test

# score against a season it never saw
python harness/run.py --metric metrics/contrib/your_metric --holdout 2026

# everything, with a leaderboard
python harness/run.py --all --holdout 2026
```

## How scoring works

For every stint in the holdout season, the five on court are credited with the
possession-normalised point margin, and their opponents with its negative. A
player's outcome is the possession-weighted average, restricted to players with
at least 200 minutes. That is what happened while they played, computed without
reference to any metric.

Your ratings are compared to that by Spearman rank correlation, with Pearson
and coverage reported alongside.

## Metrics that measure one thing

A metric does not have to predict winning. `luma_true_shooting` scores shooting
efficiency and correlates weakly with margin, which is correct and visible:

```
metric                        spearman   pearson  coverage
luma_onoff_margin               0.3317    0.3854     77.6%
luma_true_shooting              0.1038    0.1678     76.9%
```

Declare what you measure in `measures:`. The intent is that boards eventually
group by it, so a passing metric is compared with other passing metrics rather
than with everything at once.

## Submitting

Fork, add your directory, open a pull request. CI runs `--validate` and
`--holdout` and posts the result on the pull request. Nothing is merged on the
strength of a score alone; the point is that the run is reproducible by anyone.
