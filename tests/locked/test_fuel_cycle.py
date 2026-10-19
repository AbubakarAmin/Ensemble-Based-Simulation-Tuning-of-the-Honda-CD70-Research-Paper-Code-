"""v14 tests for the city cycle, run-in scenario, gearing diagnostic and the pre-declared agreement rule."""
import math

from cd70 import config, cycle
from cd70.evaluate import evaluate_design


def test_verdict_rule_is_pre_declared_and_correct():
    assert cycle.verdict(40, 50, 60, 50, 55, 0.2) == "AGREE"           # inside [40, 66]
    assert cycle.verdict(80, 89, 104, 50, 55, 0.2) == "MODEL HIGHER THAN PUBLISHED"
    assert cycle.verdict(20, 25, 30, 50, 55, 0.2) == "MODEL LOWER THAN PUBLISHED"
    assert cycle.verdict(float("nan"), float("nan"), float("nan"), 50, 55, 0.2) == "NOT AVAILABLE"


def test_city_cycle_more_idle_means_less_km_per_litre():
    low = cycle.city_cycle(None, "B", idle_share=0.10)["km_per_l"]
    high = cycle.city_cycle(None, "B", idle_share=0.30)["km_per_l"]
    assert math.isfinite(low) and math.isfinite(high)
    assert high < low


def test_city_cycle_is_plausible_for_nominal_engine():
    km_l = cycle.city_cycle(None, "B")["km_per_l"]
    assert 20.0 < km_l < 150.0, km_l


def test_runin_friction_increases_fuel_use():
    base = cycle.city_cycle(None, "B")["km_per_l"]
    runin = cycle.city_cycle(cycle.runin_unc(None), "B")["km_per_l"]
    assert runin < base


def test_locked_evaluation_is_unchanged_by_v14():
    # evaluate_design must keep returning the same keys it did in v12 (v14 adds nothing to it)
    r = evaluate_design(None, None, None, "B")
    assert "l100_40" in r and "l100_50" in r and "rpm_cruise_50" in r
    assert "city_km_per_l" not in r


def test_gearing_diagnostic_matches_sheet_note():
    g = cycle.gearing_check()
    assert 65.0 < g["kmh_at_7500_rpm"] < 73.0  # sheet note: about 69 km/h at 7,500 rpm in 4th gear
    assert g["rpm_30"] < g["rpm_40"] < g["rpm_50"]


def test_validation_config_declares_assumptions():
    v = config.validation()
    assert abs(sum(ph["time_share"] for ph in v["city_cycle"]["phases"]) - 1.0) < 1e-9
    assert v["runin"]["fmep_factor"] > 1.0


def test_acceleration_term_lowers_km_per_litre():
    res = cycle.city_cycle(None, "B")
    assert res["accel_l_100km"] > 0.0
    assert abs(res["l_100km"] - (res["cruise_l_100km"] + res["accel_l_100km"])) < 1e-9
