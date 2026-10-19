---
description: Recover when the agent is confused or looping
---
Stop what you were doing. Do exactly this and nothing else:

1. Run `python scripts/locks.py check`. If it reports a violation, undo your change with `git checkout -- <file>` for each listed file.
2. Run `python scripts/health.py` and fix only the problems it lists.
3. Run `python scripts/jobs.py status`. If a job is DEAD or FAILED, restart it with its `ensure` command from the task text.
4. Run `python scripts/task.py next` and continue with that task from its first line. If you already tried this task 3 times, block it with `python scripts/task.py block <ID> "<what you tried and the exact error>"`.
