# CD70 tuning study (agent project)

Honda CD70 (72 cc, 4-stroke, air-cooled) simulation study: can the engine's torque and fuel economy be improved with
tuning changes (compression ratio, ignition curve, main jet, valve timing/size), and how sure can we be when the real engine is unknown?

## How the human uses this

1. Install Python 3.10+ and opencode. Copy this folder to the laptop.
2. In the folder: `pip install -r requirements.txt` (the agent also does this in task T-002).
3. Run `opencode` in the folder and select your model (MiMo V2.6 Flash).
4. Every day, in a NEW session, type: **/work** (or, if that command is missing, type: *Read AGENTS.md and run python scripts/session_start.py, then work through the tasks*).
5. When the agent says `RESEARCH COMPLETE`, run `/finalpaper` (builds `paper/PAPER_DRAFT.docx` with all figures and tables; fill the `[[...]]` placeholders). Optionally, give `FINAL_HANDOFF.md`, `paper_inputs/`, `figures/`, `reports/` and `docs/spec_sheet_v11.md` to a smart model and ask it to write the paper (abstract, methods, results, discussion, limitations).

Keep the laptop plugged in and awake while a job is running. Long jobs keep running when you close a session and resume if they were stopped.
If the agent gets confused: type **/unstick**. If you want a status without work: **/status**.

Expected total computer time: about 1 to 3 days on an 8 GB i7 laptop (the agent needs roughly 5 to 15 sessions).

## Version 13 (what changed from v12)

- Fixed: T-033 blocker (binary-safe `check_stage.py`); Windows lock hashes (`locks.py` uses POSIX paths); git identity (`git -c`, no `git config`); redirection-free test report (`capture.py`); weak T-011 gate (`check_stage.py pytest`).
- Long jobs may wait up to 200 x 100 s (about 5.5 hours) per session, instead of about 1 hour.
- Physics, config values, seeds, bounds and the number of draws are unchanged from v12. Stage results from v12 remain valid.

To continue an existing v12 run on your laptop: copy `data/`, `runs/`, `reports/`, `figures/`, `paper_inputs/` and `state/stage_done/` from the v12 folder into the v13 folder, then start the agent with `/work`. Finished stages are skipped automatically. To start fresh, do nothing extra.


## Version 14 (what changed from v13)

- New validation layer for fuel economy (T-035): city cycle with a stop-and-go term, run-in scenario, steady-speed diagnostic, and a comparison with published and owner figures under a rule fixed before results.
- Calibration, optimiser, physics and all existing results are unchanged from v12 and v13.
- Read docs/RELEASE_NOTES_v14.md for what the model still gets wrong (city figure and run-in size).
- Best next step for you: fill data/raw/fuel_log.csv from your own fill-ups (template: data/raw/fuel_log_template.csv).

## Version 15 (what changed from v14)

- The optimiser (and sensitivity analysis, robustness check, figures and paper) now uses the city-cycle fuel use as its fuel objective. Set in config/optimiser.yaml. Steady cruise remains as a diagnostic.
- Calibration, physics, bounds, seeds and draw counts are unchanged.
- Start from scratch: unzip, open the folder in opencode, type /work. There are no old results to migrate.
- Read docs/RELEASE_NOTES_v15.md for what was verified here and what was not.

## Version 16

- Paper builder includes the fuel validation section (4.10), generated from reports/fuel_validation.md.
- Start from scratch with /work. See docs/RELEASE_NOTES_v16.md for what was and was not verified here.
