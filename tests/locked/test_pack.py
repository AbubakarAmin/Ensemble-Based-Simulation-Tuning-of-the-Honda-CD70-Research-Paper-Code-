"""Tests of vehicle, rules, config, runner, analysis. LOCKED."""
import math
from pathlib import Path

import numpy as np
import pytest

from cd70 import analysis, config, rules, study
from cd70 import vehicle as V
from cd70.objective import FUEL_KEY
from cd70.params import DESIGN_BASELINE, UNC_NOMINAL
from cd70.runner import run_batch

ROOT = Path(__file__).resolve().parents[2]


def test_overall_ratios():
    assert V.overall_ratio(1) == pytest.approx(35.67, abs=0.02)
    assert V.overall_ratio(4) == pytest.approx(11.37, abs=0.02)


def test_road_load_power():
    assert V.road_load_engine_power_hp(70.0) == pytest.approx(4.27, abs=0.05)
    assert V.road_load_engine_power_hp(75.0) == pytest.approx(5.10, abs=0.06)
    assert V.road_load_engine_power_hp(80.0) == pytest.approx(6.04, abs=0.06)


def test_priors_match_params():
    assert set(config.uncertain_names()) == set(UNC_NOMINAL)
    for k, v in config.nominal_unc().items():
        assert v == pytest.approx(UNC_NOMINAL[k])
    assert config.baseline_design() == pytest.approx(DESIGN_BASELINE)
    assert len(config.uncertain_names()) == 38 and len(config.design_names()) == 8


def test_spec_numbers_present_in_sheet():
    txt = (ROOT / "docs" / "spec_sheet_v11.md").read_text(encoding="utf-8")
    for s in ("47.0 × 41.4", "9.3 : 1", "12.7 bar", "5.05 hp", "3.722"):
        assert s in txt, s


def test_unit_mapping_bounds():
    u = np.random.default_rng(0).random((50, 38))
    spec = {d["name"]: d for d in config.priors()["uncertain"]}
    for row in config.unit_to_unc(u):
        for k, v in row.items():
            s = spec[k]
            lo, hi = (s["low"], s["high"]) if s["dist"] != "discrete" else (min(s["values"]), max(s["values"]))
            assert lo - 1e-9 <= v <= hi + 1e-9
    d = config.unit_to_design(np.random.default_rng(1).random((20, 8)))
    assert all(float(x["main_jet_delta"]).is_integer() for x in d)


def test_baseline_passes_rules_and_plausibility():
    from cd70.evaluate import evaluate_design
    for t in "AB":
        assert rules.all_ok(rules.design_rules(None, None, t))
        assert rules.all_ok(rules.plausibility(evaluate_design(timing=t)))


def test_rules_can_fail():
    r = rules.design_rules(None, {"cam_dur_scale": 0.9}, "A")
    assert "valve_accel_ratio" in rules.failed(r)
    r = rules.design_rules(None, {"cam_dur_scale": 1.15, "int_shift_deg": -12, "exh_shift_deg": 12}, "B")
    assert "overlap_deg" in rules.failed(r)
    r = rules.design_rules(None, {"main_jet_delta": -8}, "A")
    assert "lambda_wot_eff" in rules.failed(r)


def test_eval_checked_baseline_feasible():
    r = study.eval_checked(study.flat_row(timing="B"))
    assert r["feasible"] == 1.0 and r["g_knock"] < 0.0 and math.isfinite(r[FUEL_KEY])


def test_cruise_solution_is_consistent():
    from cd70.evaluate import evaluate_design
    r = evaluate_design(timing="B")
    assert 0.0 < r["alpha_40"] < 0.2
    assert 0.5 < r["l100_40"] < 4.0


def test_runner_parallel_equals_serial_and_resumes(tmp_path):
    rows = [study.flat_row(design={"cr": 9.0 + 0.1 * i}, timing="B", i=i) for i in range(6)]
    a = run_batch("cd70.study:eval_checked", rows, tmp_path / "a", chunk=3, n_jobs=2, progress=False)
    b = run_batch("cd70.study:eval_checked", rows, tmp_path / "b", chunk=3, n_jobs=1, progress=False)
    assert np.allclose(a["f1_torque_wot_mean_nm"], b["f1_torque_wot_mean_nm"])
    (tmp_path / "a" / "part_00001.parquet").unlink()
    c = run_batch("cd70.study:eval_checked", rows, tmp_path / "a", chunk=3, n_jobs=2, progress=False)
    assert len(c) == 6


def test_runner_captures_errors(tmp_path):
    r = run_batch("cd70.study:eval_checked", [study.flat_row(design={"cr": float("nan")}, timing="B")], tmp_path, chunk=1, n_jobs=1, progress=False)
    assert len(r) == 1


def test_pareto_and_hypervolume():
    F = np.array([[-1.0, 1.0], [-1.1, 1.05], [-0.9, 1.1], [-1.05, 0.99], [-0.95, 1.02]])
    m = analysis.pareto_mask(F)
    assert m.tolist() == [False, True, False, True, False]
    assert analysis.hypervolume(F[m]) > 0
    assert analysis.hypervolume(np.empty((0, 2))) == 0.0


def test_claim_levels():
    rng = np.random.default_rng(0)
    assert analysis.claim_level(rng.normal(3.0, 0.5, 200)).startswith("CLAIM")
    assert analysis.claim_level(rng.normal(0.0, 1.0, 200)).startswith("NOT")
    assert analysis.claim_level(rng.normal(3.0, 0.5, 10)).startswith("NOT")


def test_invalid_variations_are_flagged_not_accepted():
    r = study.eval_checked(study.flat_row(design={"cr": 10.5, "cam_dur_scale": 0.9, "int_shift_deg": -12, "exh_shift_deg": 12, "main_jet_delta": -8}, timing="B"))
    assert r["feasible"] == 0.0
    assert r["rules_failed"] != ""


def test_top_speed_uses_overspeed_and_road_load_priors():
    from cd70.evaluate import evaluate_design
    a = evaluate_design(unc={"cda_m2": 0.30}, timing="B")
    b = evaluate_design(unc={"cda_m2": 0.50}, timing="B")
    assert a["v_top_kmh"] > b["v_top_kmh"] > 60.0
    assert a["v_top_indicated_kmh"] >= a["v_top_kmh"]
    assert a["p_9500_hp"] > 0.0


def test_calibration_metrics_include_top_speed_and_crank_speed():
    m = study.cal_metrics(study.flat_row(unc={"crank_rpm": 1000.0}, timing="B"))
    m2 = study.cal_metrics(study.flat_row(unc={"crank_rpm": 400.0}, timing="B"))
    assert m["cranking_bar"] > m2["cranking_bar"] > 5.0
    assert 50.0 < m["v_top_true_kmh"] < 110.0
