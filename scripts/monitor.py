"""Live progress screen for the human. Run in its own terminal:  python scripts/monitor.py   (Ctrl+C to stop; it never changes anything).
Shows: every job (RUNNING/OK/FAILED/DEAD), time since start, last log line, tasks done, finished stages."""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import jobs  # noqa: E402


def last_line(name):
    f = jobs.JD / f"{name}.log"
    if not f.exists():
        return ""
    lines = f.read_bytes()[-4000:].decode("utf-8", "replace").strip().splitlines()
    return lines[-1][:100] if lines else ""


def main():
    while True:
        os.system("cls" if sys.platform == "win32" else "clear")
        print("CD70 MONITOR  " + time.strftime("%F %T") + "   (updates every 5 s, Ctrl+C to stop)\n")
        try:
            st = json.loads((ROOT / "state" / "STATE.json").read_text(encoding="utf-8"))
            t = st.get("tasks", {})
            print(f"Tasks done: {sum(1 for v in t.values() if v.get('status') == 'done')}   blocked: {sum(1 for v in t.values() if v.get('status') == 'blocked')}")
        except Exception:
            print("Tasks: (no state yet)")
        print(f"Finished stages: {len(list((ROOT / 'state' / 'stage_done').glob('*.done')))}\n")
        names = jobs.names()
        if not names:
            print("No jobs yet.")
        for n in names:
            s, j = jobs.state(n)
            print(f"[{s:8}] {n}  started {j.get('started', '?')}")
            print(f"           {last_line(n)}")
        if any(jobs.state(n)[0] == "DEAD" for n in names):
            print("\nA job was killed. Start a new agent session (or run: python scripts/jobs.py resume).")
        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
