"""Head-to-head comparison of every picked design against the baseline engine on the SAME calibrated engines.
python scripts/compare_baseline.py --timing B [--members 60]   (run as a job; resumable)
Writes data/processed/compare_<T>.parquet, paper_inputs/tables/compare_<T>.csv, figures/f13..f15 (baseline vs designs)."""
import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import figlint  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import (  # noqa: E402
    analysis,
    config,
    study,  # noqa: E402
)
from cd70 import experiments as E  # noqa: E402
from cd70.objective import FUEL_KEY  # noqa: E402
from cd70.runner import run_batch  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--timing", default="B")
ap.add_argument("--members", type=int, default=60)
a = ap.parse_args()
T = a.timing
PROC = ROOT / "data" / "processed"
members = E.load_members(T, a.members, "full")
base_d = config.baseline_design()
labels = {"baseline": base_d}
for cls in "ABC":
    f = PROC / f"picked_{T}_{cls}.json"
    if f.exists():
        for which, d in json.loads(f.read_text(encoding="utf-8")).items():
            labels[f"class{cls}_{which}"] = {**base_d, **d}
rows = []
for lab, d in labels.items():
    for k, u in enumerate(members):
        r = study.flat_row(unc=u, design=d, timing=T)
        r["label"], r["member"] = lab, k
        rows.append(r)
df = run_batch("cd70.study:eval_checked", rows, PROC / f"compare_{T}", chunk=60, n_jobs=E._jobs("full"))
keep = ["label", "member", "feasible", "f1_torque_wot_mean_nm", FUEL_KEY, "t_3000_nm", "t_4000_nm", "t_5000_nm", "t_5500_nm",
        "t_7500_nm", "p_7500_hp", "p_peak_kw", "l100_30", "l100_40", "l100_50", "v_top_kmh", "t_0_60_s", "ki_max", "p_cyl_max_bar", "bsfc_min_gkwh"]
df = df[[c for c in keep if c in df.columns]]
df.to_parquet(PROC / f"compare_{T}.parquet", index=False)
(ROOT / "paper_inputs" / "tables").mkdir(parents=True, exist_ok=True)
(ROOT / "figures").mkdir(exist_ok=True)
base = df[df.label == "baseline"].set_index("member")
metrics = [c for c in keep[3:] if c in df.columns]
recs = []
for lab in labels:
    if lab == "baseline":
        continue
    d = df[df.label == lab].set_index("member")
    rec = {"design": lab, "feasible_fraction": float(d["feasible"].mean())}
    for m in metrics:
        ch = 100.0 * (d[m] / base[m] - 1.0)
        med, lo, hi = analysis.bootstrap_ci(ch.to_numpy(float))
        rec[f"{m}_change_pct_median"], rec[f"{m}_ci_lo"], rec[f"{m}_ci_hi"] = med, lo, hi
    recs.append(rec)
pd.DataFrame(recs).to_csv(ROOT / "paper_inputs" / "tables" / f"compare_{T}.csv", index=False)
abs_tbl = df.groupby("label")[metrics].median().reset_index()
abs_tbl.to_csv(ROOT / "paper_inputs" / "tables" / f"compare_absolute_{T}.csv", index=False)
cols = {"baseline": "#52514e"}
pal = ["#2a78d6", "#eb6834", "#1baf7a", "#e87ba4", "#6250d6", "#e34948", "#eda100", "#008300", "#9085e9"]
for i, lab in enumerate([x for x in labels if x != "baseline"]):
    cols[lab] = pal[i % len(pal)]
rp = [3000, 4000, 5000, 5500, 7500]
fig, ax = plt.subplots(figsize=(7, 4.2))
for lab in labels:
    d = df[df.label == lab]
    q = np.array([[d[f"t_{r}_nm"].quantile(p) for r in rp] for p in (0.05, 0.5, 0.95)])
    ax.plot(rp, q[1], "-o", color=cols[lab], lw=2.4 if lab == "baseline" else 1.4, label=lab)
    if lab == "baseline":
        ax.fill_between(rp, q[0], q[2], color=cols[lab], alpha=0.18)
