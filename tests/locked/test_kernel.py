"""LOCKED verification tests for the engine kernel. The agent must not edit this file (gates check its hash).

These tests do not depend on calibration. They check that the equations are coded correctly.
"""

import math

import numpy as np
import pytest

from cd70 import kernel as K
from cd70.engine import engine_point, nominal_params, valve_angles


def _closed_params(**over):
    """Textbook case: constant gamma 1.4, no wall heat, intake closes at BDC, exhaust opens at BDC."""
    p = nominal_params("A")
    iv_open, iv_dur, ev_open, ev_dur = valve_angles(0, 0, 0, 0)
    p.update(
        iv_open_deg=iv_open, iv_dur_deg=iv_dur, ev_open_deg=ev_open, ev_dur_deg=ev_dur,
        clearance_m=0.0, const_gamma=1.4, wall_on=0.0, leak_area_m2=0.0,
    )
    p.update(over)
    return p


def test_geometry_numbers():
    p = nominal_params("A")
    ap = 0.25 * math.pi * p["bore_m"] ** 2
    vd = ap * p["stroke_m"]
    vc = vd / (p["cr"] - 1.0)
    assert vd * 1e6 == pytest.approx(71.83, abs=0.02)
    assert vc * 1e6 == pytest.approx(8.65, abs=0.02)
    r = p["stroke_m"] / 2
    x_bdc = K.piston_x(180.0, r, p["conrod_m"])
    assert x_bdc == pytest.approx(p["stroke_m"], abs=1e-9)
    assert K.piston_x(0.0, r, p["conrod_m"]) == pytest.approx(0.0, abs=1e-12)
    assert K.piston_x(360.0, r, p["conrod_m"]) == pytest.approx(0.0, abs=1e-12)
    assert 2 * p["stroke_m"] * 7500 / 60 == pytest.approx(10.35, abs=0.01)
    # slope check by finite difference
    th = 70.0
    fd = (K.piston_x(th + 1e-3, r, p["conrod_m"]) - K.piston_x(th - 1e-3, r, p["conrod_m"])) / 2e-3
    assert K.piston_dx(th, r, p["conrod_m"]) == pytest.approx(fd, rel=1e-6)


def test_valve_timing_scenarios():
    iv_open, iv_dur, ev_open, ev_dur = valve_angles(0, 20, 20, 0)
    assert (iv_open, iv_dur, ev_open, ev_dur) == (0.0, 200.0, 520.0, 200.0)  # overlap 0
    a = nominal_params("B")
    assert a["iv_dur_deg"] == pytest.approx(240.0)
    assert a["ev_dur_deg"] == pytest.approx(240.0)
    # overlap in B: exhaust closes 20 after TDC, intake opens 20 before TDC -> 40 deg
    assert a["iv_open_deg"] == pytest.approx(700.0)
    assert (a["ev_open_deg"] + a["ev_dur_deg"]) % 720.0 == pytest.approx(20.0)
    # shifts move events later (positive) and duration scale keeps the centre
    s_open, s_dur, _, _ = valve_angles(0, 20, 20, 0, int_shift=5.0, dur_scale=1.1)
    assert s_dur == pytest.approx(220.0)
    assert (s_open + 0.5 * s_dur) % 720.0 == pytest.approx(105.0)


def test_valve_lift_and_area():
    assert K.valve_lift(100.0, 0.0, 200.0, 0.0065, 0.0) == pytest.approx(0.0065)
    assert K.valve_lift(250.0, 0.0, 200.0, 0.0065, 0.0) == 0.0
    assert K.valve_lift(710.0, 700.0, 240.0, 0.0065, 0.0) > 0.0  # wraps through TDC
    a_small = K.valve_area(0.001, 0.025, 0.00498)
    assert a_small == pytest.approx(math.pi * 0.025 * 0.001)
    a_big = K.valve_area(0.01, 0.025, 0.00498)
    assert a_big == pytest.approx(0.25 * math.pi * ((0.92 * 0.025) ** 2 - 0.00498**2))


def test_ignition_map():
    assert K.spark_adv(1000.0, 20.0, 35.0, 36.0) == 20.0
    assert K.spark_adv(1500.0, 20.0, 35.0, 36.0) == 20.0
    assert K.spark_adv(2750.0, 20.0, 35.0, 36.0) == pytest.approx(27.5)
    assert K.spark_adv(4000.0, 20.0, 35.0, 36.0) == pytest.approx(35.0)
    assert K.spark_adv(4500.0, 20.0, 35.0, 36.0) == pytest.approx(35.5)
    assert K.spark_adv(7000.0, 20.0, 35.0, 36.0) == 36.0


def test_wiebe_function():
    xb0, d0 = K.wiebe(100.0, 360.0, 60.0, 2.0)
    assert xb0 == 0.0 and d0 == 0.0
    xb_end, _ = K.wiebe(420.0, 360.0, 60.0, 2.0)
    assert xb_end == pytest.approx(1.0 - math.exp(-6.908))
    # derivative matches finite difference and the integral of the rate gives xb
    th = np.linspace(360.0, 420.0, 6001)
    rate = np.array([K.wiebe(t, 360.0, 60.0, 2.0)[1] for t in th])
    assert np.trapezoid(rate, th) == pytest.approx(1.0 - math.exp(-6.908), abs=1e-4)


