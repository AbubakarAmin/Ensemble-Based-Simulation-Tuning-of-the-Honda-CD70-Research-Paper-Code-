# Release notes v14

## What v14 is
v14 is v13 plus a validation layer for fuel economy. It does NOT change calibration, the optimiser, the locked evaluation, the physics, any config value used by the existing results, the seeds or the draw counts. v12 and v13 stage results remain valid. What changes is how the model is compared with real figures.

## Why
The model predicted about 78 / 89 / 104 km/l at a steady 50 km/h, and the published figures are about 52 to 70 km/l. The comparison mixed definitions (steady cruise against mixed city and highway figures) and left out city riding. v14 compares like with like and states which gaps remain.

## Added
- `src/cd70/cycle.py`: city cycle (idle, cruise phases, stop-and-go acceleration), run-in scenario, steady-speed diagnostic, the pre-declared agreement rule and percentile helper.
- `config/validation.yaml`: all new assumptions in one place (time shares, idle throttle, acceleration constants, run-in factor, agreement tolerance). Fixed before any v14 result was seen.
- `data/raw/published_fuel.csv`: published, owner and user-supplied figures, each with its source, quality and whether it is used for the verdict.
- `data/raw/fuel_log_template.csv`: template for your own fill-up log.
- `scripts/fuel_validation.py` and task T-035: the comparison report `reports/fuel_validation.md` (long job, about 5 to 15 minutes).
- `tests/locked/test_fuel_cycle.py`: 8 tests (agreement rule, idle sensitivity, city plausibility, run-in direction, locked evaluation unchanged, gearing diagnostic, config consistency, acceleration term).
- T-063 now also needs T-035, so the results summary cannot be written before the fuel comparison exists.

## What the nominal engine gives (check, not a result)
- Steady 40 / 50 km/h: about 102 and 86 km/l. Engine speed at 50 km/h: about 5,400 rpm.
- City cycle (with acceleration term): about 73 km/l; acceleration adds about 0.2 L/100 km.
- Run-in scenario (friction x1.15): city about 71 km/l.
- Speed at 7,500 rpm in 4th gear: about 69 km/h (matches the sheet's note).

## Known gaps (kept on purpose)
- City figure still above owner reports (50 to 55 km/l). Likely drivers: part-load efficiency, cold start, enrichment and traffic. Not tuned away.
- Run-in penalty is about 3 percent in the model against 15 to 20 percent in owner reports. Not tuned away.
- Owner reports are not measurements. Only a measured fill-up log can settle the question.

## What to do next (you)
1. Fill `data/raw/fuel_log.csv` from your own fill-ups (at least 500 km, or a full tank per row), tagging each row with condition city, mixed or highway, and a row for a new bike if you have one.
2. Run T-035 (or `python scripts/fuel_validation.py` through the jobs wrapper).

## Migration
Same as v13: copy data/, runs/, reports/, figures/, paper_inputs/ and state/stage_done/ from the old folder if you want to keep results. T-035 runs after T-034 and before T-063.
