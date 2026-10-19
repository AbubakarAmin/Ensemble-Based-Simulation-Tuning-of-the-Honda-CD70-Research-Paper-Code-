"""Draw the study workflow diagram (no data needed).  python scripts/make_workflow_figure.py -> figures/f00_workflow.png"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "figures").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 56)
ax.axis("off")
C = {"in": "#cde2fb", "model": "#b7d3f6", "cal": "#fde3c8", "opt": "#c8efe0", "out": "#e8ddf7"}


def box(x, y, w, h, text, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=C[col], ec="#52514e", lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.4, color="#0b0b0b", wrap=True)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, lw=1, color="#52514e"))


box(1, 42, 20, 11, "Specification sheet\nsource-tagged values\n(official / manual / proxy)", "in")
box(26, 42, 20, 11, "38 uncertain inputs\n(prior ranges)\n8 tuning variables", "in")
box(51, 42, 21, 11, "Design rules and\nplausibility checks\n(physics, hardware)", "model")
box(77, 42, 22, 11, "Cycle model\n(0-D, crank-angle,\nverified by tests)", "model")
box(77, 25, 22, 11, "Sobol sampling of\ncandidate engines\n(32,768 per round)", "cal")
box(51, 25, 21, 11, "Rejection calibration:\npower, torque, cranking,\ntop speed, plausibility", "cal")
box(26, 25, 20, 11, "Ensemble of accepted\nengines + nominal\nengine", "cal")
box(1, 25, 20, 11, "Validity pass\n(baseline passes\nall rules)", "cal")
box(1, 6, 20, 12, "Screening (OFAT, Morris)\nvariance shares (Sobol)\nnominal engine", "opt")
box(26, 6, 20, 12, "Optimisers: NSGA-II,\nTPE, random search\n(classes A, B, C)", "opt")
box(51, 6, 21, 12, "Robust NSGA-II over\nthe ensemble\npicked: econ/power/knee", "opt")
box(77, 6, 22, 12, "Paired comparison vs\nbaseline, scenarios,\nvalue of information", "out")
for a in [(21, 47.5, 26, 47.5), (46, 47.5, 51, 47.5), (72, 47.5, 77, 47.5), (88, 42, 88, 36.5), (77, 30.5, 72, 30.5), (51, 30.5, 46, 30.5), (26, 30.5, 21, 30.5),
          (11, 25, 11, 18.5), (21, 12, 26, 12), (46, 12, 51, 12), (72, 12, 77, 12)]:
    arrow(*a)
ax.text(50, 54.8, "Calibrated-ensemble robust tuning workflow", ha="center", fontsize=9, weight="bold")
fig.savefig(ROOT / "figures" / "f00_workflow.png", dpi=200, bbox_inches="tight")
idx = ROOT / "figures" / "FIGURE_INDEX.md"
old = idx.read_text(encoding="utf-8") if idx.exists() else "# Figure index\n"
if "f00_workflow" not in old:
    idx.write_text(old.rstrip("\n") + "\n- `f00_workflow.png`: Study workflow. Published specification and its uncertain inputs are turned into an ensemble of calibrated engines; screening, optimisation and robust optimisation are then evaluated by paired comparison with graded claims.\n", encoding="utf-8")
print("workflow figure written")
