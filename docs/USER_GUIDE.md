# User guide (for the human)

You only start sessions and read the result. The agent does everything else.

## 0. Watching jobs and surviving shutdowns

- Every long job opens its **own console window** (title "CD70 job ...") with live output. Do not close it and **do not click inside it** (on Windows a click pauses the program until you press Enter). Minimise it instead.
- Want a dashboard? Open another terminal in the project folder and run `python scripts\monitor.py`: it shows tasks done, finished stages, each job's state and its last log line. It changes nothing.
- **Power off, sleep, Windows update, closed window:** nothing is lost except the unfinished chunk. Calibration and sensitivity save every ~500 runs; optimiser runs are re-run from their start (one run is about 30-120 minutes). Next day just start a session: it automatically restarts any killed job (`jobs.py resume`) and skips finished stages.
- Tip: set Windows power settings to "never sleep when plugged in" while a job runs.

## 0b. The paper: /finalpaper

- `/work` tells you when everything is done ("RESEARCH COMPLETE ... run /finalpaper").
- `/finalpaper` refuses to run before that ("NOT READY ..."). When ready it runs `scripts/build_paper.py`, which assembles the whole paper from result files only (no hand-typed numbers): abstract, introduction, data sources, model, calibration, baseline curves, sensitivity ranking (OFAT, Morris, Sobol), optimiser comparison, robust designs and **baseline-versus-design comparison figures and tables**, scenario grid, value of information, feasibility, discussion, scope and extensions, conclusions, data/code availability, AI-use declaration, references and appendices. It then runs the number verifier and a checklist.
- Output in `paper/`: `PAPER_DRAFT.docx` (and `.md`) in journal structure (title, highlights, abstract, nomenclature, introduction with related work and research questions, methods with workflow figure and rule/calibration/design tables, results, discussion, limitations, conclusions, data availability, declarations, references numbered by first citation, five appendices), `COVER_LETTER.md`, `TITLE_OPTIONS.md`, `SUBMISSION_GUIDE.md` (target journals, pre-submission steps, a prompt for a polishing model, likely reviewer objections), `PLACEHOLDERS.md`, `CHECKLIST.md`, and `supplement/` (spec sheet, code zip, raw-results zip). Search the Word file for `[[` and fill: authors, affiliations, e-mail, code link, data link, funding, acknowledgements, conflict of interest, journal.
- Language polishing: give the draft to a smart model with the instruction not to change numbers, claim words or figures.
- Power cut / session killed: see 0 above; nothing finished is lost.


**arXiv-ready output (automatic).** `/finalpaper` also writes `paper/arxiv/main.tex` + `paper/arxiv/figures/`, a compiled `paper/arxiv/main.pdf` (when LaTeX is installed; arXiv compiles the .tex itself anyway), `paper/arxiv_source.zip` (upload this to arXiv) and `paper/ARXIV_METADATA.md` (title, plain-text abstract under 1920 characters, suggested categories, comments line, licence, upload steps). Fill every `[[...]]` first (search main.tex for `[[`). Every figure is checked for x and y axis labels when it is drawn (`scripts/figlint.py`), and the checklist fails if the baseline-vs-design comparison figures (f13-f15), the pattern figure (f12) or the baseline curves (f02) are missing.

## 1. One-time setup (about 20 minutes)

