"""Is the CD70 specification physically possible?  16 checks. Writes reports/feasibility_report.md and .json.
Engine-dependent checks use the NOMINAL (uncalibrated) model; the calibrated version of the main question
(can 5.05 hp at 7500 rpm exist?) is answered by the calibration stage.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import rules  # noqa: E402
from cd70 import vehicle as V
from cd70.engine import ambient_pressure  # noqa: E402
from cd70.evaluate import evaluate_design  # noqa: E402
from cd70.params import build_params  # noqa: E402

# Values quoted from docs/spec_sheet_v11.md
BORE, STROKE, CR, ROD = 47.0, 41.4, 9.3, 91.0
HP, RPM_HP, NM, RPM_NM = 5.05, 7500.0, 5.0, 5500.0
VD = math.pi / 4 * (BORE / 10) ** 2 * (STROKE / 10)  # cm3
checks = []


def add(i, name, value, rule, verdict, note=""):
    checks.append({"id": i, "name": name, "value": value, "rule": rule, "verdict": verdict, "note": note})


def band(v, ok_lo, ok_hi, edge_lo=None, edge_hi=None):
    if ok_lo <= v <= ok_hi:
        return "PASS"
    if edge_lo is not None and edge_lo <= v <= edge_hi:
        return "EDGE"
    return "FAIL"


add(1, "Displacement from bore x stroke (cm3)", round(VD, 2), "within 1% of the quoted 72 cc", band(VD, 71.28, 72.72))
add(2, "Bore / stroke", round(BORE / STROKE, 3), "0.8 to 1.3 for a motorcycle engine", band(BORE / STROKE, 0.8, 1.3))
add(3, "Rod / crank-radius ratio", round(ROD / (STROKE / 2), 2), "3.2 to 4.8", band(ROD / (STROKE / 2), 3.2, 4.8, 2.8, 5.5))
sp = 2 * STROKE / 1000 * RPM_HP / 60
add(4, "Mean piston speed at 7500 rpm (m/s)", round(sp, 2), "below 18 m/s for a production road engine", band(sp, 0, 18, 0, 22))
vc = VD / (CR - 1)
add(5, "Clearance volume (cm3)", round(vc, 2), "positive, equals 8.66 cc in the sheet", band(vc, 8.60, 8.72))
p = build_params(None, None, None, "A")
add(6, "Intake valve head / bore", round(p["head_in_m"] / p["bore_m"], 3), "<= 0.58 (must fit the head)", band(p["head_in_m"] / p["bore_m"], 0, 0.58, 0, 0.62))
add(7, "Valve lift / head diameter", round(p["lift_in_m"] / p["head_in_m"], 3), "0.22 to 0.32 (typical)", band(p["lift_in_m"] / p["head_in_m"], 0.22, 0.32, 0.18, 0.36))
a_valve = p["cd_valve"] * math.pi * p["head_in_m"] * p["lift_in_m"]
a_pist = math.pi / 4 * p["bore_m"] ** 2
z = a_pist * sp * 1.5 / (a_valve * 350.0)  # Mach-index style: mean piston speed * 1.5 peak factor over valve flow
add(8, "Intake Mach index at 7500 rpm", round(z, 3), "below 0.6 (flow not choked at peak lift)", band(z, 0, 0.6, 0, 0.75))
rho = ambient_pressure(0.0) / (287.0 * 308.15)
mdot_need = rho * VD * 1e-6 * 0.85 * RPM_HP / 120
a_vent = math.pi / 4 * 0.018 ** 2 * 0.8
mdot_cap = a_vent * ambient_pressure(0.0) * math.sqrt(1.35 / (287.0 * 308.15)) * (2 / 2.35) ** (2.35 / 0.7)
add(9, "Venturi air capacity / engine air demand at 7500 rpm", round(mdot_cap / mdot_need, 2), "> 1.0 (carburettor can pass the air)", band(mdot_cap / mdot_need, 1.0, 99, 0.85, 1.0))
bmep55 = NM * 4 * math.pi / (VD * 1e-6) / 1e5
add(10, "BMEP implied by 5.0 Nm at 5500 rpm (bar)", round(bmep55, 2), "6 to 11 for a carbureted NA small engine", band(bmep55, 6, 11, 5, 12.5))
t75 = HP * 745.7 / (2 * math.pi * RPM_HP / 60)
add(11, "Torque implied by 5.05 hp at 7500 rpm (Nm)", round(t75, 2), "within -25% to +5% of the 5.0 Nm at 5500", band(t75 / NM, 0.75, 1.05, 0.6, 1.15))
sp_hp = HP / (VD / 1000)
add(12, "Specific power (hp/L)", round(sp_hp, 1), "30 to 90 for a small air-cooled 4-stroke", band(sp_hp, 30, 90, 20, 110))
req = HP * 745.7 * 3.6e6  # W*3.6e6 -> use air flow estimate
air_kg_s = rho * VD * 1e-6 * 0.85 * RPM_HP / 120
fuel_kg_s = air_kg_s / (14.7 * 0.9)
eta_b = HP * 745.7 / (fuel_kg_s * 44e6)
add(13, "Brake efficiency needed for 5.05 hp at VE 0.85, lambda 0.9", round(eta_b, 3), "0.18 to 0.33", band(eta_b, 0.18, 0.33, 0.15, 0.37))
ideal = 1 - CR ** (1 - 1.35)
add(14, "Needed brake efficiency / ideal Otto efficiency", round(eta_b / ideal, 3), "below 0.6", band(eta_b / ideal, 0, 0.6, 0, 0.75))
for tm in ("A", "B"):
    pass
ratio4 = V.overall_ratio(4)
v7500 = V.speed_at_rpm(7500.0, ratio4)
rpm_need = V.rpm_at_speed(85.0, ratio4)
add(15, "Engine speed needed for 85 km/h true (middle of 80-90) in 4th (rpm)", round(rpm_need), "below 10000 rpm (above the 7500 rpm power point: needs over-rev)",
    "PASS" if rpm_need <= 9500 else ("EDGE" if rpm_need <= 10200 else "FAIL"),
    f"stock CD70 real-world top speed is 80-90 km/h; 4th gear gives {v7500:.0f} km/h at 7500 rpm and {V.speed_at_rpm(9500.0, ratio4):.0f} km/h at 9500 rpm; "
    "the model is calibrated so true top speed 80-90 km/h is reached with power extrapolated to 9500 rpm")
hp_need = V.road_load_engine_power_hp(85.0, cda=0.33)
add(16, "Road-load engine power at 85 km/h with CdA 0.33 (tucked rider) (hp)", round(hp_need, 2), "within the 5.05-5.8 hp the engine makes between 7500 and 9500 rpm", band(hp_need, 0, 5.8, 0, 6.4))
rows = {}
for tm in ("A", "B"):
    r = evaluate_design(timing=tm)
    rows[tm] = {k: r[k] for k in ("p_peak_kw", "t_peak_nm", "ve_max", "bsfc_min_gkwh", "ki_max", "p_cyl_max_bar")}
    pl = rules.plausibility(r)
    rows[tm]["plausibility_failed"] = rules.failed(pl)
    rows[tm]["design_rules_failed"] = rules.failed(rules.design_rules(None, None, tm))
fails = [c for c in checks if c["verdict"] == "FAIL"]
edges = [c for c in checks if c["verdict"] == "EDGE"]
verdict = "FAIL" if fails else ("PASS WITH EDGES" if edges else "PASS")
out = {"verdict": verdict, "checks": checks, "nominal_model": rows}
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "feasibility_report.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
md = ["# Feasibility report (spec sheet v10)", "", f"**Verdict: {verdict}**", "",
      "| # | Check | Value | Rule | Verdict |", "|---|---|---|---|---|"]
md += [f"| {c['id']} | {c['name']} | {c['value']} | {c['rule']} | {c['verdict']} |" for c in checks]
md += ["", "## Nominal (uncalibrated) model, both valve-timing readings", "", "```", json.dumps(rows, indent=1), "```"]
(ROOT / "reports" / "feasibility_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"verdict {verdict}: {len(fails)} FAIL, {len(edges)} EDGE of {len(checks)}")
for c in checks:
    if c["verdict"] != "PASS":
        print(" ", c["id"], c["name"], c["value"], c["verdict"])
sys.exit(1 if fails else 0)
