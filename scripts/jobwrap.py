"""Internal: runs one job command, shows its output live in this window, appends it to the log, writes the exit code file. Used by jobs.py only."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JD = ROOT / "state" / "jobs"
name, cmd = sys.argv[1], sys.argv[2]
if sys.platform == "win32":
    os.system(f"title CD70 job {name} - do not close, do not click inside this window")
print(f"CD70 job {name}\n{cmd}\nIf this window is closed or the computer restarts, the next agent session restarts the job and finished parts are kept.\n", flush=True)
env = dict(os.environ, PYTHONUNBUFFERED="1")
with open(JD / f"{name}.log", "ab") as lf:
    p = subprocess.Popen(cmd, shell=True, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    for raw in p.stdout:
        lf.write(raw)
        lf.flush()
        sys.stdout.write(raw.decode("utf-8", "replace"))
        sys.stdout.flush()
    code = p.wait()
(JD / f"{name}.exit").write_text(str(code), encoding="utf-8")
print(f"\nJOB {name} FINISHED with exit code {code}. You may close this window.", flush=True)