1. Install Python 3.11 or 3.12 for Windows from python.org. Tick "Add python.exe to PATH". (3.13 also works; if packages fail to install use 3.12.)
2. Install Git for Windows (git-scm.com). Install opencode (follow https://opencode.ai/docs, usually `npm i -g opencode-ai` after installing Node.js).
3. Unzip `cd70_agent_project.zip`. You get a folder `cd70`. Put it somewhere short, e.g. `C:\research\cd70` (no spaces).
4. Open PowerShell in that folder and run: `pip install -r requirements.txt`. (If it says python not found, try `py -m pip install -r requirements.txt`.) This takes several minutes (Cantera and Numba are big).
5. Run `opencode` in the same folder. Connect your provider and choose the model (MiMo V2.6 Flash) with the `/models` command.
6. Windows power settings: Settings > System > Power: set "Sleep" to Never while plugged in, and keep the laptop plugged in. A sleeping laptop pauses the computations (they resume, but nothing runs).

## 2. Every day

1. Open PowerShell in the `cd70` folder, run `opencode` (a NEW session, not an old one).
2. Type `/work` and press Enter. If that command is not listed, type: `Read AGENTS.md, run python scripts/session_start.py and follow it`.
3. Leave it. The agent works through tasks, starts long background jobs, and when it stops it writes 3 lines: tasks done today, what is still running, what is next.
4. The background jobs keep running after the session ends (laptop on, not asleep). Next day open a new session and type `/work` again.
5. When the agent says `RESEARCH COMPLETE`, go to section 5.

Total: about 5-15 sessions and 1-3 days of computer time. The longest steps are the calibration (1-3 h per valve-timing reading) and the optimisation (2-6 h).

## 3. How the agent is configured (what loads when)

| Piece | File | When it loads |
|---|---|---|
| Rules | `AGENTS.md` and `opencode.json` ("instructions") | automatically, at the start of every session |
| Permissions | `opencode.json` ("permission") | always active: the agent may run any command, but cannot edit protected files (model, config, tests, tasks, docs, scripts) and cannot `git push`, `sudo`, delete data |
| Commands | `.opencode/commands/*.md` | you type `/work`, `/status`, `/unstick`, `/finish` |
| Skills | `.opencode/skills/*/SKILL.md` (run-long-job, write-honest-report, debug-failure) | opencode lists their names to the agent automatically; the agent loads the full text on demand with its skill tool. AGENTS.md and the task texts tell it exactly when to load each one, because a weak model will not remember otherwise |
| Task list | `tasks/T-*.md` | the agent asks `python scripts/task.py next` and gets one task at a time; a task is ticked only if its machine-checked gate passes |
| Protection | `state/LOCKS.json` | `python scripts/locks.py check` runs at every session start and in the health check; it detects any edit of protected files |

The agent never has to remember anything between sessions: `JOURNAL.md`, `state/STATE.json`, `OPEN_ITEMS.md`, `BLOCKERS.md` and the job status files hold everything, and `session_start.py` prints it.

## 4. Check progress yourself (no agent needed)

In PowerShell in the folder: `python scripts/task.py status`, `python scripts/task.py list`, `python scripts/jobs.py status`, `python scripts/show.py JOURNAL.md 15`, `python scripts/show.py BLOCKERS.md 30`. Or type `/status` in opencode.

## 5. When it is finished

Give a smart model (e.g. Claude) these files: `FINAL_HANDOFF.md`, the folders `paper_inputs/`, `figures/`, `reports/`, and `docs/spec_sheet_v11.md`, `docs/MODEL_SPEC.md`, `docs/ANALYSIS_SPEC.md`, `docs/CLAIM_RULES.md`, `docs/LIMITATIONS.md`. Ask it to write the abstract, methods, results, discussion and limitations, to use only the numbers in `paper_inputs/RESULTS_FACTS.json`, to respect the claim levels, and to include every red-team flag.

## 6. If something goes wrong

| Symptom | What to do |
|---|---|
| Agent loops or seems lost | type `/unstick` |
| Agent says "lock violation" | type `/unstick` (it restores files with git) |
| Job shows DEAD | the laptop slept or opencode was closed: type `/work`, it restarts the job and resumes |
| Out of memory (8 GB) | tell the agent: "set CD70_JOBS=2 and CD70_PAR=2 and restart the job" (it knows how from the run-long-job skill) |
| `pip install` fails for cantera/numba | use Python 3.12 (uninstall 3.13), repeat step 4 |
| Agent asks you to run a command | it should not; reply "run it yourself with your terminal tool" |
| A task is blocked | read `BLOCKERS.md`; most blocks are fine (e.g. valve timing A may have too few engines and is skipped automatically) |

## 6b. How the agent is kept on track

- Locked files (model, config, tests, tasks, docs, scripts, AGENTS.md, opencode.json) are hash-checked; `task.py done` refuses to tick anything if one changed.
- The agent can only edit `src/cd70/custom`, `scripts/custom`, `tests/custom` and the records; it cannot edit `data/raw` or `data/processed`, cannot `pip install` anything except from requirements.txt, cannot use curl/wget/npm, cannot `git push/reset/clean`, and cannot delete data.
- Every report must pass `verify_numbers.py` (numbers must exist in result files) and the claim-level rules before its task is ticked.
- It works one task at a time from the list; new ideas go to OPEN_ITEMS.md. Web use is allowed only in T-034.
- `python scripts/health.py` and `python scripts/locks.py check` are yours to run any time to confirm nothing was damaged.
- Limits: an agent with a terminal can still make mistakes inside allowed areas; that is why results carry claim levels and the audit/red-team tasks exist. Check `JOURNAL.md` now and then.

## 7. What the results can and cannot mean (read before the paper)

- No real CD70 was measured. Everything is a model prediction conditional on: 5.05 hp @ 7500, 5.0 Nm @ 5500, 12.7 bar cranking, and a real-world top speed of 80-90 km/h.
- Top speed: with the sheet gearing 80-90 km/h needs about 8700-9800 rpm; the model extrapolates power to 9500 rpm. The ensemble will tell you which drag area fits. Power above 7500 rpm is an extrapolation.
- Cranking: 12.7 bar at the stated 1000 rpm would imply a worn engine (about 1 mm2 leak). The model lets the test speed vary and finds speed about 350-500 rpm with a 0.3-0.45 mm2 leak fits. This is a statement about the model, not the engine.
- Valve timing A (as printed) is hard to reconcile with the other targets; B (20 degrees more per flank) is the main case. Unreconciled results are flagged by the agent.
- Every engine in the ensemble and every tested tuning passes physics and hardware rules (head skim, valve-piston clearance, valve acceleration, overlap, valve size, ignition limits, mixture, efficiency/VE/power/torque plausibility, knock and pressure limits). Anything that fails is recorded as infeasible and cannot win. The assumed limits are listed in `docs/LIMITATIONS.md`.
