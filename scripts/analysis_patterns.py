"""Pattern analysis of the calibrated ensemble (what the data says about the engine itself).
python scripts/analysis_patterns.py
For each timing: posterior-vs-prior shrinkage table, strongest correlations between inputs, PCA, correlation heatmap."""
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
from cd70 import config  # noqa: E402

PROC = ROOT / "data" / "processed"
(ROOT / "paper_inputs" / "tables").mkdir(parents=True, exist_ok=True)
(ROOT / "figures").mkdir(exist_ok=True)
pri = {d["name"]: d for d in config.priors()["uncertain"]}
idx = []
for T in "AB":
    f = PROC / f"accepted_{T}.parquet"
    if not f.exists():
        continue
    acc = pd.read_parquet(f)
    cols = [f"u_{n}" for n in pri if f"u_{n}" in acc.columns and acc[f"u_{n}"].nunique() > 1]
    X = acc[cols]
    rows = []
    for c in cols:
        d = pri[c[2:]]
        if "low" in d:
            pstd = (d["high"] - d["low"]) / np.sqrt(12.0)
            rows.append(dict(input=c[2:], prior_low=d["low"], prior_high=d["high"], post_mean=X[c].mean(), post_p05=X[c].quantile(.05),
                             post_p95=X[c].quantile(.95), sd_ratio_post_to_prior=float(X[c].std() / pstd)))
    pd.DataFrame(rows).sort_values("sd_ratio_post_to_prior").to_csv(ROOT / "paper_inputs" / "tables" / f"posterior_shrinkage_{T}.csv", index=False)
    corr = X.corr(method="spearman")
    pairs = [(corr.index[i][2:], corr.columns[j][2:], float(corr.iloc[i, j])) for i in range(len(cols)) for j in range(i + 1, len(cols))]
    top = pd.DataFrame(sorted(pairs, key=lambda p: -abs(p[2]))[:20], columns=["input_1", "input_2", "spearman"])
    top.to_csv(ROOT / "paper_inputs" / "tables" / f"posterior_top_correlations_{T}.csv", index=False)
    Z = (X - X.mean()) / X.std().replace(0, 1)
    ev = np.linalg.svd(Z.to_numpy(), compute_uv=False) ** 2
    ev = ev / ev.sum()
    pd.DataFrame({"component": np.arange(1, len(ev) + 1), "explained_variance": ev}).to_csv(ROOT / "paper_inputs" / "tables" / f"posterior_pca_{T}.csv", index=False)
    fig, axs = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [2.2, 1]})
    im = axs[0].imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    axs[0].set_xticks(range(len(cols)))
    axs[0].set_yticks(range(len(cols)))
    axs[0].set_xticklabels([c[2:] for c in cols], rotation=90, fontsize=5)
    axs[0].set_yticklabels([c[2:] for c in cols], fontsize=5)
    axs[0].grid(False)
    axs[0].set_xlabel("uncertain input")
    axs[0].set_ylabel("uncertain input")
    fig.colorbar(im, ax=axs[0], shrink=0.7)
    axs[0].set_title(f"Spearman correlation of accepted inputs, timing {T}", fontsize=8)
    axs[1].bar(range(1, min(10, len(ev)) + 1), ev[:10])
    axs[1].set(xlabel="principal component", ylabel="explained variance", title="PCA of accepted ensemble")
    figlint.lint(fig, 'f12')
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / f"f12_posterior_patterns_timing{T}.png", dpi=170)
    plt.close(fig)
    idx.append(f"- `f12_posterior_patterns_timing{T}.png`: which uncertain inputs the calibration data constrain together (left, rank correlation among accepted engines) and how many independent directions remain (right, PCA), timing {T}.")
fi = ROOT / "figures" / "FIGURE_INDEX.md"
old = fi.read_text(encoding="utf-8") if fi.exists() else ""
old = "\n".join(x for x in old.splitlines() if "f12_posterior_patterns" not in x)
fi.write_text(old.rstrip("\n") + "\n" + "\n".join(idx) + "\n", encoding="utf-8")
print("patterns done for", len(idx), "timings")
