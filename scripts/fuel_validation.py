"""v14 fuel validation. Compares the calibrated ensemble with published, owner and (if present) your own fuel figures.

  python scripts/fuel_validation.py            (long job, about 5 to 15 minutes for 60 engines; run it through scripts/jobs.py)
  (--n N is for testing only; the real run uses the default of 60)

Reads: data/processed accepted engines (via experiments.load_members), data/raw/published_fuel.csv, optional data/raw/fuel_log.csv.
Writes: reports/fuel_validation.md. Changes no calibration, optimiser or locked evaluation result.
Rules (thresholds, time shares, run-in factor) come from config/validation.yaml, fixed before results were seen.
"""

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70 import config, cycle  # noqa: E402
from cd70 import experiments as E  # noqa: E402
from cd70.evaluate import evaluate_design  # noqa: E402

N_ENGINES = 60
TIMING = "B"
BOOT_SEED = 20261015  # fixed seed for the fuel-log bootstrap (stated in the report)


def model_rows(members):
    rows = {"steady40": [], "steady50": [], "rpm50": [], "city": [], "city_idle_low": [], "city_idle_high": [],
            "runin_steady50": [], "runin_city": []}
    for u in members:
        r = evaluate_design(u, None, None, TIMING)
        rows["steady40"].append(100.0 / r["l100_40"] if np.isfinite(r["l100_40"]) else np.nan)
        rows["steady50"].append(100.0 / r["l100_50"] if np.isfinite(r["l100_50"]) else np.nan)
        rows["rpm50"].append(r["rpm_cruise_50"])
        rows["city"].append(cycle.city_cycle(u, TIMING)["km_per_l"])
        cfg = config.validation()["city_cycle"]["idle_share_sensitivity"]
        rows["city_idle_low"].append(cycle.city_cycle(u, TIMING, idle_share=cfg[0])["km_per_l"])
        rows["city_idle_high"].append(cycle.city_cycle(u, TIMING, idle_share=cfg[1])["km_per_l"])
        ru = cycle.runin_unc(u)
        rr = evaluate_design(ru, None, None, TIMING)
        rows["runin_steady50"].append(100.0 / rr["l100_50"] if np.isfinite(rr["l100_50"]) else np.nan)
        rows["runin_city"].append(cycle.city_cycle(ru, TIMING)["km_per_l"])
    return rows


