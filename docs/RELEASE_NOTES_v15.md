# Release notes v15

## What changed
- The optimiser's fuel objective is now the city-cycle fuel use (f2_city_l100km), set in config/optimiser.yaml. Steady cruise remains as a diagnostic.
- One definition, src/cd70/objective.py (FUEL_KEY), is used by the optimiser, robust optimiser, sensitivity analysis (Morris, Sobol, one-at-a-time), feasibility check, design picks, figures, paper text and audit.
- evaluate_design now also returns the city figure and its two parts (cruise phases, acceleration term). The existing steady-cruise columns are unchanged.
- Paper and figure wording says "city fuel" where it said "cruise fuel".
- Calibration, physics, bounds, seeds and draw counts are unchanged.
- Tests: 48 locked tests pass (3 new in tests/locked/test_objective.py, the feasibility test now uses FUEL_KEY).

## What was verified here
- Lint clean; 48 of 48 locked tests pass; health gate (see report).
- A smoke-scale NSGA-II run (60 evaluations, nominal engine, synthetic twin file for testing only) completed; objective values are about 1.36 L/100 km (about 73 km/l), 85 percent of designs feasible.
- The smoke robust optimiser and design pick were run in the background (see report for result).

## What was NOT verified here
- The full study (days of compute), the full figures and the paper build. Those run from scratch on your computer.
- Whether the new objective improves the designs against the real figures. That is what the full run and T-035 are for.

## Runtime
Each evaluation adds the city cycle (about 5 more engine points plus 3 extra cruise solves). Expect the full study to take longer than v14 (roughly 20 to 40 percent more per evaluation). The 200-wait budget per long job still applies.

## Starting from scratch
Unzip v15, open the folder in opencode, type /work. There are no old results to migrate.
