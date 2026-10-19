"""Compare the calibrated baseline with independent published numbers NOT used in calibration.
python scripts/validate_holdout.py --kmpl 60 --source URL [--kmpl 70 --source URL2]
Predicts km/l at steady 40 and 50 km/h (4th gear) for 60 calibrated engines (timing B). Writes reports/holdout_validation.md.
Order of magnitude agreement (within a factor 1.6) is all that can be claimed; owner-reported mileage includes traffic and wind."""
import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import experiments as E  # noqa: E402
from cd70 import (
    study,  # noqa: E402
)

ap = argparse.ArgumentParser()
ap.add_argument("--kmpl", type=float, action="append", default=[])
ap.add_argument("--source", action="append", default=[])
ap.add_argument("--timing", default="B")
a = ap.parse_args()
members = E.load_members(a.timing, 60, "full")
k40, k50 = [], []
for u in members:
    r = study.eval_checked(study.flat_row(unc=u, timing=a.timing))
    k40.append(100.0 / r["l100_40"])
    k50.append(100.0 / r["l100_50"])
lines = ["# Holdout validation (not used in calibration)", "",
         f"Predicted steady-speed mileage, 4th gear, timing {a.timing}, 60 calibrated engines (5th/50th/95th percentile):",
         f"- 40 km/h: {np.percentile(k40, 5):.0f} / {np.percentile(k40, 50):.0f} / {np.percentile(k40, 95):.0f} km/l",
         f"- 50 km/h: {np.percentile(k50, 5):.0f} / {np.percentile(k50, 50):.0f} / {np.percentile(k50, 95):.0f} km/l", ""]
if not a.kmpl:
    lines.append("No independent mileage numbers were found. STATUS: NO HOLDOUT DATA. The model is validated only by physics tests and calibration targets.")
else:
    med = float(np.median(k50))
    for v, s in zip(a.kmpl, a.source + [""] * len(a.kmpl)):
        ratio = med / v
        lines.append(f"- published {v} km/l ({s}): model/published = {ratio:.2f} -> {'agrees within 1.6x' if 1 / 1.6 <= ratio <= 1.6 else 'DOES NOT AGREE (model too ' + ('optimistic' if ratio > 1 else 'pessimistic') + ')'}")
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "holdout_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
