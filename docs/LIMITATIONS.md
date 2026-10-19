# Known limitations (must appear in the paper)

1. No real CD70 was measured. Calibration uses two MEDIUM-confidence published numbers (5.05 hp, 5.0 Nm) and one older-manual value (12.7 bar cranking).
2. Valve timing printed in the manual is ambiguous (zero-lift or reference-lift). Both readings are run. Reading A may be harder to reconcile with the published power (check its acceptance rate).
3. Cranking pressure: the sheet says 12.7 bar at 1000 rpm (older manual). A healthy engine cannot give 12.7 bar at 1000 rpm (the model needs a blow-by area near 1 mm2, a worn engine), and a kick/starter cannot crank at 1000 rpm. The test speed is therefore an uncertain input (300-1000 rpm) next to the blow-by area; the calibration reports which combination the data prefer (smoke test: about 350-500 rpm with 0.3-0.45 mm2). The test speed itself stays unverified.
4. Friction, exhaust temperature, plenum volumes, Woschni constants, knock constants and valve lift are assumed or calibrated, not measured. Knock is a diagnostic index with the baseline margin as a free parameter.
5. Zero-dimensional model: no intake/exhaust wave dynamics, no mixture-preparation dynamics, no cycle-to-cycle variation, no thermal limits of the head/piston.
6. Top speed: the stock CD70 real-world top speed is taken as 80-90 km/h (literature and owner experience, not an instrumented test). With the sheet gearing that needs about 8700-9800 rpm in 4th, above the 7500 rpm power point, so the model extrapolates power to 9500 rpm (assumed: no rev limiter, valve float above 9500). The speedometer over-read (0-10%), drag area (0.25-0.65 m2), rolling resistance, mass and drivetrain efficiency are uncertain inputs. The model's power above 7500 rpm is an extrapolation with no data behind it. Top speed is a calibration target and reported, never optimised.
7. Cruise fuel economy depends on assumed road-load (CdA nominal 0.45 m2, Crr 0.02, mass 155 kg, all uncertain) and steady speed; real mileage includes traffic.
8. Optimum designs are often bound-limited; the bounds come from assumed hardware practicality, not from tests.
9. Design rule limits tagged HARDWARE are assumed values (e.g. head skim 0.8 mm, valve acceleration +15%).

10. No real-engine measurements exist; the study is simulation only. Mileage holdout checks agree only within a factor of about 1.6.

11. Mileage holdout (T-034, v12 run): the model predicts about 78 / 89 / 104 km/l at a steady 50 km/h (5th / 50th / 95th percentile of 60 engines), against published figures of 55, 70 and 52 km/l. The model is optimistic by a factor of about 1.3 to 1.7 against these sources. Likely cause: road-load and cruise assumptions (item 7). No config value was changed to close the gap; this is reported as a limitation.

12. City figures (v14): the city cycle uses assumed time shares and a simple stop-and-go energy term. It leaves out braking, cold starts, choke use, rider enrichment and traffic. The model city figure is therefore likely still optimistic against real city riding, and the gap is reported, not closed.
13. Run-in (v14): the run-in scenario only raises friction. In this model a 15 percent friction increase lowers city fuel economy by about 3 percent, far less than the 15 to 20 percent difference owner reports show for new bikes. Reaching that difference by friction alone would need roughly twice the friction, which is implausible for run-in alone. The likely drivers (ring and valve bedding, carburettor setting, tyres, rider style) are not modelled. This is reported as a model gap.
14. Owner and blog figures are not measured tests. The user-supplied table has no source and is reported only.
15. Optimiser objective (v15): designs are ranked by the model's city-cycle estimate. That estimate uses assumed time shares and a simple acceleration energy term, and it is still above owner city figures (see item 12). Design rankings are therefore relative to the model's own city estimate, not absolute fuel economy.
16. Calibration and fuel are kept separate on purpose: fuel is not a calibration target. If a future version calibrates to fuel, the fuel validation (T-035) must use a different source for its check.
