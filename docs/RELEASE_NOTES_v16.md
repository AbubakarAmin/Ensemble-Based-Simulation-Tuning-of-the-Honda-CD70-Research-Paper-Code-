# Release notes v16

## What changed
- scripts/build_paper.py: new section 4.10 (fuel validation) reads reports/fuel_validation.md and copies its tables and SUMMARY line; if T-035 has not run, the paper says NOT AVAILABLE. No fuel number is typed by hand.
- Paper and figure wording uses city fuel where it used cruise fuel (since v15).
- Everything else unchanged from v15: calibration, physics, objective (city cycle), validation rules, tests.

## Verified here
- All scripts compile; lint clean; locked tests and health gate (see report).
- Paper builder compiles and its new section was checked by reading the code path; the full paper build was NOT run here (it needs the complete results of the full study).

## Not verified here
- Full calibration, full optimisation, full figures, full paper build, and the runtime on your computer. These are the job of the from-scratch run.
