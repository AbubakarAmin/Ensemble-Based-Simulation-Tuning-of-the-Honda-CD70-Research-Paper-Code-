"""Run this FIRST in every session.  python scripts/session_start.py"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sh(c):
    r = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


st = ROOT / "state" / "STATE.json"
s = json.loads(st.read_text(encoding="utf-8")) if st.exists() else {"tasks": {}, "sessions": 0}
s["sessions"] = s.get("sessions", 0) + 1
st.parent.mkdir(exist_ok=True)
st.write_text(json.dumps(s, indent=1, sort_keys=True), encoding="utf-8")
print(f"=== SESSION {s['sessions']} START ===")
print(sh("python scripts/task.py status"))
print("\n--- locks / health (quick) ---")
print(sh("python scripts/health.py --quick"))
print("\n--- background jobs ---")
print(sh("python scripts/jobs.py resume"))
print(sh("python scripts/jobs.py status"))
j = ROOT / "JOURNAL.md"
if j.exists():
    print("\n--- last journal lines ---")
    print("\n".join(j.read_text(encoding="utf-8").splitlines()[-12:]))
o = ROOT / "OPEN_ITEMS.md"
if o.exists() and o.read_text(encoding="utf-8").strip():
    print("\n--- OPEN_ITEMS.md (read it) ---")
    print(o.read_text(encoding="utf-8")[-1500:])
print("\n--- RULES (full text in AGENTS.md) ---")
print("1 One task at a time via task.py.  2 Never edit locked files (python scripts/locks.py check).")
print("3 Long runs only through scripts/jobs.py.  4 Never invent numbers; copy them from files in data/ or reports/.")
print("5 Stuck 3 times -> task.py block.  6 End the session with python scripts/session_finish.py.\n")
if s.get("tasks", {}).get("T-080", {}).get("status") == "done":
    print("*** RESEARCH COMPLETE. All work is done. The user should now run /finalpaper to build the paper. ***\n")
print("--- NEXT TASK ---")
print(sh("python scripts/task.py next"))
