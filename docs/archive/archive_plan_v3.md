# CD70 Engine Optimization: Phase 1 Research Plan (v3.0)

Version 3.0, 9 October 2026. Replaces v2.0 and v1.0. Companion: `CD70_Final_Spec_Sheet_v10.md`. Every model input is taken from section 8 of that sheet. Nothing in this plan overrides it. If a value changes, change the sheet first, then this plan.

---

## 0. What changed from v2.0

| Item | v2.0 | v3.0 | Basis (spec sheet v10) |
|---|---|---|---|
| Compression ratio | 9.3 base, 8.8 second scenario | **9.3 only.** 8.8 kept as a single check run, not a design scenario. | Official Atlas product page and Atlas spec PDF both state 9.3:1. 8.8 traced to the C70 sibling and to secondary listings. |
| Calibration point 3 (cranking compression) | Used to decide between CR 9.3 and 8.8 | **Check only.** Used to test valve timing and loss model. | CR is settled. Cranking value comes from the older workshop manual (WSM). |
| Carburettor code | Not in plan | **PZ18** (MEDIUM−, CD70 1997–2004 fitment) | Oro2u PZ18 listing. Current Euro II code still open. |
| Venturi | Not in plan | **18 mm base**, 16.5 mm sensitivity | Oro2u listing gives both sizes |
| Main jet | #78 (UNRESOLVED) | **#78 (MEDIUM)**, #72 check | WSM printed value and Keihin list |
| Slow / idle jet | #38 (PROXY) | **#38 base (PROXY/OPEN)**, #35 sensitivity | CD70 parts list vs. WSM printed "35" |
| Valve timing | WSM 0/20/20/0 | **WSM, provisional.** Sensitivity ±2°. | No official CD70 value found |
| Ignition | 20° BTDC WSM | **20° BTDC WSM, OPEN.** Range 15–25°. | No independent CD70 source |
| Gear ratios | WSM | **WSM, provisional** | Official gives final drive only |
| Chain slack | Not in plan | Not a model input | Official 20–30 mm; WSM 10–20 mm rejected |
| Stage 1 gate | All WSM values checked at full size before Stage 2 | **Model build may start now.** WSM values are provisional and tested by sensitivity. A current manual check is required before submission (Stage 8 gate). | Official sources cover the core geometry. Blocking the build is no longer needed. |
| Sources | Partial | **Full register** (section 16) with links | Spec sheet v10, section 10 |

---

## 1. Research question

Can a calibrated 1D thermodynamic model of a 72 cc air-cooled single-cylinder SI engine (Honda CD70, Atlas Honda Pakistan) find a Pareto front of tuning designs that trades brake torque against brake-specific fuel consumption (BSFC), subject to a knock limit for Pakistani petrol?

**Scope:** tuning and operating variables only. Bore, stroke, combustion chamber shape and venturi size are fixed in Phase 1.

---

## 2. Hypothesis

Tuning changes (compression ratio, ignition advance, main jetting, valve timing) can improve BSFC or torque by a modest, measurable amount without violating the knock limit. Gains will be small because the Otto cycle at this size is already near its practical limits. Several inputs are provisional, so the result is a conditional prediction, not a measured gain.

---

## 3. Inputs and their status

All values are in spec sheet v10, section 8.

### 3.1 Official (fixed, use as given)
- Bore 47.0 mm, stroke 41.4 mm, displacement 71.84 cm³ (rated 72)
- Compression ratio 9.3:1; clearance volume 8.66 cm³ (derived)
- Final drive 14/41 = 2.93
- Ignition type AC-CDI; spark plug C7HSA
- Idle 1,500 ± 100 rpm
- Dry weight 82 kg, tyres 2.25-17 / 2.50-17 (for later vehicle-level phases, not used in Phase 1)

### 3.2 MEDIUM (use, test by sensitivity)
- Connecting rod centre-to-centre 91 mm (90–92)
- Calibration targets: 5.05 hp at 7,500 rpm; 5.0 Nm at 5,500 rpm
- Main jet #78 (test #72)
- Rated speed 7,500 rpm
- Carburettor code PZ18 (MEDIUM−)

