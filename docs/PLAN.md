# Research plan in plain words

## The question

A Honda CD70 has published numbers (5.05 hp at 7500 rpm, 5.0 Nm at 5500 rpm, 12.7 bar cranking compression) but nobody has measured one in this project.
We build a physics model of the engine, make it match the published numbers in all the ways that are still compatible with the unknown details
(an ensemble of 100+ plausible engines), then ask: which hardware-feasible tuning changes make the engine produce more torque and use less fuel
**for all plausible engines, not just for one guess**. The answer is a robust tune plus an honest statement of how sure we are.

## Why this is publishable

Most tuning papers optimise one calibrated model and report its gain. Here the gain is reported as a distribution over calibrated engines
(paired against the baseline), every candidate must pass physics and hardware design rules, constraints (knock, peak pressure) are enforced across the ensemble,
and we also report **which unknown engine properties decide the size of the gain** (value of information: what a single measurement on a real engine would be worth).
That is a defensible contribution for a low-data engine, and it needs no new physics, only careful statistics.

## Is the specification physically possible? (checked in every variation)

Three layers:
1. `scripts/feasibility.py`: 16 quick checks of the printed numbers against engineering limits (displacement, piston speed, Mach index, BMEP, efficiency, gearing).
2. Calibration: the engine model must reproduce 5.05 hp, 5.0 Nm, 12.7 bar and obey BSFC, volumetric-efficiency, peak-pressure-angle and pressure limits. If almost no random engine can, the spec is at the edge (timing reading A is: about 0.1% accepted).
3. `src/cd70/rules.py`: every evaluated design passes 9 design rules (valve-piston clearance, head skim, valve acceleration, overlap, valve size, ignition limits, mixture) and 7 result plausibility limits (efficiency, VE, power, torque, convergence). A design or a result that breaks one is **infeasible** and cannot win.

## Why we build our own model (and reuse libraries)

Public codes were checked. LEAP 71's Noyron and PicoGK/ShapeKernel are geometry-and-manufacturing engines for 3D-printed hardware (Noyron itself is closed, PicoGK is a C#/voxel geometry kernel); they have no 4-stroke cycle model and need a graphics/.NET stack.
NovaTurbo is a micro turbojet (Brayton cycle) design generator, not a piston engine. OpenFOAM is a 3-D CFD solver: far too slow for thousands of cycles on 8 GB and needs a real mesh, i.e. a real geometry we do not have.
What we take from them is the **idea**: encode engineering knowledge as explicit, testable rules that gate every design (our `rules.py`), and keep the whole chain automatic and reproducible. See docs/DESIGN_NOTES.md.
We reuse well-tested libraries: Cantera (gas properties), NumPy/SciPy, Numba (speed), SALib (Morris, Sobol), pymoo (NSGA-II, hypervolume), Optuna (TPE), scikit-learn.

## Stages (the task list in `tasks/` implements these)

0. Setup (T-001..T-004). 1. Verify spec and model (T-010, T-011). 2. Rehearsal at tiny scale (T-020..T-022).
3. Calibration, both valve-timing readings, baseline curves, report, holdout validation (T-030..T-034).
4. Sensitivity (T-040..T-042). 5. Optimisation: three algorithms, three hardware classes, then the ensemble-robust optimiser (T-050..T-054).
6. Paired robustness, scenario grid, value of information (T-060, T-061). 7. Figures, paper inputs, results summary (T-062, T-063).
8. Audit, red team, handoff (T-070..T-080).

## Top speed and cranking pressure (updated 11 Oct 2026)

Top speed: the real-world top speed of a stock CD70 is 80-90 km/h. With the sheet gearing that needs about 8700-9800 rpm in 4th, so the model is run up to 9500 rpm and calibrated so that the true top speed lies between 80 and 90 km/h. Air drag, rolling resistance, mass and drivetrain efficiency became uncertain inputs (38 uncertain inputs in total). The ensemble then says what the data imply, e.g. a low drag area.
Cranking pressure: instead of forcing the unverified 1000 rpm, the test speed is an uncertain input (300-1000 rpm) and the blow-by area is calibrated with it. Both are reported after calibration.
Variation validity: every accepted calibrated engine is re-checked with the baseline design rules and plausibility limits (invalid engines are dropped and counted), and every design evaluated later passes the same rules.

## Valve timing ambiguity

The workshop manual prints 0/20/20/0 degrees. Such timing is usually quoted at a lift of ~1 mm, not at zero lift. Reading A uses the numbers as printed (200 deg duration, 0 deg overlap).
Reading B adds 20 deg on every flank (240 deg, 40 deg overlap). Everything is run for both (B is the main case, A the stress test). A conclusion that flips sign between A and B is flagged and cannot be a CLAIM.

## Hardware classes (what is allowed to change)

A = jet and ignition only (cheap, no engine opening). B = A plus compression ratio (head skim or gasket). C = everything including cam timing/duration and intake valve size.

## Objectives and constraints

f1 = mean full-throttle torque 2000-7500 rpm (12 points). f2 = mean fuel use (L/100 km) at steady 30, 40, 50 km/h in 4th gear. o1 = -f1/f1_base, o2 = f2/f2_base (both minimised, ratios to the baseline of the same engine).
Constraints: knock index <= 0.95 (the baseline engine itself sits at 0.6-0.95 of the limit: calibration parameter knock_margin_base), peak cylinder pressure <= 60 bar, all rules and plausibility checks.
