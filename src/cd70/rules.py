"""Engineering knowledge layer ("design rules"), in the spirit of LEAP 71's Noyron idea: every candidate design
must pass encoded physical, hardware and manufacturing rules BEFORE its numbers are believed.

LOCKED FILE for the agent: do not edit unless a task says so.

Two groups:
  design_rules(...)   rules on the CONFIGURATION (cheap, no engine run needed)
  plausibility(row)   rules on the RESULTS of an engine run (a result that breaks physics is a model failure)
Every limit has a tag: PHYSICS (cannot be broken), HARDWARE (real part limit, value ASSUMED), CONVENTION.
"""

from __future__ import annotations

import math

from cd70 import kernel as K
from cd70.engine import valve_angles
from cd70.params import DESIGN_BASELINE, UNC_NOMINAL

LHV_J_KG = 44.0e6
# name: (limit_kind, limit, tag, meaning)
DESIGN_LIMITS = {
    "head_skim_mm": ("max", 0.8, "HARDWARE", "material removed from head/deck to raise CR from 9.3"),
    "valve_piston_gap_mm": ("min", 1.0, "HARDWARE", "closest approach of a valve head to the piston crown near TDC"),
    "valve_accel_ratio": ("max", 1.15, "HARDWARE", "peak valve acceleration at 7500 rpm relative to the stock cam (spring limit)"),
    "overlap_deg": ("max", 70.0, "CONVENTION", "both valves open around TDC; larger overlap ruins idle and cruise"),
    "head_in_over_bore": ("max", 0.58, "HARDWARE", "intake valve head diameter divided by bore (must fit the head)"),
    "ign_adv_max_deg": ("max", 40.0, "HARDWARE", "largest ignition advance the ignition box/trigger can give"),
    "ign_adv_min_deg": ("min", 0.0, "HARDWARE", "no retard past TDC"),
    "lambda_wot_eff": ("max", 1.0, "PHYSICS", "never run lean at full load (detonation and melted piston)"),
    "lambda_wot_rich": ("min", 0.78, "PHYSICS", "richer than this misfires"),
}
RESULT_LIMITS = {
    "bsfc_min_gkwh": ("min", 230.0, "PHYSICS", "brake efficiency above 36 percent is not possible for this engine class"),
    "ve_max": ("max", 1.10, "PHYSICS", "volumetric efficiency of a naturally aspirated engine without tuned-intake resonance"),
    "p_peak_hp": ("max", 9.0, "PHYSICS", "specific power above 125 hp/L is not credible for this 72 cc carbureted engine"),
    "t_peak_nm": ("max", 7.5, "PHYSICS", "BMEP above 13 bar is not credible for NA petrol"),
    "t_peak_nm_min": ("min", 2.0, "PHYSICS", "an engine making less torque than this does not run"),
    "eta_brake_over_otto": ("max", 0.75, "PHYSICS", "brake efficiency must stay below 75 percent of the ideal Otto efficiency"),
    "converged": ("min", 1.0, "PHYSICS", "all 12 WOT points must have a converged cycle"),
}


def _both_open_deg(p: dict) -> float:
    n = 0
    for k in range(-240, 241):  # 0.5 degree steps over -120..+120
        th = 0.5 * k
        if (K.valve_lift(th, p["iv_open_deg"], p["iv_dur_deg"], 1.0, 0.0) > 0.0
                and K.valve_lift(th, p["ev_open_deg"], p["ev_dur_deg"], 1.0, 0.0) > 0.0):
            n += 1
    return 0.5 * n


def design_rules(unc: dict | None, design: dict | None, timing: str = "A") -> dict:
    """Return {rule: {'value','kind','limit','tag','ok'}}. Uses build_params so it sees exactly what the kernel sees."""
    from cd70.params import build_params  # local import: params imports engine only

    u = {**UNC_NOMINAL, **(unc or {})}
    d = {**DESIGN_BASELINE, **(design or {})}
    p = build_params(u, d, None, timing)
    area = 0.25 * math.pi * p["bore_m"] ** 2
    vd = area * p["stroke_m"]
    vc0 = vd / (DESIGN_BASELINE["cr"] - 1.0)
    vc = vd / (d["cr"] - 1.0)
    skim = (vc0 - vc) / area * 1e3
    deck = vc / area  # clearance height at TDC, m
    r = 0.5 * p["stroke_m"]
    gap = 1e9
    for k in range(-160, 161):  # -80..+80 degrees about TDC, 0.5 deg steps
        th = 0.5 * k
        lift = max(K.valve_lift(th, p["iv_open_deg"], p["iv_dur_deg"], p["lift_in_m"], p["clearance_m"]),
                   K.valve_lift(th, p["ev_open_deg"], p["ev_dur_deg"], p["lift_ex_m"], p["clearance_m"]))
        gap = min(gap, (deck + K.piston_x(th, r, p["conrod_m"]) - lift) * 1e3)
    ign = (p["ign_low_deg"], p["ign_4000_deg"], p["ign_above_deg"])
    fm = p["fuel_mult_main"]
    vals = {
        "head_skim_mm": skim,
        "valve_piston_gap_mm": gap,
        "valve_accel_ratio": 1.0 / (d["cam_dur_scale"] ** 2),
        "overlap_deg": _both_open_deg(p),
        "head_in_over_bore": p["head_in_m"] / p["bore_m"],
        "ign_adv_max_deg": max(ign),
        "ign_adv_min_deg": min(ign),
        "lambda_wot_eff": p["lambda_wot"] / fm,
        "lambda_wot_rich": p["lambda_wot"] / fm,
    }
    return _judge(vals, DESIGN_LIMITS)


def plausibility(row: dict, cr: float = 9.3) -> dict:
    """Result-level physics check on one evaluate_design() row."""
    ideal = 1.0 - cr ** (1.0 - 1.35)
    bs = row.get("bsfc_min_gkwh", float("nan"))
    eta_b = 3.6e9 / (bs * LHV_J_KG) if bs == bs and bs > 0 else float("nan")
    vals = {
        "bsfc_min_gkwh": bs,
        "ve_max": row.get("ve_max", float("nan")),
        "p_peak_hp": row.get("p_peak_kw", float("nan")) * 1000.0 / 745.7,
        "t_peak_nm": row.get("t_peak_nm", float("nan")),
        "t_peak_nm_min": row.get("t_peak_nm", float("nan")),
        "eta_brake_over_otto": eta_b / ideal if eta_b == eta_b else float("nan"),
        "converged": row.get("all_converged", 0.0),
    }
    return _judge(vals, RESULT_LIMITS)


def _judge(vals: dict, limits: dict) -> dict:
    out = {}
    for k, (kind, lim, tag, _doc) in limits.items():
        v = vals[k]
        ok = (v == v) and ((v <= lim) if kind == "max" else (v >= lim))
        out[k] = {"value": float(v), "kind": kind, "limit": lim, "tag": tag, "ok": bool(ok)}
    return out


def all_ok(result: dict) -> bool:
    return all(v["ok"] for v in result.values())


def failed(result: dict) -> list:
    return [k for k, v in result.items() if not v["ok"]]


__all__ = ["design_rules", "plausibility", "all_ok", "failed", "valve_angles", "DESIGN_LIMITS", "RESULT_LIMITS"]
