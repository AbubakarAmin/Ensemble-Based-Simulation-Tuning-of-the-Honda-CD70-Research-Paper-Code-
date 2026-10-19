"""Audit stored results.  python scripts/audit.py
1) re-evaluates 12 stored rows from scratch and compares (reproducibility), 2) checks no NaN in key columns,
3) checks every stored 'feasible' design still satisfies design rules. Writes reports/audit.md. Exit 1 on any failure."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import config, rules, study  # noqa: E402
from cd70.objective import FUEL_KEY  # noqa: E402
from cd70.runner import load_parts  # noqa: E402

PROC = ROOT / "data" / "processed"
lines, bad = ["# Audit", ""], 0
dirs = sorted(d for d in PROC.glob("robust_*") if d.is_dir())
if not dirs:
    print("no robust_* results to audit")
    sys.exit(1)
rng = np.random.default_rng(12345)
for d in dirs:
    df = load_parts(d)
    ok = df[df["status"] == "ok"]
    lines.append(f"## {d.name}: {len(df)} rows, {len(df) - len(ok)} errors")
    if len(df) - len(ok):
        bad += 1
    samp = ok.iloc[rng.choice(len(ok), min(12, len(ok)), replace=False)]
    diffs = []
    for _, r in samp.iterrows():
        again = study.eval_checked({k: v for k, v in r.items() if k.startswith(("u_", "d_", "s_")) or k == "timing"})
        diffs.append(abs(again["f1_torque_wot_mean_nm"] - r["f1_torque_wot_mean_nm"]) / r["f1_torque_wot_mean_nm"])
        diffs.append(abs(again[FUEL_KEY] - r[FUEL_KEY]) / r[FUEL_KEY])
    mx = float(np.max(diffs))
    lines.append(f"- max relative difference on re-evaluation: {mx:.2e} (must be < 1e-6)")
    bad += mx > 1e-6
    for c in ("f1_torque_wot_mean_nm", FUEL_KEY, "ki_max"):
        n = int(ok[c].isna().sum())
        lines.append(f"- NaN in {c}: {n}")
    des = ok[ok["arm"] == "design"].iloc[0]
    dd = {k[2:]: v for k, v in des.items() if k.startswith("d_")}
    rr = rules.design_rules(None, dd, str(des["timing"]))
    lines.append(f"- design rule check of the design: {'ok' if rules.all_ok(rr) else 'FAILED ' + str(rules.failed(rr))}")
    bad += not rules.all_ok(rr)
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "audit.md").write_text("\n".join(lines) + f"\n\nRESULT: {'FAIL' if bad else 'PASS'}\n", encoding="utf-8")
print("\n".join(lines))
print("AUDIT", "FAIL" if bad else "PASS")
del pd, config
sys.exit(1 if bad else 0)
