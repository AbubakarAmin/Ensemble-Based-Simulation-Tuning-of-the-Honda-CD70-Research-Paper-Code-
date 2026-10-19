"""Map the 31 uncertain inputs, the 8 design variables and the scenario onto kernel parameters.

LOCKED FILE for the agent: do not edit unless a task says so. This file IS the definition of what each
name in config/priors.yaml means physically.
"""

from __future__ import annotations

from cd70.engine import ambient_pressure, engine_point, nominal_params, valve_angles

# Nominal (spec sheet v10 baseline) values of the 31 uncertain inputs. Calibration parameters use mid-range guesses.
UNC_NOMINAL = {
    "burn_dur_deg": 60.0, "wiebe_m": 2.0, "spark_delay_deg": 10.0, "eta_comb": 0.95, "cd_scale": 0.70,
    "lambda_wot": 0.90, "lambda_cruise": 1.00, "fmep_scale": 1.0, "t_wall_offset_k": 0.0,
    "v_intake_cm3": 100.0, "muffler_area_mm2": 100.0, "leak_area_mm2": 0.15, "charge_heat_k": 30.0, "knock_margin_base": 0.85,
    "valve_lift_mm": 6.5, "io_off": 0.0, "ic_off": 0.0, "eo_off": 0.0, "ec_off": 0.0,
    "valve_clearance_mm": 0.09, "conrod_mm": 91.0, "head_in_mm": 25.0, "head_ex_mm": 21.9,
    "venturi_mm": 18.0, "main_jet_true": 78.0, "slow_jet_true": 38.0,
    "ign_low_true": 20.0, "ign_high_true": 35.0, "ign_above_true": 35.0,
    "gear_scale": 1.0, "primary": 3.722, "rolling_radius_m": 0.279,
    "cda_m2": 0.45, "crr": 0.020, "drive_eff": 0.86, "mass_kg": 155.0,
    "speedo_overread": 0.05, "crank_rpm": 600.0,
}

DESIGN_BASELINE = {
    "cr": 9.3, "d_ign_low_deg": 0.0, "d_ign_high_deg": 0.0, "main_jet_delta": 0.0,
    "int_shift_deg": 0.0, "exh_shift_deg": 0.0, "cam_dur_scale": 1.0, "int_valve_scale": 1.0,
}

SCENARIO_CAL = {"ron": 87.0, "t_amb_c": 35.0, "alt_m": 0.0}  # conditions at which calibration targets apply


def build_params(unc: dict | None = None, design: dict | None = None, scen: dict | None = None,
                 timing: str = "A") -> dict:
    """Return kernel parameters (SI) for one engine configuration."""
    u = {**UNC_NOMINAL, **(unc or {})}
    d = {**DESIGN_BASELINE, **(design or {})}
    s = {**SCENARIO_CAL, **(scen or {})}
    p = nominal_params("A")
    extra = 20.0 if timing.upper() == "B" else 0.0
    iv_open, iv_dur, ev_open, ev_dur = valve_angles(
        0.0 + extra + u["io_off"], 20.0 + extra + u["ic_off"], 20.0 + extra + u["eo_off"], 0.0 + extra + u["ec_off"],
        int_shift=d["int_shift_deg"], exh_shift=d["exh_shift_deg"], dur_scale=d["cam_dur_scale"],
    )
    fm_main = ((u["main_jet_true"] + d["main_jet_delta"]) / u["main_jet_true"]) ** 2
    p.update(
        cr=d["cr"], conrod_m=u["conrod_mm"] * 1e-3,
        iv_open_deg=iv_open, iv_dur_deg=iv_dur, ev_open_deg=ev_open, ev_dur_deg=ev_dur,
        lift_in_m=u["valve_lift_mm"] * 1e-3, lift_ex_m=u["valve_lift_mm"] * 1e-3,
        clearance_m=u["valve_clearance_mm"] * 1e-3,
        head_in_m=u["head_in_mm"] * 1e-3 * d["int_valve_scale"], head_ex_m=u["head_ex_mm"] * 1e-3,
        stem_in_m=0.00498, stem_ex_m=0.00496, cd_valve=u["cd_scale"],
        venturi_m=u["venturi_mm"] * 1e-3, muffler_area_m2=u["muffler_area_mm2"] * 1e-6,
        v_intake_m3=u["v_intake_cm3"] * 1e-6, leak_area_m2=u["leak_area_mm2"] * 1e-6,
        lambda_wot=u["lambda_wot"], lambda_cruise=u["lambda_cruise"], fuel_mult_main=fm_main,
        charge_heat_k=u["charge_heat_k"],
        ign_low_deg=u["ign_low_true"] + d["d_ign_low_deg"],
        ign_4000_deg=u["ign_high_true"] + d["d_ign_high_deg"],
        ign_above_deg=u["ign_above_true"] + d["d_ign_high_deg"],
        burn_dur_deg=u["burn_dur_deg"], wiebe_m=u["wiebe_m"], spark_delay_deg=u["spark_delay_deg"],
        eta_comb=u["eta_comb"], fmep_scale=u["fmep_scale"], t_wall_offset_k=u["t_wall_offset_k"],
        knock_k=u.get("knock_k", 1.0), ron=s["ron"],
        t_amb_k=s["t_amb_c"] + 273.15, p_amb_pa=ambient_pressure(s["alt_m"]),
    )
    return p


def knock_k_from_margin(unc: dict, timing: str, margin: float,
                        rpms=(2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500)) -> float:
    """knock_k so that the BASELINE engine at calibration conditions has max KI = margin over the WOT sweep.

    KI is a diagnostic only (it does not feed back into the cycle), so KI scales exactly as 1/knock_k.
    """
    p = build_params({**unc, "knock_k": 1.0}, None, SCENARIO_CAL, timing)
    ki_max = max(engine_point(r, 1.0, p)["ki_end"] for r in rpms)
    return ki_max / margin