def test_motoring_is_isentropic():
    """No burn, no wall heat, constant gamma: p V^gamma is constant between valve closing and opening."""
    p = _closed_params(burn_on=0.0, fuel_on=0.0)
    r = engine_point(3000.0, 1.0, p, with_trace=True)
    tr = r["trace"]
    sel = (tr["th"] > 182.0) & (tr["th"] < 538.0)
    inv = tr["p"][sel] * tr["V"][sel] ** 1.4
    assert (inv.max() - inv.min()) / inv.mean() < 0.005
    assert r["converged"] == 1.0


def test_otto_efficiency():
    """Instant heat release at TDC, constant gamma 1.4, no wall heat: gross efficiency = 1 - CR^(1-gamma)."""
    p = _closed_params(
        lambda_wot=1.0, eta_comb=1.0, burn_dur_deg=2.0, spark_delay_deg=0.0,
        ign_low_deg=0.0, ign_4000_deg=0.0, ign_above_deg=0.0, dth_deg=0.05, max_cycles=6.0,
    )
    r = engine_point(3000.0, 1.0, p)
    w_gross = r["imep_gross_bar"] * 1e5 * r["vd_m3"]
    eta = w_gross / r["qc_j"]
    ideal = 1.0 - p["cr"] ** (1.0 - 1.4)
    assert eta == pytest.approx(ideal, rel=0.015)


def test_energy_closure():
    r = engine_point(5500.0, 1.0, nominal_params("A"))
    assert abs(r["energy_resid_j"]) < 0.005 * r["qc_j"]


def test_mass_balance():
    r = engine_point(5500.0, 1.0, nominal_params("A"))
    assert abs(r["dm_sys_kg"] - (r["m_in_kg"] - r["m_out_kg"] - r["m_leak_kg"])) < 1e-9
    r = engine_point(5500.0, 1.0, nominal_params("B"))
    assert abs(r["dm_sys_kg"] - (r["m_in_kg"] - r["m_out_kg"] - r["m_leak_kg"])) < 1e-9
    assert r["m_leak_kg"] > 0.0


def test_step_size_independence():
    base = nominal_params("A")
    a = engine_point(4000.0, 1.0, {**base, "dth_deg": 0.5})
    b = engine_point(4000.0, 1.0, {**base, "dth_deg": 0.25})
    assert a["imep_net_bar"] == pytest.approx(b["imep_net_bar"], rel=0.005)
    assert a["pmax_bar"] == pytest.approx(b["pmax_bar"], rel=0.01)


def test_knock_scaling_laws():
    base = nominal_params("A")
    r1 = engine_point(4000.0, 1.0, base)
    r2 = engine_point(4000.0, 1.0, {**base, "knock_k": 2.0})
    r3 = engine_point(4000.0, 1.0, {**base, "ron": 92.0})
    assert r2["ki_end"] == pytest.approx(r1["ki_end"] / 2.0, rel=1e-9)
    assert r3["ki_end"] == pytest.approx(r1["ki_end"] * (92.0 / 87.0) ** -3.402, rel=1e-9)
    assert r1["ki_end"] > 0.0


def test_spark_advance_has_interior_optimum():
    base = nominal_params("A")
    adv = np.arange(5.0, 50.0, 5.0)
    tq = []
    for a in adv:
        q = {**base, "ign_low_deg": a, "ign_4000_deg": a, "ign_above_deg": a}
        tq.append(engine_point(3000.0, 1.0, q)["torque_nm"])
    i = int(np.argmax(tq))
    assert 0 < i < len(adv) - 1


def test_throttle_monotonic_and_no_nan_grid():
    base = nominal_params("A")
    last = -1e9
    for alpha in (0.1, 0.2, 0.4, 0.6, 0.8, 1.0):
        t = engine_point(4000.0, alpha, base)["torque_nm"]
        assert t > last
        last = t
    for scen in ("A", "B"):
        for rpm in (1500.0, 3000.0, 5500.0, 7500.0):
            for alpha in (0.05, 0.3, 1.0):
                r = engine_point(rpm, alpha, nominal_params(scen))
                vals = [r[k] for k in ("imep_net_bar", "pmax_bar", "ve_air", "ki_end")]
                assert all(np.isfinite(v) for v in vals)
                assert r["converged"] == 1.0, (scen, rpm, alpha)


def test_nominal_regression_ranges():
    """Wide ranges that lock the kernel behaviour. A change that breaks these is a bug in the kernel."""
    base = nominal_params("A")
    r55 = engine_point(5500.0, 1.0, base)
    r75 = engine_point(7500.0, 1.0, base)
    assert 4.0 < r55["torque_nm"] < 5.6
    assert 4.0 < r75["power_hp"] < 5.4
    assert 0.65 < r75["ve_air"] < 0.95
    assert 38.0 < r55["pmax_bar"] < 70.0
    assert 330.0 < r55["th_pmax_deg"] - 360.0 + 360.0 < 400.0
    assert 250.0 < r55["bsfc_gkwh"] < 380.0