def read_fuel_log(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = [r for r in csv.DictReader(f) if r.get("km_since_last_fill") and r.get("litres_added")]
    if not data:
        return None
    km = np.array([float(r["km_since_last_fill"]) for r in data])
    lt = np.array([float(r["litres_added"]) for r in data])
    rng = np.random.default_rng(BOOT_SEED)
    boots = []
    for _ in range(2000):
        idx = rng.integers(0, len(km), len(km))
        boots.append(km[idx].sum() / lt[idx].sum())
    lo, hi = np.percentile(boots, [2.5, 97.5])
    out = {"n": len(km), "km_per_l": float(km.sum() / lt.sum()), "ci_low": float(lo), "ci_high": float(hi)}
    out["by_condition"] = {}
    for c in sorted({r["condition"] for r in data}):
        sel = [i for i, r in enumerate(data) if r["condition"] == c]
        out["by_condition"][c] = (len(sel), float(km[sel].sum() / lt[sel].sum()))
    return out


def main():
    n = N_ENGINES
    if "--n" in sys.argv:  # testing only; the real validation always uses 60 engines
        n = int(sys.argv[sys.argv.index("--n") + 1])
    members = E.load_members(TIMING, n, "full")
    if len(members) < n:
        print(f"only {len(members)} engines available; need {n}")
        return 1
    rows = model_rows(members)
    stats = {k: cycle.percentiles(v) for k, v in rows.items()}
    tol = float(config.validation()["agreement"]["tolerance"])
    gear = cycle.gearing_check()
    fuel_log = read_fuel_log(ROOT / "data" / "raw" / "fuel_log.csv")

    L = ["# Fuel validation (v14)", "",
         f"Engines: {len(members)} accepted calibrated engines, timing {TIMING}. Rules and assumptions: config/validation.yaml.",
         "Percentiles are 5th / 50th / 95th. Steady = 4th gear cruise. City = indicative cycle with an acceleration term (still likely optimistic: no braking, no cold start, no rider enrichment).",
         "", "## Model predictions (km/l)", "",
         f"- Steady 40 km/h: {stats['steady40'][0]:.1f} / {stats['steady40'][1]:.1f} / {stats['steady40'][2]:.1f}",
         f"- Steady 50 km/h: {stats['steady50'][0]:.1f} / {stats['steady50'][1]:.1f} / {stats['steady50'][2]:.1f}",
         f"- City cycle: {stats['city'][0]:.1f} / {stats['city'][1]:.1f} / {stats['city'][2]:.1f}",
         f"- City cycle, idle share {config.validation()['city_cycle']['idle_share_sensitivity'][0]}: "
         f"{stats['city_idle_low'][1]:.1f} (median)",
         f"- City cycle, idle share {config.validation()['city_cycle']['idle_share_sensitivity'][1]}: "
         f"{stats['city_idle_high'][1]:.1f} (median)",
         f"- Run-in scenario (friction x{config.validation()['runin']['fmep_factor']}), steady 50 km/h: "
         f"{stats['runin_steady50'][1]:.1f} (median); city: {stats['runin_city'][1]:.1f} (median)",
         "", "## Gearing check (diagnostic)", "",
         f"- Engine speed at 30 / 40 / 50 km/h in 4th gear with the sheet gearing: {gear['rpm_30']:.0f} / {gear['rpm_40']:.0f} / {gear['rpm_50']:.0f} rpm",
         f"- Speed in 4th gear at 7,500 rpm (rated): {gear['kmh_at_7500_rpm']:.1f} km/h; at 9,500 rpm: {gear['kmh_at_9500_rpm']:.1f} km/h",
         f"- Median engine speed at 50 km/h across the ensemble: {stats['rpm50'][1]:.0f} rpm",
         "", "## Comparison with published and owner figures", "",
         "| id | figure (km/l) | kind | model median | verdict |", "|---|---|---|---|---|"]
    verdicts = []
    model_for_kind = {"owner_city_mixed": "city", "owner_real_world": "city", "owner_mixed": "city",
                      "owner_review": "city", "city_user_table": "city", "runin_new_bike": "runin_city",
                      "runin_user_table": "runin_city", "steady_cruise_user_table": "steady50"}
    with open(ROOT / "data" / "raw" / "published_fuel.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lo, hi = float(r["figure_low_kmpl"]), float(r["figure_high_kmpl"])
            kind = r["kind"]
            if r["use_for_verdict"] != "yes":
                v = "not used for verdict (" + ("manufacturer claim" if kind == "manufacturer_claim" else r["source_quality"]) + ")"
                key = model_for_kind.get(kind, "city")
                med = stats[key][1]
            else:
                key = model_for_kind.get(kind, "city")
                med = stats[key][1]
                v = cycle.verdict(stats[key][0], med, stats[key][2], lo, hi, tol)
            verdicts.append(v)
            fig = f"{lo:g}" if lo == hi else f"{lo:g} to {hi:g}"
            L.append(f"| {r['id']} | {fig} | {kind} ({key}) | {med:.1f} | {v} |")
    L += ["", f"Agreement rule (fixed before results): AGREE if the model median is within [low x {1 - tol:.1f}, high x {1 + tol:.1f}].", ""]
    if fuel_log:
        L += ["## Your own fuel log (measured)", "",
              f"- Fill-ups: {fuel_log['n']}; overall {fuel_log['km_per_l']:.1f} km/l (95% bootstrap CI {fuel_log['ci_low']:.1f} to {fuel_log['ci_high']:.1f})."]
        for c, (n, k) in fuel_log["by_condition"].items():
            L.append(f"- Condition '{c}': {n} fill-ups, {k:.1f} km/l")
        city_key = fuel_log["by_condition"].get("city")
        if city_key:
            L.append(f"- Model city median {stats['city'][1]:.1f} km/l versus your city log {city_key[1]:.1f} km/l: "
                     f"{cycle.verdict(stats['city'][0], stats['city'][1], stats['city'][2], city_key[1], city_key[1], tol)}")
        L.append("")
    else:
        L += ["## Your own fuel log", "", "NOT AVAILABLE: data/raw/fuel_log.csv not found. Add your fill-ups (see data/raw/fuel_log_template.csv).", ""]
    n_used = sum(1 for v in verdicts if not v.startswith("not used"))
    n_agree = sum(1 for v in verdicts if v == "AGREE")
    n_high = sum(1 for v in verdicts if v.startswith("MODEL HIGHER"))
    n_low = sum(1 for v in verdicts if v.startswith("MODEL LOWER"))
    L += ["## Verdict", "",
          f"SUMMARY: of {n_used} figures used for the verdict, {n_agree} AGREE; {n_high} published figures sit BELOW the model "
          f"(model too optimistic) and {n_low} sit ABOVE it (model too pessimistic). Figures marked 'not used' are reported only.",
          "Owner reports include traffic, wind and rider style, so they are weaker evidence than a measured test. "
          "A measured fuel log (data/raw/fuel_log.csv) is the strongest check.",
          ""]
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "fuel_validation.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
