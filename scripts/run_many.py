"""Run a named GROUP of stage commands, skipping the ones already finished.   python scripts/run_many.py GROUP [--scale smoke]
Groups: cal_A cal_B base_A base_B sens_A sens_B opt_B opt_A robopt_B robopt_A pick_B pick_A stats_B stats_A
Optimiser groups run several single-process runs in parallel; stats groups run one at a time (they parallelise inside).
Always run it through scripts/jobs.py (see the task text). Re-running after a crash is safe."""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_stage import make_key  # noqa: E402

DONE = ROOT / "state" / "stage_done"


def cmds(group, scale):
    sc = ["--scale", scale]
    out = []  # (stage, timing, cls, method, seed, which)
    T = group.split("_")[-1]
    kind = group.rsplit("_", 1)[0]
    if kind == "cal":
        out = [("calibrate", T, "C", "nsga2", 1, "knee")]
    elif kind == "base":
        out = [("curves", T, "C", "nsga2", 1, "knee")]
    elif kind == "sens":
        out = [(s, T, "C", "nsga2", 1, "knee") for s in ("ofat", "morris", "sobol")]
    elif kind == "opt":
        classes, seeds = (("A", "B", "C"), (1, 2, 3, 4, 5)) if T == "B" else (("A", "C"), (1, 2, 3))
        out = [("optimise", T, c, m, s, "knee") for c in classes for m in ("nsga2", "tpe", "random") for s in seeds]
    elif kind == "robopt":
        classes, seeds = (("A", "B", "C"), (1, 2, 3)) if T == "B" else (("C",), (1, 2))
        out = [("optimise_robust", T, c, "nsga2", s, "knee") for c in classes for s in seeds]
    elif kind == "pick":
        classes = ("A", "B", "C") if T == "B" else ("A", "C")
        out = [("pick", T, c, "nsga2", 1, "knee") for c in classes]
    elif kind == "stats":
        classes = ("A", "B", "C") if T == "B" else ("A", "C")
        for c in classes:
            for w in ("econ", "power", "knee"):
                out += [("robust", T, c, "nsga2", 1, w), ("voi", T, c, "nsga2", 1, w)]
        out += [("grid", T, "C", "nsga2", 1, w) for w in ("econ", "power", "knee")]
    else:
        raise SystemExit(f"unknown group {group}")
    res = []
    for stage, t, c, m, s, w in out:
        key = make_key(stage, t, scale, c, m, s, w)
        cmd = [sys.executable, "scripts/run_stage.py", stage, "--timing", t, "--cls", c, "--method", m, "--seed", str(s), "--which", w] + sc
        res.append((key, cmd))
    return res


def main():
    group = sys.argv[1]
    scale = sys.argv[sys.argv.index("--scale") + 1] if "--scale" in sys.argv else "full"
    todo = [(k, c) for k, c in cmds(group, scale) if not (DONE / f"{k}.done").exists()]
    print(f"[{group}] {len(todo)} runs to do", flush=True)
    kind = group.rsplit("_", 1)[0]
    par = 1
    if kind in ("opt", "robopt"):
        par = int(os.environ.get("CD70_PAR", max(1, min(4, (os.cpu_count() or 4) - 2))))
    env = dict(os.environ)
    if par > 1:
        env["CD70_JOBS"] = "1"
    fails = []

    def go(item):
        k, c = item
        t0 = time.time()
        r = subprocess.run(c, cwd=ROOT, env=env, capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"[{group}] {'ok  ' if ok else 'FAIL'} {k} {time.time() - t0:.0f}s", flush=True)
        if not ok:
            fails.append(k)
            print("\n".join((r.stdout + r.stderr).splitlines()[-8:]), flush=True)

    with ThreadPoolExecutor(par) as ex:
        list(ex.map(go, todo))
    print(f"[{group}] finished, {len(fails)} failures: {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
