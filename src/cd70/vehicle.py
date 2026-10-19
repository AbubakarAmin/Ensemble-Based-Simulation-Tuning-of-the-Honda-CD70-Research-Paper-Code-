"""Vehicle model: gearing, road load, cruise throttle solve, 0-60 km/h estimate, gear-limited top speed.

LOCKED FILE for the agent: do not edit unless a task says so.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq

from cd70.engine import engine_point

GEARS = (3.272, 1.937, 1.350, 1.043)
FINAL_DRIVE = 41.0 / 14.0  # exact fraction (sheet rounds to 2.93)
MASS_KG = 82.0 + 3.0 + 70.0  # dry + fuel/oil + rider
CRR = 0.02
CDA_M2 = 0.50
ETA_DRIVE = 0.85
ROT_MASS_FACTOR = 1.10
FUEL_DENSITY_KG_L = 0.74
RPM_LIMIT = 7500.0


def overall_ratio(gear: int, primary: float = 3.722, gear_scale: float = 1.0) -> float:
    """gear = 1..4. Engine revolutions per wheel revolution."""
    return primary * GEARS[gear - 1] * gear_scale * FINAL_DRIVE


def rpm_at_speed(v_kmh: float, ratio: float, rolling_radius_m: float = 0.279) -> float:
    wheel_rps = (v_kmh / 3.6) / (2.0 * math.pi * rolling_radius_m)
    return wheel_rps * ratio * 60.0


def speed_at_rpm(rpm: float, ratio: float, rolling_radius_m: float = 0.279) -> float:
    return rpm / 60.0 / ratio * 2.0 * math.pi * rolling_radius_m * 3.6


def road_load_force(v_kmh: float, rho_air: float = 1.147, mass: float = MASS_KG, crr: float = CRR,
                    cda: float = CDA_M2) -> float:
    v = v_kmh / 3.6
    return crr * mass * 9.81 + 0.5 * rho_air * cda * v * v


def road_load_engine_power_hp(v_kmh: float, rho_air: float = 1.147, eta: float = ETA_DRIVE,
                              cda: float = CDA_M2, crr: float = CRR, mass: float = MASS_KG) -> float:
    return road_load_force(v_kmh, rho_air, mass, crr, cda) * (v_kmh / 3.6) / eta / 745.7


RPM_TOP_CAP = 9500.0  # ASSUMED highest engine speed reached at top speed (no rev limiter on the CDI; valve float assumed above this)


def _road(unc: dict) -> dict:
    return {"mass": unc.get("mass_kg", MASS_KG), "crr": unc.get("crr", CRR), "cda": unc.get("cda_m2", CDA_M2)}


def cruise_point(v_kmh: float, params: dict, unc: dict, rho_air: float, gear: int = 4) -> dict:
    """Find the throttle that gives steady cruise at v_kmh in `gear`. Returns a dict, status 'ok' or 'infeasible'."""
    ratio = overall_ratio(gear, unc.get("primary", 3.722), unc.get("gear_scale", 1.0))
    rr = unc.get("rolling_radius_m", 0.279)
    rpm = rpm_at_speed(v_kmh, ratio, rr)
    eta = unc.get("drive_eff", ETA_DRIVE)
    force = road_load_force(v_kmh, rho_air, **_road(unc))
    t_req = force * rr / (ratio * eta)  # engine brake torque needed, Nm

    def f(a):
        return engine_point(rpm, a, params)["torque_nm"] - t_req

    lo, hi = 0.001, 1.0
    if f(hi) < 0.0:
        return {"status": "infeasible", "rpm": rpm, "t_req_nm": t_req}
    if f(lo) > 0.0:
        alpha = lo
    else:
        alpha = brentq(f, lo, hi, xtol=1e-4, rtol=1e-6, maxiter=40)
    r = engine_point(rpm, alpha, params)
    fuel_l_h = r["fuel_g_h"] / 1000.0 / FUEL_DENSITY_KG_L
    return {
        "status": "ok", "rpm": rpm, "alpha": alpha, "t_req_nm": t_req, "torque_nm": r["torque_nm"],
        "bsfc_gkwh": r["bsfc_gkwh"], "fuel_l_h": fuel_l_h, "l_100km": fuel_l_h / v_kmh * 100.0,
        "lam": r["lam"], "ki_end": r["ki_end"], "bmep_bar": r["bmep_bar"],
    }


def accel_0_60_s(rpms: np.ndarray, torque_nm: np.ndarray, unc: dict, rho_air: float = 1.147) -> float:
    """Indicative 0-60 km/h time from the WOT torque curve. 1.0 s launch to 2500 rpm in 1st, shifts at 7000 rpm."""
    primary = unc.get("primary", 3.722)
    gs = unc.get("gear_scale", 1.0)
    rr = unc.get("rolling_radius_m", 0.279)
    gear = 1
    ratio = overall_ratio(gear, primary, gs)
    v = speed_at_rpm(2500.0, ratio, rr)
    t = 1.0
    dt = 0.02
    eta = unc.get("drive_eff", ETA_DRIVE)
    road = _road(unc)
    meff = road["mass"] * ROT_MASS_FACTOR
    shift_until = 0.0
    while v < 60.0 and t < 60.0:
        ratio = overall_ratio(gear, primary, gs)
        rpm = rpm_at_speed(v, ratio, rr)
        if rpm > 7000.0 and gear < 4:
            gear += 1
            shift_until = t + 0.4
            continue
        tq = float(np.interp(min(max(rpm, rpms[0]), rpms[-1]), rpms, torque_nm))
        f_drive = 0.0 if t < shift_until else tq * ratio * eta / rr
        a = (f_drive - road_load_force(v, rho_air, **road)) / meff
        v_new = v + a * dt * 3.6
        if a <= 0.0 and f_drive > 0.0:
            return float("nan")
        v = max(v_new, v)
        t += dt
    return t if v >= 60.0 else float("nan")


def top_speed_kmh(rpms: np.ndarray, power_kw: np.ndarray, unc: dict, rho_air: float = 1.147) -> float:
    """True top speed in 4th gear: highest speed where WOT power (interpolated, rpm capped at RPM_TOP_CAP) covers road load."""
    ratio = overall_ratio(4, unc.get("primary", 3.722), unc.get("gear_scale", 1.0))
    rr = unc.get("rolling_radius_m", 0.279)
    eta = unc.get("drive_eff", ETA_DRIVE)
    v_max_gear = speed_at_rpm(RPM_TOP_CAP, ratio, rr)
    best = 0.0
    for v in np.linspace(20.0, v_max_gear, 200):
        rpm = rpm_at_speed(v, ratio, rr)
        p_eng = float(np.interp(min(max(rpm, rpms[0]), rpms[-1]), rpms, power_kw)) * 1000.0
        p_need = road_load_force(v, rho_air, **_road(unc)) * (v / 3.6) / eta
        if p_eng >= p_need:
            best = v
    return best
