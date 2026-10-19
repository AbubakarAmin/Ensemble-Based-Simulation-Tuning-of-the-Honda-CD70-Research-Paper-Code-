"""Row-level functions used by the batch runner. LOCKED FILE for the agent.

Row key convention (flat dict, so one parquet table holds everything):
  u_<name>  uncertain input,  d_<name>  design variable,  s_ron / s_t_amb_c / s_alt_m  scenario,  timing  'A' or 'B'
"""

from __future__ import annotations

import math

import numpy as np

from cd70 import config, rules
from cd70 import vehicle as V
from cd70.engine import engine_point
from cd70.evaluate import evaluate_design
from cd70.objective import FUEL_KEY
from cd70.params import SCENARIO_CAL, build_params

KI_LIMIT = 0.95
PMAX_LIMIT_BAR = 60.0


def split_row(row: dict) -> tuple:
    unc = {k[2:]: float(v) for k, v in row.items() if k.startswith("u_") and v == v}
    des = {k[2:]: float(v) for k, v in row.items() if k.startswith("d_") and v == v}
    scen = {k[2:]: float(v) for k, v in row.items() if k.startswith("s_") and v == v}
    return unc, des, scen, str(row.get("timing", "A"))


def flat_row(unc: dict | None = None, design: dict | None = None, scen: dict | None = None, timing: str = "A",
             **extra) -> dict:
    r = {"timing": timing}
    r.update({f"u_{k}": v for k, v in (unc or {}).items()})
    r.update({f"d_{k}": v for k, v in (design or {}).items()})
    r.update({f"s_{k}": v for k, v in (scen or {}).items()})
    r.update(extra)
    return r


def eval_checked(row: dict) -> dict:
    """Full evaluation + design rules + plausibility + constraints. This is THE function every experiment uses."""
    unc, des, scen, timing = split_row(row)
    res = evaluate_design(unc, des, scen, timing)
    dr = rules.design_rules(unc, des, timing)
    pl = rules.plausibility(res, des.get("cr", 9.3))
    res["rules_failed"] = ",".join(rules.failed(dr))
    res["plaus_failed"] = ",".join(rules.failed(pl))
    res["rules_ok"] = float(rules.all_ok(dr))
    res["plaus_ok"] = float(rules.all_ok(pl))
    for k, v in dr.items():
        res[f"rule_{k}"] = v["value"]
    res["g_knock"] = res["ki_max"] - KI_LIMIT
    res["g_pmax"] = res["p_cyl_max_bar"] - PMAX_LIMIT_BAR
    ok = (res["status"] == "ok" and res["rules_ok"] == 1.0 and res["plaus_ok"] == 1.0
          and res["g_knock"] <= 0.0 and res["g_pmax"] <= 0.0
          and math.isfinite(res[FUEL_KEY]) and math.isfinite(res["f1_torque_wot_mean_nm"]))
    res["feasible"] = float(ok)
    return res


def cal_metrics(row: dict) -> dict:
    """Calibration observables for one engine (uncertain inputs only). Runs 4 engine points."""
    unc, _des, _scen, timing = split_row(row)
    cal = config.calibration()
    scen = {**SCENARIO_CAL, **{k: v for k, v in cal["conditions"].items()}}
    p = build_params({**config.nominal_unc(), **unc}, None, scen, timing)
    r75 = engine_point(7500.0, 1.0, p)
    sweep = {r: engine_point(float(r), 1.0, p) for r in (6500, 8500, 9500)}
    r55 = engine_point(5500.0, 1.0, p, with_trace=True)
    tr = r55["trace"]
    th_pmax = float(tr["th"][int(tr["p"].argmax())]) - 360.0
    pm = dict(p)
    pm.update(fuel_on=0.0, burn_on=0.0)
    rc = engine_point(float(unc.get("crank_rpm", 600.0)), 1.0, pm)
    crank_bar = rc["pmax_bar"] - p["p_amb_pa"] / 1e5
    uu = {**config.nominal_unc(), **unc}
    rpm_pts = np.array([5500.0, 6500.0, 7500.0, 8500.0, 9500.0])
    pw_pts = np.array([r55["power_kw"], sweep[6500]["power_kw"], r75["power_kw"], sweep[8500]["power_kw"], sweep[9500]["power_kw"]])
    rho = p["p_amb_pa"] / (287.0 * p["t_amb_k"])
    v_true = V.top_speed_kmh(rpm_pts, pw_pts, uu, rho)
    out = {
        "v_top_true_kmh": v_true, "v_top_indicated_kmh": v_true * (1.0 + uu["speedo_overread"]),
        "power_hp_7500": r75["power_hp"], "torque_nm_5500": r55["torque_nm"], "cranking_bar": crank_bar,
        "bsfc_gkwh_7500": r75["bsfc_gkwh"], "ve_7500": r75["ve_air"], "theta_pmax_atdc_5500": th_pmax,
        "pmax_bar": max(r75["pmax_bar"], r55["pmax_bar"]),
        "converged": float(r75["converged"] == 1.0 and r55["converged"] == 1.0 and rc["converged"] == 1.0),
    }
    return out


def cal_accept(m: dict, cal: dict | None = None, power_target: float | None = None) -> bool:
    cal = cal or config.calibration()
    pt = power_target if power_target is not None else cal["power_hp_7500"]["target"]
    checks = [
        abs(m["power_hp_7500"] - pt) <= cal["power_hp_7500"]["rel_tol"] * pt,
        abs(m["torque_nm_5500"] - cal["torque_nm_5500"]["target"]) <= cal["torque_nm_5500"]["rel_tol"] * cal["torque_nm_5500"]["target"],
        abs(m["cranking_bar"] - cal["cranking_bar"]["target"]) <= cal["cranking_bar"]["rel_tol"] * cal["cranking_bar"]["target"],
        cal["bsfc_gkwh_7500"]["low"] <= m["bsfc_gkwh_7500"] <= cal["bsfc_gkwh_7500"]["high"],
        cal["ve_7500"]["low"] <= m["ve_7500"] <= cal["ve_7500"]["high"],
        cal["theta_pmax_atdc_5500"]["low"] <= m["theta_pmax_atdc_5500"] <= cal["theta_pmax_atdc_5500"]["high"],
        m["pmax_bar"] < cal["pmax_bar"]["high"],
        cal["top_speed_true_kmh"]["low"] <= m["v_top_true_kmh"] <= cal["top_speed_true_kmh"]["high"],
        m["converged"] == 1.0,
    ]
    return all(checks)


def cal_row(row: dict) -> dict:
    m = cal_metrics(row)
    cal = config.calibration()
    m["accepted"] = float(cal_accept(m, cal))
    m["accepted_p45"] = float(cal_accept(m, cal, cal["power_target_sensitivity_hp"]))
    return m
