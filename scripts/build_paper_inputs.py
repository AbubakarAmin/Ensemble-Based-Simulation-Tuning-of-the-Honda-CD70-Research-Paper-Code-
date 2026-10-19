"""Collect every number, table and figure the paper writer needs into paper_inputs/.
python scripts/build_paper_inputs.py     (re-run any time; it only reads results, never invents)"""
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import analysis, config, rules  # noqa: E402
from cd70.runner import load_parts  # noqa: E402

PROC = ROOT / "data" / "processed"
OUT = ROOT / "paper_inputs"
(OUT / "tables").mkdir(parents=True, exist_ok=True)
facts: dict = {"built": pd.Timestamp.now().isoformat(timespec="minutes")}


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None


facts["feasibility"] = jload(ROOT / "reports" / "feasibility_report.json")
for T in "AB":
    f = {"calibration": jload(PROC / f"cal_summary_{T}.json"), "twin": jload(PROC / f"twin_{T}.json")}
    bc = PROC / f"baseline_curves_{T}.parquet"
    if bc.exists():
        d = pd.read_parquet(bc)
        rows = []
        for rpm, g in d.groupby("rpm"):
            row = {"rpm": rpm}
            for k in ("torque_nm", "power_hp", "bsfc", "ve", "ki", "pmax_bar"):
                for q, v in (("p05", .05), ("p50", .5), ("p95", .95)):
                    row[f"{k}_{q}"] = float(g[k].quantile(v))
            rows.append(row)
        pd.DataFrame(rows).to_csv(OUT / "tables" / f"baseline_curves_{T}.csv", index=False)
        f["baseline_curve_csv"] = f"tables/baseline_curves_{T}.csv"
    for nm in ("morris", "sobol"):
        p = PROC / f"{nm}_result_{T}.parquet"
        if p.exists():
            pd.read_parquet(p).to_csv(OUT / "tables" / f"{nm}_{T}.csv", index=False)
    of = PROC / f"ofat_{T}"
    if of.exists():
        load_parts(of).to_csv(OUT / "tables" / f"ofat_{T}.csv", index=False)
    f["hv"] = {}
    for cls in "ABC":
        fl = sorted((PROC / "opt").glob(f"{T}_{cls}_*_*.parquet")) if (PROC / "opt").exists() else []
        if fl:
            df = pd.concat([pd.read_parquet(x) for x in fl])
            res = {}
            for m, g in df.groupby("method"):
                hv = [analysis.hypervolume(s[s["feasible"] == 1.0][["o1", "o2"]].to_numpy()) for _, s in g.groupby("seed")]
                res[m] = {"hv_mean": float(np.mean(hv)), "hv_per_seed": [float(h) for h in hv],
                          "feasible_fraction": float(g["feasible"].mean())}
            f["hv"][cls] = res
            fr = df[df["feasible"] == 1.0]
            if len(fr):
                front = fr[analysis.pareto_mask(fr[["o1", "o2"]].to_numpy())].sort_values("o1")
                front.to_csv(OUT / "tables" / f"pareto_twin_{T}_{cls}.csv", index=False)
        pk = jload(PROC / f"picked_{T}_{cls}.json")
        if pk:
            f.setdefault("picked", {})[cls] = pk
        for which in ("econ", "power", "knee"):
            pp = PROC / f"paired_{T}_{cls}_{which}.parquet"
            if not pp.exists():
                continue
            d = pd.read_parquet(pp)
            feas = float(d["feasible_des"].mean())
            ent = {"members": int(len(d)), "feasible_fraction_design": feas,
                   "feasible_fraction_base": float(d["feasible_base"].mean())}
            for y in ("torque_gain_pct", "fuel_gain_pct", "power_gain_pct"):
                med, lo, hi = analysis.bootstrap_ci(d[y].to_numpy())
                ent[y] = {"median": med, "ci95": [lo, hi], "fraction_positive": float(np.mean(d[y] > 0))}
            cl = {}
            for y in ("torque_gain_pct", "fuel_gain_pct"):
                c = analysis.claim_level(d[y].to_numpy())
                cl[y] = c if feas >= 0.9 else f"NOT SUPPORTED (design breaks a constraint on {100 * (1 - feas):.0f}% of engines)"
            ent["claims"] = cl
            f.setdefault("paired", {}).setdefault(cls, {})[which] = ent
            d.to_csv(OUT / "tables" / f"paired_{T}_{cls}_{which}.csv", index=False)
            vp = PROC / f"voi_{T}_{cls}_{which}.parquet"
            if vp.exists():
                v = pd.read_parquet(vp)
                v.to_csv(OUT / "tables" / f"voi_{T}_{cls}_{which}.csv", index=False)
                ent["voi_top"] = {y: v[v["y"] == y].sort_values("perm_importance", ascending=False).head(5)["var"].tolist()
                                  for y in v["y"].unique()}
    facts[f"timing_{T}"] = f
(OUT / "RESULTS_FACTS.json").write_text(json.dumps(facts, indent=1, default=float), encoding="utf-8")

pri = config.priors()
md = ["# Methods facts (generated from config files)", "", f"Python {platform.python_version()}. See requirements.txt for package versions.", "",
      "## Uncertain inputs (priors)", "", "| name | group | tag | distribution | low | high | nominal |", "|---|---|---|---|---|---|---|"]
for d in pri["uncertain"]:
    lo, hi = (d.get("low"), d.get("high")) if d["dist"] != "discrete" else (d["values"], "")
    md.append(f"| {d['name']} | {d['group']} | {d['tag']} | {d['dist']} | {lo} | {hi} | {d['nominal']} |")
md += ["", "## Design variables", "", "| name | low | high | baseline | integer | first hardware class |", "|---|---|---|---|---|---|"]
md += [f"| {d['name']} | {d['low']} | {d['high']} | {d['baseline']} | {d['integer']} | {d['hardware']} |" for d in pri["design"]]
md += ["", "## Design rules and plausibility limits", "", "| rule | kind | limit | tag | meaning |", "|---|---|---|---|---|"]
for nm, lim in list(rules.DESIGN_LIMITS.items()) + list(rules.RESULT_LIMITS.items()):
    md.append(f"| {nm} | {lim[0]} | {lim[1]} | {lim[2]} | {lim[3]} |")
md += ["", "## Calibration", "", "```yaml", (ROOT / "config" / "calibration.yaml").read_text(encoding="utf-8"), "```", "",
       "## Seeds", "", "```yaml", (ROOT / "config" / "seeds.yaml").read_text(encoding="utf-8"), "```"]
(OUT / "METHODS_FACTS.md").write_text("\n".join(md), encoding="utf-8")
print("paper_inputs built:", sorted(p.name for p in OUT.iterdir()))
