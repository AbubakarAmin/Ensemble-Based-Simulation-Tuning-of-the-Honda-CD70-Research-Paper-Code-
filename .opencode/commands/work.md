---
description: Start or continue the CD70 research (daily command)
---
You are the CD70 research agent. Read AGENTS.md (it is already in your instructions) and follow it exactly.

Session start report (already run for you):

!`python scripts/session_start.py`

If the session start report above says RESEARCH COMPLETE, do nothing else: tell the user "The research is finished. Run /finalpaper in a new session to build the paper." and stop.

Otherwise do the NEXT TASK shown above, exactly as written. After each task run its `task.py done` command, then `python scripts/task.py next`, and continue. Work until no task is ready or you have done a lot of work, then run `python scripts/session_finish.py "one line note"` and tell the user in 3 lines: tasks finished today, what is running in the background, what comes next. Do not ask the user questions; if something is unclear, choose the safest option, write it in DECISIONS.md, and continue.
