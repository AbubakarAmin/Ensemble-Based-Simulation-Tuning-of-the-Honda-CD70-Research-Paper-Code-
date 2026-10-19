"""Automatic red-team checks on the finished results.  python scripts/red_team.py  -> reports/red_team.md
Each flag says what a hostile reviewer would attack. The agent copies every FLAG into FINAL_HANDOFF (finish_research.py does it)."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import config  # noqa: E402

PROC = ROOT / "data" / "processed"
F = json.loads((ROOT / "paper_inputs" / "RESULTS_FACTS.json").read_text(encoding="utf-8"))
flags = []
for T in "AB":
    t = F.get(f"timing_{T}", {})
    cal = t.get("calibration") or {}
    if cal and cal.get("accepted", 0) < 100:
        flags.append(f"timing {T}: only {cal.get('accepted')} calibrated engines (<100): the ensemble is thin, confidence intervals are wide.")
    if cal and cal.get("acceptance_rate", 1) < 0.01:
        flags.append(f"timing {T}: acceptance rate {cal['acceptance_rate']:.4f}: the published numbers are hard to reach, the model sits at the edge of its range.")
    for cls, hv in (t.get("hv") or {}).items():
        if "random" in hv and "nsga2" in hv and hv["random"]["hv_mean"] > 0.97 * hv["nsga2"]["hv_mean"]:
            flags.append(f"timing {T} class {cls}: random search reaches 97% of NSGA-II hypervolume: the optimisation problem is easy, say so (no algorithmic novelty claim).")
    for cls, pk in (t.get("paired") or {}).items():
        for which, e in pk.items():
            if e["feasible_fraction_design"] < 0.9:
                flags.append(f"timing {T} class {cls} {which}: design infeasible on {100 * (1 - e['feasible_fraction_design']):.0f}% of engines: NOT a robust design.")
            for y, c in e["claims"].items():
                if not c.startswith("CLAIM"):
                    flags.append(f"timing {T} class {cls} {which} {y}: claim level is '{c}', do not write it as a firm result.")
    for cls in "ABC":
        p = PROC / "opt"
        if not p.exists():
            continue
        for fpath in sorted(p.glob(f"{T}_{cls}_nsga2_*.parquet"))[:1]:
            d = pd.read_parquet(fpath)
            d = d[d["feasible"] == 1.0]
            if d.empty:
                continue
            sp = {x["name"]: x for x in config.priors()["design"]}
            hit = [n for n in config.hardware_class(cls) if (d[f"d_{n}"].max() >= sp[n]["high"] - 1e-6 * abs(sp[n]["high"]) - 1e-9) or (d[f"d_{n}"].min() <= sp[n]["low"] + 1e-9)]
            if hit:
                flags.append(f"timing {T} class {cls}: optimiser touches the bound of {hit}: the true optimum may lie beyond the allowed hardware range; report as 'bound-limited'.")
a, b = F.get("timing_A", {}).get("paired", {}), F.get("timing_B", {}).get("paired", {})
for cls in set(a) & set(b):
    for w in set(a[cls]) & set(b[cls]):
        sa, sb = a[cls][w]["fuel_gain_pct"]["median"], b[cls][w]["fuel_gain_pct"]["median"]
        if sa * sb < 0:
            flags.append(f"class {cls} {w}: fuel gain has OPPOSITE sign under valve timing A ({sa:.2f}%) and B ({sb:.2f}%): result depends on an unresolved spec ambiguity.")
flags.append("ALWAYS: no real CD70 was measured. All gains are model predictions conditional on the calibration targets (two MEDIUM published numbers and one WSM number).")
flags.append("ALWAYS: friction (Chen-Flynn coefficients), exhaust temperature, plenum volumes and knock constants are assumed, not measured.")
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "red_team.md").write_text("# Red-team flags\n\n" + "\n".join(f"- FLAG: {x}" for x in flags) + "\n", encoding="utf-8")
print("\n".join(f"FLAG: {x}" for x in flags))