### 3.3 WSM (older workshop manual, provisional)
- Valve timing IO 0 BTDC, IC 20 ABDC, EO 20 BBDC, EC 0 ATDC
- Valve clearance cold 0.08–0.10 mm (use 0.09)
- Valve stem OD 4.98 / 4.96 mm; guide ID 5.006 mm; seat 1.0 mm
- Ignition static 20° BTDC at 1,500 rpm; 35° at 4,000 rpm
- Float level 11.7 mm; air screw 2.125 turns
- Gears 3.272 / 1.937 / 1.350 / 1.043; primary 3.722
- Cranking compression 12.7 bar at 1,000 rpm
- Small-end ID 13.02 mm; piston pin bore 13.005 mm

### 3.4 PROXY (sibling-based, replace or sensitivity-test)
- Intake head diameter 25 mm; exhaust 21.9 mm (K&L family listing)
- Slow / idle jet #38 (CD70 parts list; test #35)

### 3.5 OPEN (sensitivity only)
- Venturi 18 mm (test 16.5 mm)
- Ignition timing above 4,000 rpm (held flat at 35°)
- Ignition below 1,500 rpm (held at 20°)

### 3.6 ASSUMED (no source; sensitivity-test)
- Valve lift max 6.5 mm (6.0–7.0)
- Peak cylinder pressure limit 60–70 bar

### 3.7 LOW (use as scenarios)
- Fuel: RON 87 (design worst case) and RON 92 (target). Current 2026 national grade not confirmed.

### 3.8 Not used in Phase 1
- Chain slack (official 20–30 mm). Not a thermodynamic input.
- Tyre pressures, wheelbase, ground clearance, fuel tank (vehicle-level; Phase 3).

---

## 4. Pipeline

```
[1] Config  ->  [2] Model build  ->  [3] Calibration  ->  [4] Validation
                                                                |
[8] Write-up  <-  [7] Robustness  <-  [6] Optimization  <-  [5] Sampling & sensitivity
```

Each stage has an output and a go/no-go check (section 9). Stage 8 has a submission gate that requires a current manual check of the WSM inputs.

---

## 5. Software stack

