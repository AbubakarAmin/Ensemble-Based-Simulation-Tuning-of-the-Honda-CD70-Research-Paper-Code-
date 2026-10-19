"""Write FINAL_HANDOFF.md (the file the user gives to a smart model to write the paper).  python scripts/finish_research.py"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F = json.loads((ROOT / "paper_inputs" / "RESULTS_FACTS.json").read_text(encoding="utf-8"))


def rd(p):
    q = ROOT / p
    return q.read_text(encoding="utf-8") if q.exists() else f"(missing: {p})"


st = json.loads((ROOT / "state" / "STATE.json").read_text(encoding="utf-8"))
blocked = {k: v for k, v in st["tasks"].items() if v["status"] == "blocked"}
out = ["# FINAL HANDOFF: CD70 simulation-based tuning study", "",
       "Give this whole file plus the folders `paper_inputs/`, `figures/`, `reports/` and `docs/spec_sheet_v11.md` to the paper-writing model.", "",
       "## What was done", "", "Physics-based single-cylinder engine model (see docs/MODEL_SPEC.md), calibrated against published power, torque and "
       "cranking pressure by Bayesian rejection into an ensemble of plausible engines; every candidate passes physics and hardware design rules; "
       "tuning variables explored by screening, Sobol analysis, three optimisers, an ensemble-robust optimiser; designs judged by paired comparison "
       "on the same engines with claim rules (docs/CLAIM_RULES.md).", "",
       "## Feasibility verdict", "", f"**{(F.get('feasibility') or {}).get('verdict', 'missing')}**. Details: reports/feasibility_report.md", "",
       "## Key results (machine-collected, do not retype numbers: read paper_inputs/RESULTS_FACTS.json)", ""]
for T in "AB":
    t = F.get(f"timing_{T}") or {}
    c = t.get("calibration") or {}
    out.append(f"### Valve timing reading {T}")
    out.append(f"- calibrated engines: {c.get('accepted')} of {c.get('draws')} draws (acceptance {c.get('acceptance_rate')})")
    for cls, pk in (t.get("paired") or {}).items():
        for w, e in pk.items():
            out.append(f"- class {cls} design '{w}': torque {e['torque_gain_pct']['median']:+.2f}% (95% CI {e['torque_gain_pct']['ci95'][0]:+.2f}..{e['torque_gain_pct']['ci95'][1]:+.2f}), "
                       f"fuel saving {e['fuel_gain_pct']['median']:+.2f}% (CI {e['fuel_gain_pct']['ci95'][0]:+.2f}..{e['fuel_gain_pct']['ci95'][1]:+.2f}); "
                       f"feasible on {100 * e['feasible_fraction_design']:.0f}% of engines; claims: {e['claims']}")
out += ["", "## Red-team flags (must appear in the paper's limitations)", "", rd("reports/red_team.md"), "",
        "## Holdout validation", "", rd("reports/holdout_validation.md"), "",
        "## Blocked or skipped tasks", "", json.dumps(blocked, indent=1) if blocked else "none", "",
        "## Open items", "", rd("OPEN_ITEMS.md"), "", "## Decisions taken", "", rd("DECISIONS.md"), "",
        "## Figures", "", rd("figures/FIGURE_INDEX.md"), "", "## Where everything is", "",
        "- paper_inputs/RESULTS_FACTS.json, METHODS_FACTS.md, tables/*.csv", "- figures/*.png", "- reports/*.md", "- docs/MODEL_SPEC.md (model equations), docs/ANALYSIS_SPEC.md, docs/CLAIM_RULES.md, docs/LIMITATIONS.md",
        "- data/processed/ (all raw numbers, parquet)", "- JOURNAL.md (what happened, in order)"]
(ROOT / "FINAL_HANDOFF.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("FINAL_HANDOFF.md written")
subprocess.run([sys.executable, "scripts/health.py", "--quick"], cwd=ROOT)
