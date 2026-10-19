"""Make all figures that the finished data allows.  python scripts/make_figures.py [--scale full]
Writes figures/*.png and figures/FIGURE_INDEX.md (one line per figure: what it shows, how to read it)."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd  # noqa: E402

import figlint  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import analysis, config  # noqa: E402
from cd70.objective import FUEL_KEY  # noqa: E402

SCALE = sys.argv[sys.argv.index("--scale") + 1] if "--scale" in sys.argv else "full"
PROC = ROOT / "data" / "processed" if SCALE == "full" else ROOT / "runs" / "smoke"
FIG = ROOT / "figures" if SCALE == "full" else ROOT / "runs" / "smoke" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#e87ba4"]
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.edgecolor": "#52514e",
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
                     "font.size": 9, "axes.prop_cycle": plt.cycler(color=C)})
index = []
missing = []


def save(fig, name, text):
    figlint.lint(fig, name)
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=170)
    plt.close(fig)
    index.append(f"- `{name}.png`: {text}")


def need(path, optional=False):
    p = PROC / path
    if not p.exists():
        if not optional:
            missing.append(str(path))
        return None
    return pd.read_parquet(p)


for T in "AB":
    # F01 calibration posteriors
    acc = need(f"accepted_{T}.parquet")
    if acc is not None and len(acc) > 5:
        spec = [d for d in config.priors()["uncertain"] if d["group"] == "CAL"]
        fig, ax = plt.subplots(3, 5, figsize=(11, 6))
        for a, d in zip(ax.ravel(), spec):
            lo, hi = (d["low"], d["high"]) if d["dist"] != "discrete" else (min(d["values"]), max(d["values"]))
            a.hist(acc[f"u_{d['name']}"], bins=12, range=(lo, hi), color=C[0], alpha=0.85)
            a.axhline(len(acc) / 12, color=C[1], lw=1)
            a.set_title(d["name"], fontsize=8)
            a.set_yticks([])
            a.set_xlabel("accepted value (input units)", fontsize=6)
            a.set_ylabel("count", fontsize=6)
        for a in ax.ravel()[len(spec):]:
            a.axis("off")
        save(fig, f"f01_posteriors_timing{T}", f"Accepted calibration values (blue) vs flat prior (orange line), timing {T}. A bar pattern far from flat means the published numbers pin that parameter down.")
    # F02 baseline curves band
    bc = need(f"baseline_curves_{T}.parquet")
    if bc is not None:
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        for a, y, lab in ((ax[0], "torque_nm", "Torque (Nm)"), (ax[1], "power_hp", "Power (hp)")):
            g = bc.groupby("rpm")[y]
            a.fill_between(g.median().index, g.quantile(0.05), g.quantile(0.95), color=C[0], alpha=0.25, label="90% of calibrated engines")
            a.plot(g.median().index, g.median(), color=C[0], label="median")
            a.set_xlabel("engine speed (rpm)")
            a.set_ylabel(lab)
        ax[1].plot([7500], [5.05], "o", color=C[1], label="published 5.05 hp")
        ax[0].plot([5500], [5.0], "o", color=C[1], label="published 5.0 Nm")
        ax[0].legend(frameon=False)
        ax[1].legend(frameon=False)
        save(fig, f"f02_baseline_curves_timing{T}", f"Full-throttle torque and power of the calibrated baseline ensemble, timing {T}. Orange dots are the two published numbers used for calibration.")
    # F03 OFAT tornado
    ofd = PROC / f"ofat_{T}"
    if ofd.exists():
        from cd70.runner import load_parts
        df = load_parts(ofd)
        b = df[df["var"] == "baseline"].iloc[0]
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        for a, y, lab in ((ax[0], "f1_torque_wot_mean_nm", "mean WOT torque change (%)"), (ax[1], FUEL_KEY, "city fuel use change (%)")):
            vs = []
            for v in config.design_names():
                lo_ = df[(df["var"] == v) & (df["side"] == "low")][y].iloc[0] / b[y] * 100 - 100
                hi_ = df[(df["var"] == v) & (df["side"] == "high")][y].iloc[0] / b[y] * 100 - 100
                vs.append((v, lo_, hi_))
            vs.sort(key=lambda t: max(abs(t[1]), abs(t[2])))
            for i, (v, lo_, hi_) in enumerate(vs):
                a.barh(i, lo_, color=C[0])
                a.barh(i, hi_, color=C[1])
            a.set_yticks(range(len(vs)))
            a.set_yticklabels([t[0] for t in vs])
            a.set_xlabel(lab)
            a.set_ylabel("tuning variable")
            a.axvline(0, color="#52514e", lw=0.8)
        save(fig, f"f03_ofat_tornado_timing{T}", f"One-variable-at-a-time effect of each tuning variable at its low bound (blue) and high bound (orange) on the nominal engine, timing {T}. For fuel use, negative is better.")
    # F04/F05 Morris and Sobol
    mo = need(f"morris_result_{T}.parquet")
    if mo is not None:
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        for a, y in zip(ax, ("f1_torque_wot_mean_nm", FUEL_KEY)):
            d = mo[mo["y"] == y]
            a.scatter(d["mu_star"], d["sigma"], color=C[0])
            for _, r in d.iterrows():
                a.annotate(r["var"], (r["mu_star"], r["sigma"]), fontsize=7)
            a.set_xlabel("mu* (overall influence)")
            a.set_ylabel("sigma (interaction / nonlinearity)")
            a.set_title(y, fontsize=8)
        save(fig, f"f04_morris_timing{T}", f"Morris screening, timing {T}. Far right = strong influence; high above the diagonal = interacts with other variables.")
    so = need(f"sobol_result_{T}.parquet")
    if so is not None:
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        for a, y in zip(ax, ("f1_torque_wot_mean_nm", FUEL_KEY)):
            d = so[so["y"] == y]
            x = np.arange(len(d))
            a.bar(x - 0.2, d["S1"], 0.4, yerr=d["S1_conf"], color=C[0], label="S1 (alone)")
            a.bar(x + 0.2, d["ST"], 0.4, yerr=d["ST_conf"], color=C[1], label="ST (with interactions)")
            a.set_xticks(x)
            a.set_xticklabels(d["var"], rotation=60, ha="right", fontsize=7)
            a.set_title(y, fontsize=8)
            a.set_xlabel("tuning variable")
            a.set_ylabel("variance share (Sobol index)")
        ax[0].legend(frameon=False)
        save(fig, f"f05_sobol_timing{T}", f"Sobol variance shares of the tuning variables, timing {T}. ST much larger than S1 means interactions matter.")
    for cls in "ABC":
        # F06 pareto (twin) + F07 HV convergence
        files = sorted((PROC / "opt").glob(f"{T}_{cls}_*_*.parquet")) if (PROC / "opt").exists() else []
        if files:
            df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
            fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
            for k, m in enumerate(("nsga2", "tpe", "random")):
                d = df[(df["method"] == m) & (df["feasible"] == 1.0)]
                if len(d):
                    pm = analysis.pareto_mask(d[["o1", "o2"]].to_numpy())
                    ax[0].scatter(-d[pm]["o1"] * 100 - 100, d[pm]["o2"] * 100 - 100, s=10, color=C[k], label=m)
                curves = []
                for sd, g in df[df["method"] == m].groupby("seed"):
                    hv = analysis.hv_curve(g[["o1", "o2"]].to_numpy(), g["feasible"].to_numpy(), step=max(20, len(g) // 40))
                    if hv:
                        curves.append(hv)
                if curves:
                    n = min(len(c) for c in curves)
                    xs = [c[0] for c in curves[0][:n]]
                    ys = np.mean([[v for _, v in c[:n]] for c in curves], axis=0)
                    ax[1].plot(xs, ys, color=C[k], label=m)
            ax[0].plot([0], [0], "k*", label="baseline")
            ax[0].set_xlabel("torque change (%)")
            ax[0].set_ylabel("city fuel use change (%)  (negative = better)")
            ax[0].legend(frameon=False)
            ax[1].set_xlabel("evaluations")
            ax[1].set_ylabel("hypervolume")
            ax[1].legend(frameon=False)
            save(fig, f"f06_pareto_hv_timing{T}_class{cls}", f"Hardware class {cls}, timing {T}: best trade-offs found on the nominal engine by each optimiser (left) and hypervolume vs evaluations (right). Random search being close to NSGA-II/TPE means the problem is easy.")
        # F08 robust front
        rf = sorted((PROC / "optrob").glob(f"{T}_{cls}_*.parquet")) if (PROC / "optrob").exists() else []
        if rf:
            df = pd.concat([pd.read_parquet(f) for f in rf], ignore_index=True)
            d = df[df["feasible"] == 1.0]
            fig, ax = plt.subplots(figsize=(4.5, 3.6))
            ax.scatter(-d["o1"] * 100 - 100, d["o2"] * 100 - 100, s=8, color=C[0], alpha=0.4, label="feasible on ensemble")
            if len(d):
                pm = analysis.pareto_mask(d[["o1", "o2"]].to_numpy())
                ax.scatter(-d[pm]["o1"] * 100 - 100, d[pm]["o2"] * 100 - 100, s=16, color=C[1], label="Pareto")
            ax.plot([0], [0], "k*")
            ax.set_xlabel("mean torque change (%)")
            ax.set_ylabel("mean fuel change (%)")
            ax.legend(frameon=False)
            save(fig, f"f08_robust_front_timing{T}_class{cls}", f"Ensemble-robust optimisation, class {cls}, timing {T}: mean gains over the calibrated engine ensemble with constraints enforced on 80th-percentile knock, worst pressure and rule violations.")
        for which in ("econ", "power", "knee"):
            pr = need(f"paired_{T}_{cls}_{which}.parquet", True)
            if pr is not None:
                fig, ax = plt.subplots(1, 2, figsize=(8, 3.4))
                for a, y, lab in ((ax[0], "torque_gain_pct", "torque gain (%)"), (ax[1], "fuel_gain_pct", "fuel saving (%)")):
                    a.hist(pr[y].dropna(), bins=20, color=C[0])
                    a.axvline(0, color="#52514e", lw=1)
                    a.set_xlabel(lab)
                    a.set_ylabel("number of calibrated engines")
                    a.set_title(analysis.claim_level(pr[y].to_numpy()), fontsize=8)
                save(fig, f"f09_paired_timing{T}_class{cls}_{which}", f"Paired gains of the '{which}' design over baseline across calibrated engines, class {cls}, timing {T}. Title = claim level from docs/CLAIM_RULES.md.")
            vo = need(f"voi_{T}_{cls}_{which}.parquet", True)
            if vo is not None and len(vo):
                fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
                for a, y in zip(ax, ("torque_gain_pct", "fuel_gain_pct")):
                    d = vo[vo["y"] == y].sort_values("perm_importance").tail(10)
                    a.barh(d["var"], d["perm_importance"], color=C[0])
                    a.set_title(y, fontsize=8)
                    a.set_xlabel("permutation importance (drop in R2)")
                    a.set_ylabel("uncertain engine property")
                save(fig, f"f11_voi_timing{T}_class{cls}_{which}", f"Which uncertain engine properties decide how big the gain is (random-forest permutation importance), class {cls}, timing {T}. The top bars are the things worth measuring on a real engine.")
    # F10 scenario heat map
    for d in sorted(PROC.glob(f"grid_{T}_*")):
        from cd70.runner import load_parts
        g = load_parts(d)
        if g.empty:
            continue
        b = g[g["arm"] == "base"].set_index(["s_ron", "s_t_amb_c", "s_alt_m", "member"])
        x = g[g["arm"] == "design"].set_index(["s_ron", "s_t_amb_c", "s_alt_m", "member"])
        fuel = (1 - x[FUEL_KEY] / b[FUEL_KEY]) * 100
        tq = (x["f1_torque_wot_mean_nm"] / b["f1_torque_wot_mean_nm"] - 1) * 100
        feas = x["feasible"]
        res = pd.DataFrame({"fuel": fuel, "tq": tq, "feas": feas}).groupby(level=[0, 1, 2]).mean().reset_index()
        fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
        for a, y, lab in zip(ax, ("tq", "fuel", "feas"), ("torque gain (%)", "fuel saving (%)", "fraction feasible")):
            p = res.pivot_table(index=["s_ron", "s_alt_m"], columns="s_t_amb_c", values=y)
            im = a.imshow(p.to_numpy(), aspect="auto", cmap="Blues")
            a.set_xticks(range(p.shape[1]))
            a.set_xticklabels(p.columns)
            a.set_yticks(range(p.shape[0]))
            a.set_yticklabels([f"RON{int(i[0])} {int(i[1])}m" for i in p.index])
            a.set_title(lab, fontsize=8)
            for (i, j), v in np.ndenumerate(p.to_numpy()):
                a.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7)
            a.set_xlabel("ambient temperature (C)")
            a.set_ylabel("fuel octane, altitude")
        save(fig, f"f10_scenarios_{d.name}", f"Gains of the design across fuel octane, altitude and temperature ({d.name}). Cells show the mean over engines; low 'fraction feasible' marks conditions where the tune breaks a constraint (usually knock).")

_old = (FIG / "FIGURE_INDEX.md").read_text(encoding="utf-8").splitlines() if (FIG / "FIGURE_INDEX.md").exists() else []
index += [x for x in _old if x.startswith("- `f12_") or x.startswith("- `f13_") or x.startswith("- `f14_") or x.startswith("- `f15_")]
(FIG / "FIGURE_INDEX.md").write_text("# Figure index\n\n" + "\n".join(sorted(set(index))) + ("\n\n## Not made (data missing)\n" + "\n".join(f"- {m}" for m in sorted(set(missing))) if missing else "") + "\n", encoding="utf-8")
print(f"{len(index)} figures made, {len(set(missing))} inputs missing")
