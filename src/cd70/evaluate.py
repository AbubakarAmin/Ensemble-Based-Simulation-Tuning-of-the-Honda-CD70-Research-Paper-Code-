"""evaluate_design(): the single function every experiment calls.

LOCKED FILE for the agent: do not edit unless a task says so.

One call = one engine (unc), one tuning (design), one scenario (scen), one timing reading ('A' or 'B').
Cost about 0.3 s. Returns a flat dict (one row of evals.parquet).
"""

from __future__ import annotations

import math
import time

import numpy as np

from cd70 import cycle
from cd70 import vehicle as V
from cd70.engine import engine_point
from cd70.params import SCENARIO_CAL, UNC_NOMINAL, build_params, knock_k_from_margin

WOT_RPMS = tuple(float(r) for r in range(2000, 7501, 500))
EXTRA_RPMS = (8000.0, 8500.0, 9000.0, 9500.0)  # only used for top speed
CRUISE_KMH = (30.0, 40.0, 50.0)
DESIGN_NAMES = ("cr", "d_ign_low_deg", "d_ign_high_deg", "main_jet_delta",
                "int_shift_deg", "exh_shift_deg", "cam_dur_scale", "int_valve_scale")

_KNOCK_CACHE: dict = {}


def ensure_knock_k(unc: dict, timing: str) -> dict:
    """Return a copy of unc with 'knock_k' set from 'knock_margin_base' (baseline max KI at calibration conditions)."""
    if "knock_k" in unc and unc["knock_k"] is not None and not (isinstance(unc["knock_k"], float) and math.isnan(unc["knock_k"])):
        return unc
    margin = unc.get("knock_margin_base", 0.85)
    key = (timing, tuple(sorted((k, round(float(v), 9)) for k, v in unc.items() if k != "knock_k")))
    if key not in _KNOCK_CACHE:
        if len(_KNOCK_CACHE) > 5000:
            _KNOCK_CACHE.clear()
        _KNOCK_CACHE[key] = knock_k_from_margin(unc, timing, margin)
    out = dict(unc)
    out["knock_k"] = _KNOCK_CACHE[key]
    return out


def evaluate_design(unc: dict | None = None, design: dict | None = None, scen: dict | None = None,
                    timing: str = "A", curves: bool = False) -> dict:
    t0 = time.perf_counter()
    full_unc = {**UNC_NOMINAL, **(unc or {})}
    full_unc = ensure_knock_k(full_unc, timing)
    scen_full = {**SCENARIO_CAL, **(scen or {})}
    p = build_params(full_unc, design, scen_full, timing)
    rho = p["p_amb_pa"] / (287.0 * p["t_amb_k"])
    row: dict = {"status": "ok", "timing": timing}
    rows = [engine_point(rpm, 1.0, p) for rpm in WOT_RPMS]
    tq = np.array([r["torque_nm"] for r in rows])
    pw = np.array([r["power_kw"] for r in rows])
    ki = np.array([r["ki_end"] for r in rows])
    pm = np.array([r["pmax_bar"] for r in rows])
    ve = np.array([r["ve_air"] for r in rows])
    bs = np.array([r["bsfc_gkwh"] for r in rows])
    rp = np.array(WOT_RPMS)
    row.update(
        f1_torque_wot_mean_nm=float(tq.mean()),
        p_peak_kw=float(pw.max()), rpm_p_peak=float(rp[pw.argmax()]),
        t_peak_nm=float(tq.max()), rpm_t_peak=float(rp[tq.argmax()]),
        bsfc_min_gkwh=float(np.nanmin(bs)), ki_max=float(ki.max()), rpm_ki_max=float(rp[ki.argmax()]),
        p_cyl_max_bar=float(pm.max()), ve_7500=float(ve[-1]), ve_max=float(ve.max()),
        t_3000_nm=float(np.interp(3000.0, rp, tq)), t_4000_nm=float(np.interp(4000.0, rp, tq)),
        t_5000_nm=float(np.interp(5000.0, rp, tq)), t_5500_nm=float(np.interp(5500.0, rp, tq)),
        t_7500_nm=float(tq[-1]), p_7500_hp=float(pw[-1] * 1000.0 / 745.7),
        flatness_t7500_t5500=float(tq[-1] / np.interp(5500.0, rp, tq)),
        all_converged=float(all(r["converged"] == 1.0 for r in rows)),
    )
    l100 = []
    cruise = []
    for v in CRUISE_KMH:
        c = V.cruise_point(v, p, full_unc, rho)
        cruise.append(c)
        if c["status"] != "ok":
            row["status"] = "infeasible"
            l100.append(float("nan"))
        else:
            l100.append(c["l_100km"])
        key = f"{int(v)}"
        row[f"l100_{key}"] = l100[-1]
        row[f"alpha_{key}"] = c.get("alpha", float("nan"))
        row[f"rpm_cruise_{key}"] = c["rpm"]
        row[f"bsfc_cruise_{key}"] = c.get("bsfc_gkwh", float("nan"))
    row["f2_cruise_l100km"] = float(np.mean(l100)) if all(np.isfinite(l100)) else float("nan")
    city = cycle.city_from_params(p, full_unc, rho)  # v15: the optimiser objective (config/optimiser.yaml)
    row["f2_city_l100km"] = city["l_100km"] if city["status"] == "ok" else float("nan")
    row["f2_city_cruise_l100km"] = city.get("cruise_l_100km", float("nan"))
    row["f2_city_accel_l100km"] = city.get("accel_l_100km", float("nan"))
    row["km_l_40"] = 100.0 / row["l100_40"] if np.isfinite(row["l100_40"]) else float("nan")
    row["t_0_60_s"] = V.accel_0_60_s(rp, tq, full_unc, rho)
    extra = [engine_point(r, 1.0, p) for r in EXTRA_RPMS]
    rp_all = np.concatenate([rp, np.array(EXTRA_RPMS)])
    pw_all = np.concatenate([pw, np.array([r["power_kw"] for r in extra])])
    row["v_top_kmh"] = V.top_speed_kmh(rp_all, pw_all, full_unc, rho)
    row["v_top_indicated_kmh"] = row["v_top_kmh"] * (1.0 + full_unc.get("speedo_overread", 0.0))
    row["p_9500_hp"] = float(pw_all[-1] * 1000.0 / 745.7)
    row["knock_k"] = full_unc["knock_k"]
    row["runtime_s"] = time.perf_counter() - t0
    if curves:
        row["_wot"] = rows
        row["_cruise"] = cruise
    return row
