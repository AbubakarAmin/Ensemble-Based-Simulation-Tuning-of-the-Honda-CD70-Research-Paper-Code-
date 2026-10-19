# Data specification

All stored data is Parquet (pandas) or JSON, under `data/processed/` (never edit, never delete). One row = one engine evaluation.
Column prefixes: `u_` uncertain input, `d_` design variable, `s_` scenario (ron, t_amb_c, alt_m), `timing` A/B, `arm` base/design, `member` index into the accepted ensemble.
Result columns of every evaluation (src/cd70/evaluate.py + study.py): f1_torque_wot_mean_nm, f2_cruise_l100km, l100_30/40/50, alpha_30/40/50 (throttle area fraction), p_peak_kw, rpm_p_peak, t_peak_nm, rpm_t_peak, bsfc_min_gkwh, ki_max, p_cyl_max_bar, ve_7500, ve_max, t_*_nm, p_7500_hp, t_0_60_s, v_top_kmh, knock_k, rule_* values, rules_failed, plaus_failed, rules_ok, plaus_ok, g_knock, g_pmax, feasible, status, runtime_s, wall_s.
Runs are chunked into `part_#####.parquet`; an interrupted run resumes by skipping existing parts. Seeds live only in `config/seeds.yaml`.
`state/stage_done/*.done` mark finished stages. `state/STATE.json` is the task state. `paper_inputs/` is generated, `reports/` and `figures/` are outputs. `runs/smoke/` is rehearsal output (deleted in T-080).
Disk: expect about 2-4 GB in total.


## v15 result columns (added to evaluate_design)
- f2_city_l100km: city-cycle fuel use (L/100 km). The optimiser objective (FUEL_KEY).
- f2_city_cruise_l100km, f2_city_accel_l100km: the two parts of the city figure (cruise phases, stop-and-go term).
- f2_cruise_l100km: steady cruise at 30/40/50 km/h (diagnostic only).
