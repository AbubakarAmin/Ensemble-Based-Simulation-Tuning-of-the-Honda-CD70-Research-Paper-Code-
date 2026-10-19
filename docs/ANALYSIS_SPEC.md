# Analysis specification (every stage in `src/cd70/experiments.py`)

| Stage | Command | What it does | Output (data/processed) |
|---|---|---|---|
| calibrate | `run_stage.py calibrate --timing T` | Scrambled Sobol draws of the 38 uncertain inputs (32768 per round, up to 8 rounds). Each draw runs 7 engine points (5500, 6500, 7500, 8500, 9500 rpm WOT, plus motoring at the drawn crank_rpm). Accept if power 5.05 hp +-5%, torque 5.0 Nm +-10%, cranking 12.7 bar +-10%, true top speed 80-90 km/h (4th gear, power interpolated up to 9500 rpm), BSFC 300-450, VE 0.60-0.98, peak-pressure angle 10-22 deg ATDC, pmax < 60 bar, converged. | cal_T/ (all draws), accepted_T.parquet (after the validity pass: baseline must satisfy all design rules, plausibility limits, knock and pressure limits; dropped engines counted in cal_summary), accepted_raw_T.parquet, twin_T.json (accepted engine closest to the posterior median), cal_summary_T.json |
| curves | `curves` | WOT curves (12 rpm points) of the baseline for up to 300 accepted engines | baseline_curves_T.parquet |
| ofat | `ofat` | Each tuning variable to its low and high bound, others at baseline, on the twin | ofat_T/ |
| morris | `morris` | SALib Morris, 30 trajectories, 4 levels, 8 variables | morris_result_T.parquet |
| sobol | `sobol` | SALib Saltelli sample N=256 (no second order), first and total indices with confidence | sobol_result_T.parquet |
| optimise | `optimise --cls --method --seed` | NSGA-II (pymoo, pop 40), TPE (Optuna, constraints), random search; 1600 evaluations each on the twin | opt/T_cls_method_seed.parquet |
| optimise_robust | `optimise_robust --cls --seed` | NSGA-II on 10 accepted engines at once; objectives are mean paired ratios; constraints: 80th-percentile knock <= 0.95, worst pmax <= 60 bar, at most 10% of engines may break a rule | optrob/ |
| pick | `pick --cls` | From the pooled robust front: econ (min fuel with torque >= baseline), power (max torque with fuel <= baseline), knee (closest to utopia after scaling) | picked_T_cls.json |
| robust | `robust --cls --which` | The design and the baseline on up to 300 accepted engines (paired). Gains in percent, feasibility on each engine | paired_T_cls_which.parquet |
| grid | `grid --cls --which` | 12 scenarios (RON 87/92 x 15/30/45 C x 0/1500 m) x 60 engines x {baseline, design} | grid_T_cls_which/ |
| voi | `voi --cls --which` | Random forest of the paired gain on the uncertain inputs, permutation importance + Spearman | voi_T_cls_which.parquet |

Objectives: f1 = mean WOT torque 2000..7500 step 500; f2 = mean of L/100 km at 30, 40, 50 km/h in 4th. o1 = -f1/f1_base, o2 = f2/f2_base.
Hypervolume reference point (-0.90, 1.10). Feasible = status ok, all design rules, all plausibility checks, knock index <= 0.95, pmax <= 60 bar, finite objectives.

Interpretation patterns (for the paper writer):
- Acceptance rate low -> published numbers sit at the model's edge. Posterior narrower than prior for a parameter -> the published numbers constrain it.
- Sobol ST >> S1 -> interactions. Morris sigma large relative to mu* -> non-linear / interacting.
- Random search ~ NSGA-II hypervolume -> easy problem; do not claim algorithmic advantage.
- Optimiser at a bound -> bound-limited optimum; report as such.
- Design feasible on < 90% of engines -> not robust. Gain CI crossing 0 -> no claim. Sign flip between timing A and B -> ambiguity-dependent.
- VoI top variables -> what to measure first on a real engine.


## v14 additions (validation only; no calibration or optimiser change)

| step | command | output |
|---|---|---|
| fuel validation | `python scripts/fuel_validation.py` (60 accepted engines, timing B) | reports/fuel_validation.md |

Definitions used in v14, so that the model is compared with the same kind of figure:
- Steady cruise: 4th gear at 40 or 50 km/h (the locked evaluation, unchanged).
- City cycle (src/cd70/cycle.py): time-weighted fuel over idle (1,500 rpm, 5 percent throttle) and cruise phases at 20, 30, 40 and 50 km/h, plus a stop-and-go acceleration term (2 restarts per km to 30 km/h, 20 percent fuel-to-kinetic-energy efficiency). Time shares and these constants are in config/validation.yaml and are ASSUMED.
- Run-in scenario: friction scale multiplied by the run-in factor in config/validation.yaml (ASSUMED 1.15) for a new bike.
- Agreement rule (fixed before results): AGREE if the model median lies in [low x 0.8, high x 1.2] of the published or owner range.
- Figures tagged `use_for_verdict = no` (manufacturer claim, or source unknown) are reported but not used for the verdict.
- Gearing check (diagnostic): engine speed at 30, 40 and 50 km/h in 4th gear and the speed at 7,500 and 9,500 rpm.
- Your own fuel log (data/raw/fuel_log.csv, optional): overall and per-condition km/l with a 95 percent bootstrap interval (fixed seed 20261015).

## v15: optimiser fuel objective

- The fuel objective used by the optimiser (NSGA-II, TPE and random search), the robust optimiser, the sensitivity analysis (Morris, Sobol, one-at-a-time), feasibility, the design picks, the figures and the paper is the CITY-CYCLE fuel use `f2_city_l100km` (L/100 km). It is set in `config/optimiser.yaml` and read through `src/cd70/objective.py` (`FUEL_KEY`).
- Steady cruise at 30/40/50 km/h (`f2_cruise_l100km`) is still computed and stored as a diagnostic, but is no longer the objective.
- The city cycle is defined in `src/cd70/cycle.py`, with time shares and constants in `config/validation.yaml` (ASSUMED values, listed in LIMITATIONS).
- Calibration does NOT use fuel. The calibration targets are unchanged from v12.
- Consequence: the optimiser now minimises the model's own city estimate, so the city comparison in T-035 is no longer independent of the design choice (it remains independent of calibration).
