"""Check that the computer is ready.  python scripts/check_env.py"""
import importlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ok = True


def say(good, msg):
    global ok
    ok &= good
    print(("OK   " if good else "FAIL ") + msg)


say(sys.version_info >= (3, 10), f"python {sys.version.split()[0]} (need 3.10+)")
for m in ("numpy", "scipy", "pandas", "pyarrow", "numba", "cantera", "yaml", "SALib", "pymoo", "optuna", "sklearn",
          "matplotlib", "joblib", "psutil", "pytest", "ruff"):
    try:
        importlib.import_module(m)
        say(True, f"import {m}")
    except Exception as e:  # noqa: BLE001
        say(False, f"import {m}: {e}   -> pip install -r requirements.txt")
say((ROOT / "src/cd70/data/gas_tables.npz").exists(), "gas_tables.npz present")
try:
    from cd70.evaluate import evaluate_design
    r = evaluate_design()
    say(r["status"] == "ok" and 3.0 < r["f1_torque_wot_mean_nm"] < 7.0, f"model runs (mean WOT torque {r['f1_torque_wot_mean_nm']:.2f} Nm)")
except Exception as e:  # noqa: BLE001
    say(False, f"model run failed: {e}")
free = shutil.disk_usage(ROOT).free / 1e9
say(free > 10, f"free disk {free:.0f} GB (need 10+)")
print(f"cpu cores: {os.cpu_count()}  (workers used: min(6, cores-2); override with CD70_JOBS=n)")
print("ENV OK" if ok else "ENV NOT OK")
sys.exit(0 if ok else 1)
