"""Run this LAST in every session.  python scripts/session_finish.py ["one line: what happened / what is next"]"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sh(c):
    r = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


note = " ".join(sys.argv[1:]).strip()
if note:
    with open(ROOT / "JOURNAL.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%F %H:%M')} SESSION END: {note}\n")
code, out = sh("python scripts/health.py")
print(out)
if code:
    print("\nFIX THE PROBLEMS ABOVE, then run session_finish.py again. Do not end the session yet.")
    sys.exit(1)
print(sh("python scripts/jobs.py status")[1])
if (ROOT / ".git").exists():
    sh("git add -A")
    st = json.loads((ROOT / "state" / "STATE.json").read_text(encoding="utf-8"))
    done = sum(1 for v in st["tasks"].values() if v["status"] == "done")
    c, o = sh(f'git commit -q -m "session {st.get("sessions", "?")}: {done} tasks done. {note[:80]}"')
    print("git:", "committed" if c == 0 else "nothing new to commit")
print("\nSAFE TO END THE SESSION. Tell the user in 3 lines: tasks done today, what is running, what comes next.")
