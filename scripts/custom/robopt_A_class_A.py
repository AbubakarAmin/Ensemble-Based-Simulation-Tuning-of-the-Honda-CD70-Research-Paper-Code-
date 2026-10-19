"""One-off helper (2026-10-19): run the ensemble-robust optimisations for TIMING A, CLASS A.

Why this exists: the locked scripts/run_many.py runs `robopt_A` only on class C, but the locked
groups `pick_A` and `stats_A` (and `opt_A`) all treat timing A as classes A and C. With no
data/processed/optrob/A_A_*.parquet, `pick_designs("A","A")` globs an empty list and
pd.concat([]) raises "No objects to concatenate". This helper produces exactly the two
optimise_robust runs the locked pack expects (timing A, class A, seeds 1 and 2, matching the
timing-A robust seed budget used for class C), writing the same stage_done keys as run_stage.
Safe to re-run: finished stages are skipped.

Run through scripts/jobs.py (long job):
  python scripts/jobs.py ensure robopt_A_A -- python scripts/custom/robopt_A_class_A.py
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEEDS = (1, 2)


def go(seed):
    cmd = [sys.executable, "scripts/run_stage.py", "optimise_robust",
           "--timing", "A", "--cls", "A", "--seed", str(seed)]
    env = dict(os.environ)
    env["CD70_JOBS"] = "1"  # one internal worker per process, like run_many does for optimiser groups
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    return (seed, r.returncode)


def main():
    print(f"[robopt_A_class_A] running timing A / class A robust optimisations, seeds {SEEDS}", flush=True)
    with ThreadPoolExecutor(len(SEEDS)) as ex:
        results = list(ex.map(go, SEEDS))
    for seed, code in results:
        print(f"[robopt_A_class_A] seed {seed}: {'ok' if code == 0 else 'FAIL'} (exit {code})", flush=True)
    fails = [s for s, c in results if c != 0]
    print(f"[robopt_A_class_A] finished, {len(fails)} failures: {fails}", flush=True)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
