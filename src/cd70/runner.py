"""Batch runner: evaluate many rows in parallel, store parquet parts, resume after a crash.

LOCKED FILE for the agent. A "row" is a flat dict. `func_path` is "module:function"; the function takes one row
dict and returns a dict of results. Failures are stored (status='error'), never raised.
"""

from __future__ import annotations

import importlib
import os
import time
import traceback
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed


def _call(func_path: str, row: dict) -> dict:
    mod, name = func_path.split(":")
    fn = getattr(importlib.import_module(mod), name)
    t0 = time.perf_counter()
    try:
        res = fn(row)
        out = {**row, **res}
        out.setdefault("status", "ok")
    except Exception as e:  # noqa: BLE001 - we want every failure stored
        out = {**row, "status": "error", "error": f"{type(e).__name__}: {e}"[:300], "trace": traceback.format_exc()[-400:]}
    out["wall_s"] = time.perf_counter() - t0
    return out


def run_batch(func_path: str, rows: list, out_dir: str | Path, chunk: int = 200, n_jobs: int = 2,
              progress: bool = True, start_part: int = 0) -> pd.DataFrame:
    """Run rows, writing out_dir/part_00000.parquet ... Skips parts that already exist (resume). Returns all rows found in out_dir."""
    src = str(Path(__file__).resolve().parents[1])
    os.environ["PYTHONPATH"] = src + os.pathsep + os.environ.get("PYTHONPATH", "")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n_parts = (len(rows) + chunk - 1) // chunk
    t_start = time.perf_counter()
    for i in range(n_parts):
        part = out_dir / f"part_{start_part + i:05d}.parquet"
        if part.exists():
            continue
        sub = rows[i * chunk:(i + 1) * chunk]
        res = Parallel(n_jobs=n_jobs, backend="loky")(delayed(_call)(func_path, r) for r in sub)
        pd.DataFrame(res).to_parquet(str(part) + ".tmp", index=False)
        Path(str(part) + ".tmp").rename(part)
        if progress:
            done = i + 1
            el = time.perf_counter() - t_start
            print(f"[runner] part {done}/{n_parts} done, elapsed {el:.0f}s", flush=True)
    return load_parts(out_dir)


def load_parts(out_dir: str | Path) -> pd.DataFrame:
    files = sorted(Path(out_dir).glob("part_*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
