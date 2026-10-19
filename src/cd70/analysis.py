"""Small analysis helpers (Pareto, hypervolume, bootstrap). LOCKED FILE for the agent."""

from __future__ import annotations

import numpy as np

HV_REF = np.array([-0.90, 1.10])  # o1 = -f1/f1_base, o2 = f2/f2_base. Both minimised.


def pareto_mask(F: np.ndarray) -> np.ndarray:
    """True for non-dominated rows of F (minimise all columns)."""
    F = np.asarray(F, float)
    n = len(F)
    keep = np.ones(n, bool)
    for i in range(n):
        if not keep[i]:
            continue
        dom = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if dom.any():
            keep[i] = False
    return keep


def hypervolume(F: np.ndarray, ref: np.ndarray = HV_REF) -> float:
    from pymoo.indicators.hv import HV

    F = np.asarray(F, float)
    if len(F) == 0:
        return 0.0
    F = F[np.all(F < ref, axis=1)]
    if len(F) == 0:
        return 0.0
    return float(HV(ref_point=ref)(F))


def hv_curve(F: np.ndarray, feasible: np.ndarray, ref: np.ndarray = HV_REF, step: int = 50) -> list:
    """Hypervolume of the feasible points among the first k evaluations, for k = step, 2*step, ..."""
    out = []
    for k in range(step, len(F) + 1, step):
        m = feasible[:k].astype(bool)
        out.append((k, hypervolume(F[:k][m], ref) if m.any() else 0.0))
    return out


def bootstrap_ci(x: np.ndarray, stat=np.median, n: int = 2000, seed: int = 0, alpha: float = 0.05) -> tuple:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return (float("nan"),) * 3
    s = [stat(rng.choice(x, len(x))) for _ in range(n)]
    return float(stat(x)), float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2))


def claim_level(deltas: np.ndarray, material: float = 0.5, seed: int = 0) -> str:
    """Claim rule on paired improvements IN PERCENT (positive = better); material = 0.5 percent. See docs/CLAIM_RULES.md."""
    d = np.asarray(deltas, float)
    d = d[np.isfinite(d)]
    if len(d) < 30:
        return "NOT SUPPORTED (too few members)"
    med, lo, _hi = bootstrap_ci(d, seed=seed)
    frac = float(np.mean(d > 0))
    if lo > material and frac >= 0.95:
        return "CLAIM"
    if lo > 0 and frac >= 0.80:
        return "CONDITIONAL"
    if med > 0 and frac >= 0.60:
        return "INDICATIVE"
    return "NOT SUPPORTED"