| Layer | Tool | Purpose | Notes |
|---|---|---|---|
| Language | Python 3.11+ | Model and pipeline | Fresh virtual environment |
| Numerics | NumPy, SciPy | Thermodynamics, ODEs, LHS (`scipy.stats.qmc`) | [SciPy](https://scipy.org/) |
| Data | pandas | Config, logs, results | [pandas](https://pandas.pydata.org/) |
| Sensitivity | SALib | Sobol indices | [SALib](https://salib.readthedocs.io/) |
| Multi-objective optimiser | pymoo (NSGA-II) | Main search | [pymoo](https://pymoo.org/) |
| Bayesian optimiser | Optuna | Independent comparison | Akiba et al., 2019, [arXiv:1907.10902](https://arxiv.org/pdf/1907.10902) (MIT licence) |
| Surrogate (Phase 2) | scikit-learn (Gaussian process) | Fast approximation | [scikit-learn](https://scikit-learn.org/) |
| Plotting | matplotlib | Pareto fronts, sensitivity charts | [matplotlib](https://matplotlib.org/) |
| Reproducibility | Git, `requirements.txt`, fixed seeds | Repeatable runs | Record `pip freeze` |
| Cross-check simulator | OpenWAM (GPL-3) | 1D gas dynamics, Linux build | [OpenWAM docs](https://openwam.webs.upv.es/docs/) |
| Commercial reference (optional) | GT-Suite or Ricardo WAVE | Structure cross-check | Used in validation papers in section 12 |

Install: `pip install numpy scipy pandas SALib pymoo optuna scikit-learn matplotlib`. Pin exact versions with `pip freeze` after installation.

---

## 6. Model

### 6.1 Type

Single-zone 0D/1D cycle model with crank-angle resolution (0.5° or 1°). Each run takes seconds on a laptop.

### 6.2 Submodels and their inputs

| Submodel | Method | Inputs (spec sheet v10 section 8) | Status |
|---|---|---|---|
| Cylinder volume | Slider-crank | bore 47.0, stroke 41.4, rod 91 mm | Official / MEDIUM |
| Clearance volume | Derived | CR 9.3 → 8.66 cm³ | Official |
| Valve lift | Cosine-type profile from IO, IC, EO, EC and max lift | Timing WSM; lift 6.5 mm | WSM / ASSUMED |
| Valve flow | Simplified flow through valves | Head 25 / 21.9 mm; stem 4.98 / 4.96; guide 5.006; seat 1.0 mm | PROXY / WSM |
| Valve clearance effect | Cold clearance sets the thermal reference for timing; no hot correction in Phase 1 | 0.09 mm (0.08–0.10) | WSM |
| Gas exchange | Volumetric efficiency vs. timing and rpm | Timing above | WSM |
| Carburettor | Main and slow jet flow; float level; venturi choke | Main #78; slow #38; float 11.7 mm; venturi 18 mm; air screw 2.125 turns | MEDIUM / PROXY / WSM / OPEN |
| Ignition | Static 20° BTDC at 1,500; advance linear to 35° at 4,000; flat above | Ignition values | WSM / OPEN |
| Transmission | Gear ratios for the speed sweep | 3.722 primary; 3.272 / 1.937 / 1.350 / 1.043 | WSM |
| Heat release | Wiebe function; burn duration 2–3 ms, calibrated | Calibrated | Heywood; [Dresler and Richtář](https://pernerscontacts.upce.cz/index.php/perner/article/download/900/734/1569) |
| Heat transfer | Woschni | Standard | Heywood |
| Friction | Chen-Flynn, coefficients calibrated | Calibrated | Standard |
| Knock | Livengood-Wu integral vs. limit | Fuel RON scenarios | LOW (grade) |
| Cranking check | Motoring pressure at 1,000 rpm, throttle open | 12.7 bar | WSM (check only) |

### 6.3 Outputs

- Brake torque and brake power vs. rpm
- BSFC vs. rpm and load
- Knock integral (margin to limit) at each operating point
- Peak cylinder pressure
- Motoring pressure at 1,000 rpm (check)

---

## 7. Design variables, bounds and fixed inputs

### 7.1 Design variables (optimised)

| Variable | Baseline | Range | Source of baseline |
|---|---|---|---|
| Compression ratio | 9.3 | 8.5–10.5 | Official. Above 9.3 needs a new piston; knock check. |
| Ignition advance (static, F mark at 1,500 rpm) | 20° BTDC | 15–30° BTDC | WSM, OPEN |
| Main jet | #78 | #70–#80 | MEDIUM |
| Intake cam timing shift | 0° (WSM timing) | ±15° | Sim-only; needs new cam |
| Exhaust cam timing shift | 0° (WSM timing) | ±15° | Sim-only; needs new cam |
| Intake head diameter | 25 mm | ±10% | PROXY |

### 7.2 Fixed inputs (not optimised, varied only in sensitivity)

| Input | Value | Sensitivity | Status |
|---|---|---|---|
| Bore × stroke | 47.0 × 41.4 mm | ±0.01 mm | Official |
| Connecting rod | 91 mm | 90–92 mm | MEDIUM |
| Venturi | 18 mm | 16.5 mm | OPEN |
| Slow / idle jet | #38 | #35 | PROXY / OPEN |
| Float level | 11.7 mm | ±0.5 mm | WSM |
| Valve lift | 6.5 mm | 6.0–7.0 mm | ASSUMED |
| Valve clearance | 0.09 mm | 0.08–0.10 mm | WSM |
| Exhaust head diameter | 21.9 mm | ±10% | PROXY |
| Gear ratios | 3.272 / 1.937 / 1.350 / 1.043 | ±0.02 | WSM |
| Primary | 3.722 | ±0.02 | WSM |
| Ignition above 4,000 rpm | 35° flat | ±3° | ASSUMED |

Bore and stroke are fixed. Changing them is a Phase 2 question (block and piston replacement).

---

## 8. Objectives, constraints and scenarios

**Objectives:**
- Maximise brake torque, averaged over 2,000–7,500 rpm.
- Minimise BSFC at 3,500 rpm (cruise) and at 7,500 rpm (rated).

**Constraints:**
- Knock integral below the limit for each fuel scenario.
- Peak cylinder pressure below 60–70 bar (ASSUMED; verify in Stage 3).
- Speed at or below 7,500 rpm.

**Scenarios:**
- Fuel: RON 87 (design worst case) and RON 92 (target). Report both.
- Compression ratio: 9.3 only in the optimisation. One check run at 8.8 to show how much the result depends on this official value.

---

## 9. Procedure

### Stage 0: Environment (1 day)
1. Create a Python 3.11 virtual environment and install the packages in section 5.
2. Create a Git repository. Add `requirements.txt` and a seed file.

### Stage 1: Config (1 week)
1. Build one config file from spec sheet v10, section 8. Each entry keeps its tag (OFFICIAL, MEDIUM, WSM, PROXY, ASSUMED, OPEN, LOW).
2. Write a check script that fails if any value in the config differs from the sheet.
3. **Go/no-go:** config matches the sheet exactly; every provisional input (WSM, PROXY, OPEN, ASSUMED) is listed with its sensitivity range.

*Note:* Stage 1 no longer waits for a scan of the workshop manual. Model build proceeds on the provisional values, and their effect is tested in Stage 5. The submission gate in Stage 8 still applies.

### Stage 2: Model build (2–3 weeks)
1. Implement cylinder volume, valve lift, valve flow and gas exchange.
2. Implement Wiebe heat release, Woschni heat transfer, friction, the carburettor model (main jet, slow jet, venturi, float) and the knock integral.
3. Implement the ignition advance map: 20° at 1,500 rpm, linear to 35° at 4,000 rpm, flat above.
4. Unit tests:
   - Displacement = 71.84 cm³.
   - Clearance volume = 8.66 cm³ at CR 9.3.
   - Cylinder volume at BDC = displacement + clearance.
   - Intake and exhaust durations = 200° each; overlap = 0°.
   - Piston mean speed at 7,500 rpm = 10.35 m/s.
   - Overall ratio, 1st gear = 35.66.
   - Overall ratio, top gear = 11.37.
5. **Go/no-go:** all unit tests pass, and one run completes in under 10 seconds.

### Stage 3: Calibration (1–2 weeks)
Two calibration targets and one check:
1. **Power (target):** 5.05 hp at 7,500 rpm, full throttle (±5%). MEDIUM.
2. **Torque (target):** 5.0 Nm at 5,500 rpm, full throttle (±10%). MEDIUM.
3. **Cranking compression (check):** 12.7 bar at 1,000 rpm, throttle open (±10%). WSM.

Adjust burn duration, friction coefficients and volumetric efficiency factor within physically reasonable limits until targets 1 and 2 match. Record every adjusted parameter.

Then run check 3. If it fails, diagnose in this order: valve timing (WSM), valve clearance, loss model, compression ratio. Do not change the compression ratio to fit the check; the compression ratio is official.

**Go/no-go:** targets 1 and 2 within tolerance. Check 3 within ±10%, or the gap is documented in the write-up with its likely cause.

### Stage 4: Validation (2 weeks)
1. Apply the same model structure to a published small single-cylinder case with measured data. Sources: Morrissey and Shedd (SAE 2008-32-0043; error under 15%, 20% at WOT) and Peñaranda et al. (Honda GX-35).
2. Report published-case error separately from calibration error.
3. **Go/no-go:** published-case error under 15%. If higher, revise the model before optimising.

### Stage 5: Sampling and sensitivity (1 week)
1. Latin Hypercube sample of 300 points over the six design variables in section 7.1. Fixed seed.
2. Run every point and log the outputs.
3. Sobol indices with SALib. Drop any variable whose total-order index is below 0.02.
4. One-at-a-time sensitivity on every provisional and assumed input in section 7.2:
   - Valve timing ±2° (WSM)
   - Valve lift 6.0–7.0 mm (ASSUMED)
   - Valve clearance 0.08–0.10 mm (WSM)
   - Main jet #72 vs #78 (MEDIUM)
   - Slow jet #35 vs #38 (PROXY / OPEN)
   - Venturi 16.5 vs 18 mm (OPEN)
   - Float ±0.5 mm (WSM)
   - Ignition above 4,000 rpm ±3° (ASSUMED)
   - Ignition static 15 vs 25° (OPEN)
   - Rod 90 vs 92 mm (MEDIUM)
   - Head diameters ±10% (PROXY)
   - Gear ratios ±0.02 (WSM)
   - Compression ratio 8.8 (one check run)
5. Report which provisional inputs move the front by more than the calibration tolerance. These go into the limitations section.
6. **Go/no-go:** at least three design variables remain with meaningful effect.

### Stage 6: Optimisation (2–3 weeks)
1. **NSGA-II** (pymoo): population 100, 50 generations (about 5,000 evaluations). Constraints by constrained dominance. Deb et al., 2002, IEEE TEC 6(2), pp. 182–197.
2. **Optuna** (NSGA-II sampler or TPE) on the same objectives. Akiba et al., 2019.
3. Compare the two fronts by hypervolume. Report both if they agree; explain differences if not.
4. Repeat each search with 5 seeds to test stability.
5. Run both fuel scenarios (RON 87 and RON 92).

### Stage 7: Robustness (1 week)
1. Take the top 10 designs from each front.
2. Perturb uncertain inputs: friction ±5%, burn duration ±5%, volumetric efficiency ±5%, valve lift 6.0–7.0 mm, rod length 90–92 mm, valve clearance 0.08–0.10 mm, main jet #72 / #78, slow jet #35 / #38, venturi 16.5 / 18 mm.
3. Keep only designs that stay within constraints under all perturbations. Report these.

### Stage 8: Write-up and submission gate (2–3 weeks)
1. Method: model equations, calibration (two targets and one check), validation, optimisation settings.
2. Results: Pareto fronts for RON 87 and RON 92, sensitivity, robust designs, the 8.8 check run.
3. Limitations: provisional WSM inputs, PROXY head diameters, assumed valve lift, no measured CD70 data, simulation only.
4. Reproducibility: code repository, seeds, spec sheet v10 with all sources.

**Submission gate (must be met before the paper is submitted):**
- A current Atlas Honda CD70 workshop or service manual, or a printed copy, has been checked against every WSM value in the sheet. Any value that changes is re-run through Stages 3–7.
- The carburettor tag and jets have been read on a running CD70. Venturi is confirmed.
- Ignition timing has been checked on a running CD70 at 1,500 and 4,000 rpm, or the ignition results are labelled provisional.
- The MMT limit has a source link, or it is removed from the text.

---

## 10. Deliverables

| Deliverable | Format | Done when |
|---|---|---|
| Spec sheet | Markdown (v10, attached) | Every value tagged and linked |
| Config file | Python / YAML, generated from spec sheet section 8 | Check script passes |
| Model code | Python repository | Unit tests pass |
| Calibration report | Markdown | Two targets within tolerance; check 3 reported |
| Validation report | Markdown | Published-case error under 15% |
| Sensitivity results | CSV and plots | Influential provisional inputs listed |
| Pareto fronts | CSV and plots, both fuels | Both optimisers run; constraints applied |
| Robustness report | Markdown | Top designs tested under perturbation |
| Draft paper | Word or LaTeX | Method, results, limitations complete; submission gate met |

---

## 11. Timeline (about 3.5 months)

| Weeks | Stage |
|---|---|
| 1 | Stage 0 (environment) and Stage 1 (config and check script) |
| 2–4 | Stage 2 (model build) |
| 5–6 | Stage 3 (calibration) |
| 7–8 | Stage 4 (validation) |
| 9 | Stage 5 (sampling and sensitivity) |
| 10–12 | Stage 6 (optimisation) |
| 13 | Stage 7 (robustness) |
| 14–16 | Stage 8 (write-up; submission gate runs in parallel from week 1) |

The submission gate runs in parallel from the start. If the current manual or the carburettor read cannot be obtained, the paper is submitted with the affected results labelled provisional.

---

## 12. Validation references

| Reference | What it gives | Link |
|---|---|---|
| Morrissey and Shedd, SAE 2008-32-0043 | GT-Power carburettor model, single-cylinder air-cooled. Error under 15%; 20% at WOT. | https://doi.org/10.4271/2008-32-0043 |
| Avelar et al., SAE 2019-36-0170 | GT-Power calibration for SI engines. Typical error about 5%, maximum 7%. | https://doi.org/10.4271/2019-36-0170 |
| Peñaranda et al., ITA | 1D calibration for Honda GX-35, Wiebe combustion | https://amcaonline.org.ar/ojs/index.php/mc/article/download/3359/3278 |
| Dresler and Richtář, MZ125 | Single-cylinder Wiebe model in WAVE and GT-Power | https://pernerscontacts.upce.cz/index.php/perner/article/download/900/734/1569 |
| Deb et al., NSGA-II | Multi-objective genetic algorithm (Stage 6) | https://repository.ias.ac.in/9403 |
| Akiba et al., Optuna | Hyperparameter optimiser (Stage 6) | https://arxiv.org/pdf/1907.10902 |
| OpenWAM | Open-source 1D gas dynamics, GPL-3 | https://openwam.webs.upv.es/docs/ |

Heywood, *Internal Combustion Engine Fundamentals*, is the textbook for the submodels in section 6. Not checked online in this session.

---

## 13. Risks and mitigations

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| WSM values are from an older edition (it disagrees with the official CR and chain slack) | Valve, ignition and gear inputs may be wrong | High | Sensitivity runs over WSM ranges (Stage 5). Submission gate: check against a current manual. |
| Ignition timing from WSM only | Peak pressure, knock, power curve | Medium | Sensitivity 15–25°. Timing-light check on a running CD70. |
| Carburettor venturi unresolved (18 vs 16.5 mm) | Air flow, calibration | Medium | Base 18 mm; sensitivity 16.5 mm; read the tag. |
| Carburettor code PZ18 from a retailer | Wrong carb model | Medium | Read the tag. Use only as a label until confirmed. |
| Slow / idle jet unresolved (#38 vs #35) | Idle and low-load mixture | Low for calibration (wide-open-throttle points) | Sensitivity #35 / #38 |
| Main jet #78 from WSM plus retailer | Wide-open-throttle mixture | Medium | Sensitivity #72 / #78; calibration point 1 and 2 tune the model to measured power and torque |
| Valve lift assumed | Breathing, volumetric efficiency | Medium | Sensitivity 6.0–7.0 mm. Measure a cam. |
| Head diameters are a proxy | Breathing limit | Medium | Sensitivity ±10%. Measure a head. |
| Ignition above 4,000 rpm assumed | Peak pressure, knock at high rpm | Medium | Sensitivity ±3°. Timing light at 7,500 rpm. |
| Connecting rod from an aftermarket listing | Piston kinematics | Low | Sensitivity 90–92 mm. Measure a stock rod. |
| No measured CD70 data | Validation is weak | High | State the limit. Rely on published-case validation. Search for magazine dyno data. |
| Current Pakistani petrol octane unknown | Knock constraint may be wrong | Medium | Report RON 87 and RON 92 |
| MMT limit has no recorded source | Text may be unsupported | Medium | Add the 2018 directive link or remove the figure |
| Small predicted gains | Paper may look weak | Medium | Report honest results. Modest gains with validation are publishable. |
| Knock model accuracy | Constraint too loose or too tight | Medium | Calibrate the knock constant on the published case if possible |
| Predatory journals | Paper not credible | Low | Check Scopus, DOAJ, or the HEC recognised list before submitting |

---

## 14. Publication venues

- **Preprint:** arXiv (no peer review, fast).
- **Pakistan:** NUST Journal of Engineering Sciences; Mehran University Research Journal of Engineering and Technology; UET Lahore journals; Pakistan Journal of Engineering and Applied Sciences (PJEAS). Check scope and HEC recognition.
- **International:** SAE and the International Journal of Engine Research require stronger validation than this plan provides without measured data. Treat them as later targets.

---

## 15. Phase 2 and 3 (out of scope)

- **Phase 2:** combustion chamber shape with reduced CFD ([OpenFOAM](https://openfoam.org/)) and a Gaussian process surrogate.
- **Phase 3:** full geometric redesign, including bore and stroke. Needs a cluster and physical testing. Vehicle-level inputs (82 kg dry weight, tyres, final drive) are used there, not in Phase 1.

---

## 16. Sources

Full register with status is in spec sheet v10, section 10. The sources this plan relies on are listed here with links.

### 16.1 Official Atlas Honda (CD70)
1. Atlas Honda CD70 product page (fetched 9 Oct 2026): https://www.atlashonda.com.pk/cd70/
2. Atlas Honda CD70 Specifications PDF (fetched 9 Oct 2026; some labels lost): https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Specifications.pdf
3. Atlas Honda CD70 Operation Guide PDF (fetched 9 Oct 2026; partial): https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Operation-Guide.pdf
4. Hondazone, genuine Atlas CD70 Euro II carburettor (no code or jets): https://hondazone.pk/product/honda-70-carburetor-euro-ii/

### 16.2 Workshop manual (older edition, provisional)
5. CD70 Workshop Manual (Urdu), Atlas Honda, unofficial Scribd upload (not accessible 9 Oct 2026): https://www.scribd.com/document/958566633/CD70-Workshop-Manual-URDU

### 16.3 CD70-specific secondary sources
6. Wikipedia, Honda 70 (checked 9 Oct 2026): https://en.wikipedia.org/wiki/Honda_70
7. PakWheels, Honda CD 70 price and specs: https://www.pakwheels.com/bikes/honda/cd-70--3/
8. Urdupoint, CD70 specs: https://www.urdupoint.com/bikes/detail/honda/4/cd-70.html
9. BikeBD, CD70 Dream 2022 vs C70: https://bikebd.com/bike-compare/honda-cd70-dream-2022/vs/honda-c-70-1970
10. Motorradundreisen, CD70 Dream 2022: https://www.motorradundreisen.de/motorraddatenbank/honda/cd70-dream-13124.html
11. Gari.pk, CD70 vs Pak Hero PH70 (2026): https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19
12. Con-Rods.com, CD70 rod kit (91 mm centre to centre): https://www.con-rods.com/for-honda-cd70-036.html
13. CMSNL, CD70 parts catalogue (slow jet sizes #38 / #40 / #42): https://www.cmsnl.com/honda-cd70_model50394/partslist/
14. MotoPartsPakistan CD70 page (valve clearance 0.10 mm): https://quickreviewsandgui.wixsite.com/motopartspakistan/cd70-important-instructions-from-ow
15. Oro2u, PZ18 carburettor (CD70 1997–2004 fitment, venturi 18 and 16.5 mm): https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672
16. Oro2u, second PZ18 listing (16.5 mm): https://www.oro2u.com/carburetor-assy-honda-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672
17. Randakks, Keihin main jet sizes #60–#78 (general, not CD70): https://www.randakks.com/main-jet-primary-keihin-99201-601-type-sizes-60-to-78.html
18. K&L engine valve set, C70K / CT70 family (head diameters): https://4into1.com/k-l-engine-valve-set-honda-s65-c-ct-sl-xl70/

### 16.4 Sibling models and other-model sources (not used as CD70 values)
19. Webbikeworld, Honda C70 Passport (CR 8.8, source of the 8.8 figure): https://www.webbikeworld.com/honda-cub-70/
20. LRIO, Honda C70 specifications: https://lrio.com/news/motos/c70/c70-specifications
21. Motorcycle Spare Parts, C70Z carburettor parts (main #72, slow #38): https://www.motorcyclespareparts.eu/en/honda-parts/1982-c70z-scooters/carburettor-2
22. Vintage Honda twins forum (#35 slow jet on CB/CL 350/360): https://www.vintagehondatwins.com/forums/goto/post?id=39609
23. Howtomotorcyclerepair, XR70R valve adjustment (0.05 mm, other model): https://howtomotorcyclerepair.com/how-to-honda-50-70cc-valve-adjustment-xr70r/
24. Motodealers, 2021 Atlas CD 70 (CR 8.8, tank 9.0 L; rejected): https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs

### 16.5 Fuel and octane
25. PakWheels, agreement on higher-grade petrol (RON 92 plan): https://www.pakwheels.com/blog/agreement-signed-higher-grade-petrol/amp
26. Carspirit, RON 92 approved by ECC: https://carspiritpk.com/ron-92-petrol-approved-for-use-in-pakistan-by-ecc
27. ProPakistani, RON 92 stations: https://propakistani.pk/?p=107513
28. The News, RON 92 import: https://www.thenews.com.pk/print/145758-Import-of-RON-92-standard-petrol-likely-to-start-in-November
29. ARY News, petrol price Aug 2026 (no grade stated): https://www.arynews.tv/petrol-price-in-pakistan-for-august-13-2026
30. Business Recorder, OGRA fuel context (from v6, not re-checked): https://www.brecorder.com/news/404758

### 16.6 Research and validation references
31. Morrissey and Shedd, SAE 2008-32-0043: https://doi.org/10.4271/2008-32-0043
32. Avelar et al., SAE 2019-36-0170: https://doi.org/10.4271/2019-36-0170
33. Peñaranda et al., ITA / Honda GX-35: https://amcaonline.org.ar/ojs/index.php/mc/article/download/3359/3278
34. Dresler and Richtář, MZ125: https://pernerscontacts.upce.cz/index.php/perner/article/download/900/734/1569
35. Deb et al., NSGA-II (2002): https://repository.ias.ac.in/9403
36. Akiba et al., Optuna (2019): https://arxiv.org/pdf/1907.10902
37. OpenWAM documentation: https://openwam.webs.upv.es/docs/
38. Heywood, *Internal Combustion Engine Fundamentals* (textbook, no link)

### 16.7 Gaps
- **MMT limit (40 mg/L, then 24 mg/L):** no source link was recorded in any earlier version. Add the 2018 directive before submission.
- **PZ19 and PZ22 carburettor codes:** not found in any page checked.
- **daraz, OLX, techmen carburettor pages:** not opened. Check and add if used.
