# Release notes v13

Scope: the v12 pack plus fixes from the first real run (Windows, Python 3.12.10). Physics, config values, seeds, bounds and draw counts are unchanged.

## Fixes
1. T-033 gate crash (blocker): `scripts/check_stage.py file` read every file as UTF-8. It now checks binary files (png, jpg, pdf, parquet, npz, docx, xlsx, zip) by existence, minimum size and, for PNG, the signature.
2. `scripts/locks.py` produced backslash paths on Windows, so `locks.py check` failed on a clean tree. Keys are now POSIX paths, so Windows and Linux builds agree. The DESIGN_NOTES exclusion now works on Windows too.
3. T-003 asked the agent to run `git config`, which `opencode.json` denies. T-003 now commits with `git -c user.name=... -c user.email=...`.
4. T-011 gate passed on "1 failed, 31 passed" (it searched for the word "passed"). New gate `check_stage.py pytest` requires a passing summary line and no failed or errored tests.
5. T-011 used `> file 2>&1`, which the rules forbid and which writes UTF-16 in Windows PowerShell 5.1. New `scripts/capture.py` writes UTF-8 with no shell redirection.
6. `config/calibration.yaml` comment referred to spec v10. It now says v11 (comment only; no value changed).
7. `docs/archive_plan_v3.md` moved to `docs/archive/` so the agent does not read it as a current plan.
8. `JOURNAL.md`, `BLOCKERS.md` and `state/STATE.json` reset (v12 test-run lines removed from the journal).

## Changes
- Long jobs: 200 waits of 100 seconds per session (about 5.5 hours) instead of 40 (about 1 hour). Applies to every long-job task and the run-long-job skill.
- New `python scripts/task.py reopen T-0xx`.
- New tests in `tests/locked/test_tooling.py` cover the binary check, the pytest gate, POSIX lock keys and capture.py.
- LIMITATIONS item 11 records the mileage holdout result (model optimistic by about 1.3 to 1.7 times against published figures).

## Known open items (not fixed in v13; see OPEN_ITEMS.md)
- Holdout optimism (documented as a limitation; no value changed on purpose).
- Top speed calibration uses an owner statement and a literature range (MEDIUM confidence).
- If T-030 (main calibration) gets fewer than 100 accepted engines, every task after it waits. Only timing A has a fallback.

## Migrating a v12 run
Copy `data/`, `runs/`, `reports/`, `figures/`, `paper_inputs/` and `state/stage_done/` from the v12 folder. Keep the new `state/STATE.json`. Finished stages are skipped; T-033 is rerun with the fixed gate.
