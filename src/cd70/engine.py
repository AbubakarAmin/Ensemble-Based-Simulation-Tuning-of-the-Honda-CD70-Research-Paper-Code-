"""Python wrapper around the Numba kernel: nominal parameters, valve timing, engine_point().

LOCKED FILE for the agent: do not edit unless a task says so.
All kernel parameters are in SI units (m, Pa, K, kg, s) except angles (degrees).
"""

from __future__ import annotations

import math

import numpy as np

from cd70 import kernel as K

CHEN_FLYNN = (0.4, 0.005, 0.09, 0.0009)  # bar, bar/bar, bar per m/s, bar per (m/s)^2. ASSUMED, scaled by fmep_scale


def valve_angles(io, ic, eo, ec, int_shift=0.0, exh_shift=0.0, dur_scale=1.0):
    """Return (iv_open, iv_dur, ev_open, ev_dur) in the 0..720 degree convention.

    io = intake opens deg BTDC, ic = intake closes deg ABDC, eo = exhaust opens deg BBDC,
    ec = exhaust closes deg ATDC. Positive shift = valve events later. dur_scale scales both durations
    about their centres.
    """
    out = []
    for open0, close0, shift in ((-io, 180.0 + ic, int_shift), (540.0 - eo, 720.0 + ec, exh_shift)):
        dur0 = close0 - open0
        centre = 0.5 * (open0 + close0) + shift
        dur = dur0 * dur_scale
        out.append(((centre - 0.5 * dur) % 720.0, dur))
    (iv_open, iv_dur), (ev_open, ev_dur) = out
    return iv_open, iv_dur, ev_open, ev_dur


def nominal_params(timing_scenario: str = "A") -> dict:
    """Mid-range parameter set (kernel names). Scenario A = manual timing as printed, B = +20 deg per flank."""
    extra = 20.0 if timing_scenario.upper() == "B" else 0.0
    iv_open, iv_dur, ev_open, ev_dur = valve_angles(0 + extra, 20 + extra, 20 + extra, 0 + extra)
    return {
        "bore_m": 0.0470, "stroke_m": 0.0414, "conrod_m": 0.091, "cr": 9.3,
        "iv_open_deg": iv_open, "iv_dur_deg": iv_dur, "ev_open_deg": ev_open, "ev_dur_deg": ev_dur,
        "lift_in_m": 0.0065, "lift_ex_m": 0.0065, "clearance_m": 0.00009,
        "head_in_m": 0.0250, "head_ex_m": 0.0219, "stem_in_m": 0.00498, "stem_ex_m": 0.00496,
        "cd_valve": 0.70,
        "venturi_m": 0.018, "cd_throttle": 0.80, "muffler_area_m2": 100e-6, "cd_muffler": 0.70, "leak_area_m2": 0.15e-6,
        "v_intake_m3": 100e-6, "v_exhaust_m3": 400e-6, "t_exhaust_k": 900.0,
        "lambda_wot": 0.90, "lambda_cruise": 1.00, "lambda_idle": 0.88, "fuel_mult_main": 1.0,
        "charge_heat_k": 30.0,
        "ign_low_deg": 20.0, "ign_4000_deg": 35.0, "ign_above_deg": 35.0,
        "burn_dur_deg": 60.0, "wiebe_m": 2.0, "spark_delay_deg": 10.0, "eta_comb": 0.95,
        "fmep_scale": 1.0, "t_wall_offset_k": 0.0, "knock_k": 1.0, "ron": 87.0,
        "t_amb_k": 308.15, "p_amb_pa": 101325.0,
        "const_gamma": 0.0, "wall_on": 1.0, "burn_on": 1.0, "fuel_on": 1.0,
        "max_cycles": 14.0, "dt_max_s": 25e-6, "dth_deg": 0.0,
    }


def ambient_pressure(alt_m: float) -> float:
    return 101325.0 * (1.0 - 2.2558e-5 * alt_m) ** 5.2559


def pack(params: dict, rpm: float, alpha: float) -> np.ndarray:
    p = dict(params)
    p["rpm"] = float(rpm)
    p["alpha"] = float(alpha)
    missing = [n for n in K.NAMES if n not in p]
    if missing:
        raise KeyError(f"missing kernel parameters: {missing}")
    return np.array([float(p[n]) for n in K.NAMES], dtype=np.float64)


def engine_point(rpm: float, alpha: float, params: dict, with_trace: bool = False) -> dict:
    """Run one engine point. Returns a dict of results (SI plus convenient bar / hp / g/kWh fields)."""
    P = pack(params, rpm, alpha)
    res, trace = K.run(P)
    r = {n: float(res[i]) for i, n in enumerate(K.RES_NAMES)}
    Vd = 0.25 * math.pi * params["bore_m"] ** 2 * params["stroke_m"]
    sp = 2.0 * params["stroke_m"] * rpm / 60.0
    th, p, V = trace[0], trace[1], trace[3]
    sel = (th[:-1] >= 180.0 - 1e-9) & (th[1:] <= 540.0 + 1e-9)
    w_gross = float(np.sum(0.5 * (p[:-1] + p[1:])[sel] * np.diff(V)[sel]))
    pmax_bar = r["pmax_pa"] / 1e5
    cf = CHEN_FLYNN
    fmep_bar = params["fmep_scale"] * (cf[0] + cf[1] * pmax_bar + cf[2] * sp + cf[3] * sp * sp)
    imep_net = r["w_net_j"] / Vd
    bmep = imep_net - fmep_bar * 1e5
    torque = bmep * Vd / (4.0 * math.pi)
    power_w = torque * 2.0 * math.pi * rpm / 60.0
    fuel_kg_s = r["m_fuel_kg"] * rpm / 120.0
    bsfc = fuel_kg_s * 3.6e9 / power_w if power_w > 1.0 else float("nan")
    r.update(
        rpm=float(rpm), alpha=float(alpha), sp_ms=sp, vd_m3=Vd,
        imep_net_bar=imep_net / 1e5, imep_gross_bar=w_gross / Vd / 1e5,
        pmep_bar=(imep_net - w_gross / Vd) / 1e5, pmax_bar=pmax_bar, fmep_bar=fmep_bar, bmep_bar=bmep / 1e5,
        torque_nm=torque, power_kw=power_w / 1e3, power_hp=power_w / 745.7,
        bsfc_gkwh=bsfc, fuel_g_h=fuel_kg_s * 3.6e6,
    )
    if with_trace:
        r["trace"] = {n: trace[i].copy() for i, n in enumerate(K.TRACE_NAMES)}
    return r
