"""Background jobs that survive the end of a chat session.
  python scripts/jobs.py ensure NAME -- <command...>   start the job unless it is running or finished OK (crash => restart)
  python scripts/jobs.py status [NAME]                 one line per job: RUNNING / OK / FAILED / DEAD
  python scripts/jobs.py wait NAME [--timeout 90]      wait up to N seconds, prints one status line
  python scripts/jobs.py log NAME                      last 20 log lines
  python scripts/jobs.py resume                        restart jobs that were killed (done automatically at session start)
Only ONE heavy job runs at a time (the computer has 8 GB RAM). A second `ensure` prints QUEUED and does nothing.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JD = ROOT / "state" / "jobs"
JD.mkdir(parents=True, exist_ok=True)


def _alive(pid, created=None):
    """True only if that exact process is still running (create time is compared, so a reused PID after a reboot is not mistaken for the job)."""
    import psutil

    try:
        p = psutil.Process(pid)
        if p.status() == psutil.STATUS_ZOMBIE:
            return False
        return created is None or abs(p.create_time() - created) < 2.0
    except psutil.Error:
        return False


def state(name):
    f = JD / f"{name}.json"
    if not f.exists():
        return "NONE", {}
    j = json.loads(f.read_text(encoding="utf-8"))
    ex = JD / f"{name}.exit"
    if ex.exists():
        code = ex.read_text(encoding="utf-8").strip()
        return ("OK" if code == "0" else "FAILED"), j
    return ("RUNNING" if _alive(j["pid"], j.get("created")) else "DEAD"), j


def names():
    return sorted(p.stem for p in JD.glob("*.json"))


def running():
    return [n for n in names() if state(n)[0] == "RUNNING"]


def line(name):
    s, j = state(name)
    extra = f" cmd={j.get('cmd', '')[:80]}" if s != "OK" else ""
    return f"{name}: {s}{extra}"


def ensure(name, cmd):
    s, _ = state(name)
    if s in ("RUNNING", "OK"):
        print(line(name))
        return 0
    other = [n for n in running() if n != name]
    if other:
        print(f"{name}: QUEUED (waiting for {other[0]})")
        return 0
    for ext in (".exit", ".json"):
        (JD / f"{name}{ext}").unlink(missing_ok=True)
    kw = {"stdin": subprocess.DEVNULL}
    if sys.platform == "win32":
        kw["creationflags"] = 0x00000010  # CREATE_NEW_CONSOLE: a visible window that shows the live job output
    else:
        kw["stdout"] = kw["stderr"] = subprocess.DEVNULL
        kw["start_new_session"] = True
    p = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "jobwrap.py"), name, cmd], cwd=ROOT, **kw)
    try:
        import psutil
        created = psutil.Process(p.pid).create_time()
    except Exception:
        created = None
    (JD / f"{name}.json").write_text(json.dumps({"pid": p.pid, "cmd": cmd, "started": time.strftime("%F %T"), "created": created}), encoding="utf-8")
    print(f"{name}: STARTED pid={p.pid}")
    return 0


def resume():
    """Restart every job that died (power off, sleep, window closed). Finished parts are skipped by the runners."""
    for n in names():
        s, j = state(n)
        if s == "DEAD":
            print(f"{n}: was killed, restarting")
            ensure(n, j["cmd"])
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 1
    if a[0] == "ensure":
        i = a.index("--")
        return ensure(a[1], " ".join(a[i + 1:]))
    if a[0] == "resume":
        return resume()
    if a[0] == "status":
        for n in ([a[1]] if len(a) > 1 else names()):
            print(line(n))
        if not names():
            print("no jobs")
        return 0
    if a[0] == "wait":
        t = int(a[a.index("--timeout") + 1]) if "--timeout" in a else 90
        end = time.time() + t
        while time.time() < end and state(a[1])[0] == "RUNNING":
            time.sleep(3)
        print(line(a[1]))
        return 0
    if a[0] == "log":
        lg = JD / f"{a[1]}.log"
        print("".join(lg.read_text(encoding="utf-8").splitlines(True)[-20:]) if lg.exists() else "no log")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
