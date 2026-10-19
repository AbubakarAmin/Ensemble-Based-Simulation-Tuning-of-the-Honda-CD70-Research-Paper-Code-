"""v14: city-cycle fuel, run-in scenario and steady-speed diagnostics for the validation step.

NOT used by calibration, the optimiser or the locked evaluation (evaluate_design is unchanged), so every v12 result stays valid.
Time shares, idle throttle and the run-in friction factor come from config/validation.yaml and are ASSUMED, not measured.
"""

from __future__ import annotations

import math

import numpy as np

from cd70 import config
from cd70 import vehicle as V
from cd70.engine import engine_point
from cd70.params import SCENARIO_CAL, UNC_NOMINAL, build_params


def params_for(unc: dict | None, timing: str = "B", scen: dict | None = None):
    """Same preamble as evaluate_design: returns (full_unc, params, rho_air)."""
    from cd70.evaluate import ensure_knock_k  # lazy: evaluate imports this module

    full_unc = ensure_knock_k({**UNC_NOMINAL, **(unc or {})}, timing)
    scen_full = {**SCENARIO_CAL, **(scen or {})}
    p = build_params(full_unc, None, scen_full, timing)
    rho = p["p_amb_pa"] / (287.0 * p["t_amb_k"])
    return full_unc, p, rho


def _phases(cfg: dict, idle_share: float | None) -> list:
    """Phase list with time shares. If idle_share is given, idle gets that share and the others are rescaled pro rata."""
    phases = [dict(ph) for ph in cfg["phases"]]
    if idle_share is None:
        return phases
    other = [ph for ph in phases if ph["kind"] != "idle"]
    old_other = sum(ph["time_share"] for ph in other)
    for ph in phases:
        if ph["kind"] == "idle":
            ph["time_share"] = idle_share
        else:
            ph["time_share"] = ph["time_share"] / old_other * (1.0 - idle_share)
    return phases


def city_cycle(unc: dict | None, timing: str = "B", idle_share: float | None = None, scen: dict | None = None) -> dict:
    """Time-weighted fuel use over the indicative city cycle. Returns l_100km, km_per_l and status."""
    full_unc, p, rho = params_for(unc, timing, scen)
    return city_from_params(p, full_unc, rho, idle_share)


def city_from_params(p: dict, full_unc: dict, rho: float, idle_share: float | None = None) -> dict:
    """City cycle for an already-built engine parameter set (used inside evaluate_design)."""
    cfg = config.validation()["city_cycle"]
    idle_cfg = config.validation()["idle"]
    total_l = 0.0
    total_d = 0.0
    acc_l_per_km = accel_l_per_km(full_unc, cfg["accel"])
    for ph in _phases(cfg, idle_share):
        w = float(ph["time_share"])
        if ph["kind"] == "idle":
            fuel_g_h = engine_point(float(idle_cfg["rpm"]), float(idle_cfg["throttle"]), p)["fuel_g_h"]
            fuel_l_h = fuel_g_h / 1000.0 / V.FUEL_DENSITY_KG_L
            dist = 0.0
        else:
            c = V.cruise_point(float(ph["speed_kmh"]), p, full_unc, rho, gear=int(ph["gear"]))
            if c["status"] != "ok":
                return {"status": "infeasible", "l_100km": float("nan"), "km_per_l": float("nan")}
            fuel_l_h = c["fuel_l_h"]
            dist = float(ph["speed_kmh"])
        total_l += w * fuel_l_h
        total_d += w * dist
    cruise_l100 = total_l / total_d * 100.0
    l100 = cruise_l100 + acc_l_per_km * 100.0
    return {"status": "ok", "l_100km": l100, "km_per_l": 100.0 / l100,
            "cruise_l_100km": cruise_l100, "accel_l_100km": acc_l_per_km * 100.0}


def accel_l_per_km(unc: dict, acc: dict) -> float:
    """Fuel per km for stop-and-go acceleration: kinetic energy of each restart / (efficiency x fuel energy)."""
    m = float(unc.get("mass_kg", V.MASS_KG)) * float(acc["rot_mass_factor"])
    v = float(acc["to_speed_kmh"]) / 3.6
    ke_j = 0.5 * m * v * v
    fuel_j = ke_j / float(acc["efficiency"])
    return float(acc["events_per_km"]) * fuel_j / (float(config.validation()["city_cycle"]["lhv_mj_per_kg"]) * 1e6 * V.FUEL_DENSITY_KG_L)


def runin_unc(unc: dict | None) -> dict:
    """Copy of the uncertain inputs with friction raised by the run-in factor (new bike, under 1,500 km)."""
    base = {**UNC_NOMINAL, **(unc or {})}
    out = dict(base)
    out["fmep_scale"] = float(base["fmep_scale"]) * float(config.validation()["runin"]["fmep_factor"])
    return out


def steady_km_per_l(unc: dict | None, speed_kmh: float, timing: str = "B") -> dict:
    """Steady cruise in 4th gear at speed_kmh (same definition as the locked evaluation)."""
    full_unc, p, rho = params_for(unc, timing)
    c = V.cruise_point(speed_kmh, p, full_unc, rho)
    if c["status"] != "ok":
        return {"status": "infeasible", "km_per_l": float("nan"), "rpm": c["rpm"]}
    return {"status": "ok", "km_per_l": 100.0 / c["l_100km"], "rpm": c["rpm"]}


def gearing_check() -> dict:
    """Diagnostic only: engine speed at 30/40/50 km/h in 4th gear and the speed reached at the 7,500 rpm rated speed."""
    ratio = V.overall_ratio(4)
    rr = 0.279
    return {
        "rpm_30": V.rpm_at_speed(30.0, ratio, rr),
        "rpm_40": V.rpm_at_speed(40.0, ratio, rr),
        "rpm_50": V.rpm_at_speed(50.0, ratio, rr),
        "kmh_at_7500_rpm": V.speed_at_rpm(7500.0, ratio, rr),
        "kmh_at_9500_rpm": V.speed_at_rpm(9500.0, ratio, rr),
    }


def verdict(model_p5: float, model_p50: float, model_p95: float, low: float, high: float, tol: float) -> str:
    """Pre-declared rule (config/validation.yaml): AGREE if the model median lies inside [low*(1-tol), high*(1+tol)]."""
    if not all(math.isfinite(x) for x in (model_p50, low, high)):
        return "NOT AVAILABLE"
    if low * (1.0 - tol) <= model_p50 <= high * (1.0 + tol):
        return "AGREE"
    return "MODEL HIGHER THAN PUBLISHED" if model_p50 > high * (1.0 + tol) else "MODEL LOWER THAN PUBLISHED"


def percentiles(values) -> tuple:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return (float("nan"),) * 3
    return tuple(float(np.percentile(arr, q)) for q in (5, 50, 95))