ax.set(xlabel="engine speed (rpm)", ylabel="WOT torque (Nm), median over engines", title=f"Torque: baseline (band = 5-95%) vs designs, timing {T}")
ax.legend(fontsize=6, ncol=2)
figlint.lint(fig, 'compare')
fig.tight_layout()
fig.savefig(ROOT / "figures" / f"f13_compare_torque_timing{T}.png", dpi=170)
plt.close(fig)
speeds = [30, 40, 50]
fig, ax = plt.subplots(figsize=(7, 4.2))
fig, (axc, ax) = plt.subplots(1, 2, figsize=(10, 3.8))
for j, lab in enumerate(labels):
    v = df[df.label == lab][FUEL_KEY]
    med = float(v.median())
    axc.bar(j, med, 0.6, yerr=[[med - float(v.quantile(0.25))], [float(v.quantile(0.75)) - med]], color=cols[lab], capsize=2)
axc.set_xticks(range(len(labels)))
axc.set_xticklabels([lab.replace("class", "c") for lab in labels], rotation=45, fontsize=6)
axc.set(ylabel="city-cycle fuel use (L/100 km), median and IQR", title=f"City-cycle fuel use (objective), timing {T}")
w = 0.8 / len(labels)
for j, lab in enumerate(labels):
    d = df[df.label == lab]
    md = [d[f"l100_{s}"].median() for s in speeds]
    lo = [md[i] - d[f"l100_{s}"].quantile(0.25) for i, s in enumerate(speeds)]
    hi = [d[f"l100_{s}"].quantile(0.75) - md[i] for i, s in enumerate(speeds)]
    ax.bar(np.arange(3) + j * w, md, w, yerr=[lo, hi], color=cols[lab], label=lab, capsize=1.5)
ax.set_xticks(np.arange(3) + 0.4 - w / 2)
ax.set_xticklabels([f"{s} km/h" for s in speeds])
ax.set(xlabel="steady cruising speed (km/h)", ylabel="fuel use (L/100 km, 4th gear), median and IQR",
       title=f"Steady-cruise fuel use (diagnostic), timing {T}")
ax.legend(fontsize=6, ncol=2)
figlint.lint(fig, 'compare')
fig.tight_layout()
fig.savefig(ROOT / "figures" / f"f14_compare_cruise_timing{T}.png", dpi=170)
plt.close(fig)
fig, axs = plt.subplots(1, 3, figsize=(10, 3.8))
for ax, (m, ttl) in zip(axs, (("f1_torque_wot_mean_nm", "mean WOT torque"), (FUEL_KEY, "mean city L/100 km"), ("v_top_kmh", "top speed"))):
    data, labs = [], []
    for lab in labels:
        if lab == "baseline":
            continue
        d = df[df.label == lab].set_index("member")
        data.append((100.0 * (d[m] / base[m] - 1.0)).dropna().to_numpy())
        labs.append(lab.replace("class", "c"))
    if data:
        ax.boxplot(data, orientation="horizontal", tick_labels=labs, showfliers=False)
    ax.axvline(0, color="#52514e", lw=1)
    ax.set_title(ttl + " change vs baseline (%)", fontsize=8)
    ax.tick_params(labelsize=6)
    ax.set_xlabel("change vs baseline (%)")
    ax.set_ylabel("tuned design")
fig.suptitle(f"Paired change over the same calibrated engines, timing {T}", fontsize=9)
figlint.lint(fig, 'compare')
fig.tight_layout()
fig.savefig(ROOT / "figures" / f"f15_compare_paired_timing{T}.png", dpi=170)
plt.close(fig)
idx = ROOT / "figures" / "FIGURE_INDEX.md"
add = [f"- `f13_compare_torque_timing{T}.png`: WOT torque at 5 speeds, baseline (grey, shaded 5-95% over calibrated engines) vs every picked design.",
       f"- `f14_compare_cruise_timing{T}.png`: left, city-cycle fuel use (the optimiser objective, see docs/ANALYSIS_SPEC.md); right, steady-cruise fuel use at 30/40/50 km/h (diagnostic). Baseline vs designs, median and IQR.",
       f"- `f15_compare_paired_timing{T}.png`: boxplots of the paired percentage change of torque, fuel use and top speed per design over the same engines."]
old = idx.read_text(encoding="utf-8") if idx.exists() else ""
old = "\n".join(x for x in old.splitlines() if "_compare_" not in x or f"timing{T}" not in x)
idx.write_text(old.rstrip("\n") + "\n" + "\n".join(add) + "\n", encoding="utf-8")
(ROOT / "state" / "stage_done").mkdir(parents=True, exist_ok=True)
(ROOT / "state" / "stage_done" / f"compare-{T}.done").write_text("ok", encoding="utf-8")
print("compare done", T, len(df), "rows")
