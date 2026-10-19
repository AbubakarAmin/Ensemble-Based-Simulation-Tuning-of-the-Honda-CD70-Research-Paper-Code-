"""v15: the optimiser objective is the city cycle; steady cruise is kept as a diagnostic."""
import math

from cd70 import cycle, study
from cd70.evaluate import evaluate_design
from cd70.objective import FUEL_KEY, FUEL_LABEL


def test_objective_is_city_cycle_from_config():
    assert FUEL_KEY == "f2_city_l100km"
    assert "city" in FUEL_LABEL


def test_evaluate_reports_city_and_cruise_and_they_are_consistent():
    r = evaluate_design(None, None, None, "B")
    assert math.isfinite(r["f2_city_l100km"]) and math.isfinite(r["f2_cruise_l100km"])
    direct = cycle.city_cycle(None, "B")["l_100km"]
    assert abs(r["f2_city_l100km"] - direct) < 1e-9
    assert abs(r["f2_city_l100km"] - (r["f2_city_cruise_l100km"] + r["f2_city_accel_l100km"])) < 1e-9


def test_feasibility_uses_the_objective_metric():
    row = study.eval_checked(study.flat_row(timing="B"))
    assert math.isfinite(row[FUEL_KEY])
    assert row["feasible"] == 1.0
