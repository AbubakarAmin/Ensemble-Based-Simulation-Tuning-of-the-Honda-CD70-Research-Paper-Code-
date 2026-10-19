"""One command for every experiment stage. Example:
  python scripts/run_stage.py calibrate --timing B
  python scripts/run_stage.py optimise --timing B --cls C --method nsga2 --seed 1
Writes state/stage_done/<key>.done when finished. Safe to re-run: finished parts are skipped (resume).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import experiments as E  # noqa: E402


def make_key(stage, timing, scale, cls="C", method="nsga2", seed=1, which="knee"):
    extra = {"optimise": [cls, method, str(seed)], "optimise_robust": [cls, str(seed)], "pick": [cls],
             "robust": [cls, which], "grid": [cls, which], "voi": [cls, which]}.get(stage, [])
    return "-".join([stage, timing, scale] + extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["calibrate", "curves", "ofat", "morris", "sobol", "optimise", "optimise_robust",
                                      "pick", "robust", "grid", "voi"])
    ap.add_argument("--timing", required=True, choices=["A", "B"])
    ap.add_argument("--cls", default="C", choices=["A", "B", "C"])
    ap.add_argument("--method", default="nsga2", choices=["nsga2", "tpe", "random"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--which", default="knee", choices=["econ", "power", "knee"])
    ap.add_argument("--scale", default="full", choices=["smoke", "full"])
    a = ap.parse_args()
    key = make_key(a.stage, a.timing, a.scale, a.cls, a.method, a.seed, a.which)
    t0 = time.time()
    T, S = a.timing, a.scale
    if a.stage == "calibrate":
        out = E.calibrate(T, S)
    elif a.stage == "curves":
        out = str(E.baseline_curves(T, S))
    elif a.stage == "ofat":
        out = f"{len(E.sens_ofat(T, S))} rows"
    elif a.stage == "morris":
        out = f"{len(E.sens_morris(T, S))} rows"
    elif a.stage == "sobol":
        out = f"{len(E.sens_sobol(T, S))} rows"
    elif a.stage == "optimise":
        out = str(E.optimise(T, a.cls, a.method, a.seed, S))
    elif a.stage == "optimise_robust":
        out = str(E.optimise_robust(T, a.cls, a.seed, S))
    elif a.stage == "pick":
        out = {k: "ok" for k in E.pick_designs(T, a.cls, S)}
    elif a.stage == "robust":
        out = f"{len(E.robust_paired(T, a.cls, a.which, S))} members"
    elif a.stage == "grid":
        out = f"{len(E.scenario_grid(T, a.cls, a.which, S))} rows"
    else:
        out = f"{len(E.voi(T, a.cls, a.which, S))} rows"
    d = ROOT / "state" / "stage_done"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{key}.done").write_text(json.dumps({"key": key, "seconds": round(time.time() - t0), "out": out}, default=str), encoding="utf-8")
    print(f"DONE {key} in {time.time() - t0:.0f}s: {out}")


if __name__ == "__main__":
    main()
