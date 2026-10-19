"""Every experiment stage as a function. LOCKED FILE for the agent (tasks call these through scripts/run_stage.py).

Scales: 'smoke' (minutes, only to prove the code runs) and 'full' (the real thing). Results go to data/processed.
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

from cd70 import analysis, config, study
from cd70.objective import FUEL_KEY
from cd70.runner import load_parts, run_batch

ROOT = config.ROOT
PROC = ROOT / "data" / "processed"
SCALE = {
    "smoke": dict(rob_evals=36, rob_k=3, draws=8192, min_acc=0, morris_r=4, sobol_n=16, opt_evals=60, pop=12, members=12, grid_members=3,
                  voi_members=12, n_jobs=2),
    "full": dict(rob_evals=800, rob_k=10, draws=32768, min_acc=100, morris_r=30, sobol_n=256, opt_evals=1600, pop=40, members=300,
                 grid_members=60, voi_members=300, n_jobs=2),
}


def _out(scale: str) -> Path:
    p = PROC if scale == "full" else ROOT / "runs" / "smoke"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _jobs(scale: str) -> int:
    """Worker processes. Env CD70_JOBS overrides. Default: CPU count minus 2 (min 1, max 6); smoke uses 2."""
    import os
    if os.environ.get("CD70_JOBS"):
        return max(1, int(os.environ["CD70_JOBS"]))
    if scale == "smoke":
        return 2
    return max(1, min(6, (os.cpu_count() or 4) - 2))


# ---------------------------------------------------------------- calibration
def calibrate(timing: str, scale: str = "full") -> dict:
    """Rejection ABC in rounds. Each round = `draws` more Sobol points; stop when enough engines are accepted."""
    out = _out(scale) / f"cal_{timing}"
    n = SCALE[scale]["draws"]
    max_rounds = 8 if scale == "full" else 1
    chunk = 512 if scale == "full" else 256
    dim = len(config.uncertain_names())
    u_all = qmc.Sobol(dim, scramble=True, seed=config.seeds()["calibration_sobol"]).random(n * max_rounds)
    min_acc = config.calibration()["min_accepted"] if scale == "full" else 0
    summary: dict = {}
    for r in range(max_rounds):
        sl = slice(r * n, (r + 1) * n)
        ds = config.unit_to_unc(u_all[sl])
        rows = [study.flat_row(unc=d, timing=timing, draw=r * n + i) for i, d in enumerate(ds)]
        df = run_batch("cd70.study:cal_row", rows, out, chunk=chunk, n_jobs=_jobs(scale), start_part=r * (n // chunk))
        summary = finalize_calibration(timing, scale, df)
        summary["rounds"] = r + 1
        if summary["accepted"] >= min_acc:
            break
    summary = finalize_calibration(timing, scale, None, validate=True)
    summary["rounds"] = r + 1
    (_out(scale) / f"cal_summary_{timing}.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
    return summary


def finalize_calibration(timing: str, scale: str, df: pd.DataFrame | None = None, validate: bool = False) -> dict:
    out = _out(scale)
    df = load_parts(out / f"cal_{timing}") if df is None else df
    ok = df[df["status"] == "ok"]
    acc = ok[ok["accepted"] == 1.0].reset_index(drop=True)
    ucols = [f"u_{n}" for n in config.uncertain_names()]
    n_raw, dropped = len(acc), {}
    if validate and len(acc):
        import shutil
        vdir = out / f"valid_{timing}"
        shutil.rmtree(vdir, ignore_errors=True)
        rows = [study.flat_row(unc={c[2:]: float(r[c]) for c in ucols}, timing=timing, idx=i) for i, r in acc.iterrows()]
        vdf = run_batch("cd70.study:eval_checked", rows, vdir, chunk=100, n_jobs=_jobs(scale), progress=False)
        vdf = vdf.sort_values("idx").reset_index(drop=True)
        keep = vdf["feasible"].to_numpy() == 1.0
        for col in ("rules_failed", "plaus_failed"):
            for s in vdf.loc[~keep, col].fillna(""):
                for name in str(s).split(","):
                    if name:
                        dropped[name] = dropped.get(name, 0) + 1
        dropped["status_or_knock_or_pmax"] = int((~keep).sum()) - sum(dropped.values()) if (~keep).sum() > sum(dropped.values()) else 0
        acc.to_parquet(out / f"accepted_raw_{timing}.parquet", index=False)
        acc = acc[keep].reset_index(drop=True)
    acc.to_parquet(out / f"accepted_{timing}.parquet", index=False)
    acc45 = ok[ok["accepted_p45"] == 1.0]
    summary = {
        "timing": timing, "draws": int(len(df)), "errors": int((df["status"] != "ok").sum()),
        "accepted": int(len(acc)), "accepted_before_validity_check": n_raw, "dropped_invalid_baseline": n_raw - int(len(acc)),
        "dropped_reasons": dropped, "acceptance_rate": float(len(acc) / max(len(ok), 1)),
        "accepted_power45": int(len(acc45)), "acceptance_rate_power45": float(len(acc45) / max(len(ok), 1)),
    }
    if len(acc):
        spec = {d["name"]: d for d in config.priors()["uncertain"]}
        z = []
        for c in ucols:
            s = spec[c[2:]]
            lo, hi = (s["low"], s["high"]) if s["dist"] != "discrete" else (min(s["values"]), max(s["values"]))
            z.append((acc[c].to_numpy() - lo) / (hi - lo))
        z = np.array(z).T
        dist = ((z - np.median(z, axis=0)) ** 2).sum(axis=1)
        best = acc.iloc[int(dist.argmin())]
        twin = {c[2:]: float(best[c]) for c in ucols}
        (out / f"twin_{timing}.json").write_text(json.dumps(twin, indent=1), encoding="utf-8")
        summary["posterior_median"] = {c[2:]: float(acc[c].median()) for c in ucols}
        summary["posterior_shrink"] = {c[2:]: float(acc[c].std() / ((spec[c[2:]].get("high", 1) - spec[c[2:]].get("low", 0)) / math.sqrt(12)) if spec[c[2:]]["dist"] != "discrete" else float("nan")) for c in ucols}
        summary["crank_rpm_quartiles"] = [float(x) for x in acc["u_crank_rpm"].quantile([.25, .5, .75])]
        summary["leak_area_mm2_quartiles"] = [float(x) for x in acc["u_leak_area_mm2"].quantile([.25, .5, .75])]
        summary["speedo_overread_quartiles"] = [float(x) for x in acc["u_speedo_overread"].quantile([.25, .5, .75])]
        summary["cda_m2_quartiles"] = [float(x) for x in acc["u_cda_m2"].quantile([.25, .5, .75])]
        summary["enough"] = bool(len(acc) >= config.calibration()["min_accepted"])
    (out / f"cal_summary_{timing}.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
    return summary


def load_twin(timing: str, scale: str = "full") -> dict:
    p = _out(scale) / f"twin_{timing}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_members(timing: str, n: int, scale: str = "full", seed_name: str = "robustness_subsample") -> list:
    acc = pd.read_parquet(_out(scale) / f"accepted_{timing}.parquet")
    ucols = [f"u_{k}" for k in config.uncertain_names()]
    if len(acc) > n:
        acc = acc.sample(n=n, random_state=config.seeds()[seed_name]).reset_index(drop=True)
    return [{c[2:]: float(r[c]) for c in ucols} for _, r in acc.iterrows()]


# ---------------------------------------------------------------- baseline curves
def baseline_curves(timing: str, scale: str = "full") -> Path:
    """WOT curves and cruise numbers of the baseline for every accepted member. One row per member x rpm."""
    from cd70.engine import engine_point
    from cd70.evaluate import WOT_RPMS, ensure_knock_k
    from cd70.params import SCENARIO_CAL, build_params
    members = load_members(timing, SCALE[scale]["members"], scale)
    recs = []
    for k, unc in enumerate(members):
        u = ensure_knock_k({**config.nominal_unc(), **unc}, timing)
        p = build_params(u, None, SCENARIO_CAL, timing)
        for rpm in WOT_RPMS:
            r = engine_point(rpm, 1.0, p)
            recs.append(dict(member=k, rpm=rpm, torque_nm=r["torque_nm"], power_hp=r["power_hp"], bsfc=r["bsfc_gkwh"],
                             ve=r["ve_air"], ki=r["ki_end"], pmax_bar=r["pmax_bar"], imep=r["imep_net_bar"],
                             pmep=r["pmep_bar"], fmep=r["fmep_bar"], lam=r["lam"]))
    df = pd.DataFrame(recs)
    path = _out(scale) / f"baseline_curves_{timing}.parquet"
    df.to_parquet(path, index=False)
    return path


# ---------------------------------------------------------------- sensitivity
def _twin_row(timing, scale, design, scen=None):
    return study.flat_row(unc=load_twin(timing, scale), design=design, scen=scen, timing=timing)


def sens_ofat(timing: str, scale: str = "full") -> pd.DataFrame:
    spec = config.priors()["design"]
    base = config.baseline_design()
    rows = [dict(_twin_row(timing, scale, base), var="baseline", side="base")]
    for s in spec:
        for side, val in (("low", s["low"]), ("high", s["high"])):
            d = dict(base)
            d[s["name"]] = float(val)
            rows.append(dict(_twin_row(timing, scale, d), var=s["name"], side=side))
    df = run_batch("cd70.study:eval_checked", rows, _out(scale) / f"ofat_{timing}", chunk=50, n_jobs=_jobs(scale))
    return df


def sens_morris(timing: str, scale: str = "full") -> pd.DataFrame:
    from SALib.analyze import morris as m_an
    from SALib.sample import morris as m_sa
    names = config.design_names()
    lo, hi = config.design_bounds(names)
    problem = {"num_vars": len(names), "names": names, "bounds": [[0, 1]] * len(names)}
    X = m_sa.sample(problem, SCALE[scale]["morris_r"], num_levels=4, seed=config.seeds()["morris"])
    ds = config.unit_to_design(X, names)
    rows = [dict(_twin_row(timing, scale, d), run=i) for i, d in enumerate(ds)]
    df = run_batch("cd70.study:eval_checked", rows, _out(scale) / f"morris_{timing}", chunk=100, n_jobs=_jobs(scale))
    df = df.sort_values("run").reset_index(drop=True)
    res = []
    for y in ("f1_torque_wot_mean_nm", FUEL_KEY):
        v = df[y].to_numpy(float)
        if not np.isfinite(v).all():
            v = np.where(np.isfinite(v), v, np.nanmedian(v))
        r = m_an.analyze(problem, X, v, num_levels=4, print_to_console=False)
        res.append(pd.DataFrame({"var": names, "mu": r["mu"], "mu_star": r["mu_star"], "sigma": r["sigma"], "y": y}))
    out = pd.concat(res)
    out.to_parquet(_out(scale) / f"morris_result_{timing}.parquet", index=False)
    return out


def sens_sobol(timing: str, scale: str = "full") -> pd.DataFrame:
    from SALib.analyze import sobol as s_an
    from SALib.sample import sobol as s_sa
    names = config.design_names()
    problem = {"num_vars": len(names), "names": names, "bounds": [[0, 1]] * len(names)}
    X = s_sa.sample(problem, SCALE[scale]["sobol_n"], calc_second_order=False, seed=config.seeds()["sobol_design"])
    ds = config.unit_to_design(X, names)
    rows = [dict(_twin_row(timing, scale, d), run=i) for i, d in enumerate(ds)]
    df = run_batch("cd70.study:eval_checked", rows, _out(scale) / f"sobol_{timing}", chunk=200, n_jobs=_jobs(scale))
    df = df.sort_values("run").reset_index(drop=True)
    res = []
    for y in ("f1_torque_wot_mean_nm", FUEL_KEY):
        v = df[y].to_numpy(float)
        v = np.where(np.isfinite(v), v, np.nanmedian(v))
        r = s_an.analyze(problem, v, calc_second_order=False, print_to_console=False, seed=1)
        res.append(pd.DataFrame({"var": names, "S1": r["S1"], "S1_conf": r["S1_conf"], "ST": r["ST"],
                                 "ST_conf": r["ST_conf"], "y": y}))
    out = pd.concat(res)
    out.to_parquet(_out(scale) / f"sobol_result_{timing}.parquet", index=False)
    return out


# ---------------------------------------------------------------- optimisation
def _objectives(res: dict, base: dict) -> tuple:
    f1, f2 = res.get("f1_torque_wot_mean_nm", float("nan")), res.get(FUEL_KEY, float("nan"))
    if not (math.isfinite(f1) and math.isfinite(f2)):
        return 0.0, 3.0
    return -f1 / base["f1"], f2 / base["f2"]


def _cons(res: dict) -> list:
    bad = 1.0 if (res.get("rules_ok", 0) != 1.0 or res.get("plaus_ok", 0) != 1.0 or res.get("status") != "ok") else -1.0
    return [float(res.get("g_knock", 1.0)), float(res.get("g_pmax", 1.0)), bad]


def _base_values(timing: str, scale: str) -> dict:
    r = study.eval_checked(_twin_row(timing, scale, config.baseline_design()))
    return {"f1": r["f1_torque_wot_mean_nm"], "f2": r[FUEL_KEY]}


def optimise(timing: str, cls: str, method: str, seed: int, scale: str = "full") -> Path:
    """method: nsga2 | tpe | random. cls: A | B | C. Evaluates the nominal twin only (robustness is tested later)."""
    names = config.hardware_class(cls)
    lo, hi = config.design_bounds(names)
    n_evals = SCALE[scale]["opt_evals"]
    base = _base_values(timing, scale)
    twin = load_twin(timing, scale)
    hist: list = []

    def evaluate(x):
        d = config.unit_to_design(((np.asarray(x) - lo) / (hi - lo))[None, :], names)[0]
        res = study.eval_checked(study.flat_row(unc=twin, design=d, timing=timing))
        o = _objectives(res, base)
        c = _cons(res)
        hist.append(dict(eval=len(hist) + 1, method=method, cls=cls, timing=timing, seed=seed, o1=o[0], o2=o[1],
                         g_knock=c[0], g_pmax=c[1], bad=c[2], feasible=float(max(c) <= 0.0),
                         f1=res["f1_torque_wot_mean_nm"], f2=res[FUEL_KEY],
                         rules_failed=res["rules_failed"], plaus_failed=res["plaus_failed"],
                         **{f"d_{k}": v for k, v in d.items()}))
        return o, c

    if method == "nsga2":
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import ElementwiseProblem
        from pymoo.optimize import minimize
        from pymoo.termination import get_termination

        class P(ElementwiseProblem):
            def __init__(self):
                super().__init__(n_var=len(names), n_obj=2, n_ieq_constr=3, xl=lo, xu=hi)

            def _evaluate(self, x, out, *a, **k):
                o, c = evaluate(x)
                out["F"], out["G"] = list(o), c

        pop = SCALE[scale]["pop"]
        minimize(P(), NSGA2(pop_size=pop), get_termination("n_eval", n_evals), seed=seed, verbose=False)
    elif method == "tpe":
        import optuna
        warnings.filterwarnings("ignore", category=FutureWarning)
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        spec = {d["name"]: d for d in config.priors()["design"]}

        def objective(trial):
            x = []
            for n in names:
                s = spec[n]
                x.append(trial.suggest_int(n, int(s["low"]), int(s["high"])) if s["integer"] else trial.suggest_float(n, s["low"], s["high"]))
            o, c = evaluate(np.array(x, float))
            trial.set_user_attr("c", c)
            return o

        sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=max(10, n_evals // 10),
                                             constraints_func=lambda t: t.user_attrs["c"])
        st = optuna.create_study(directions=["minimize", "minimize"], sampler=sampler)
        st.optimize(objective, n_trials=n_evals)
    elif method == "random":
        rng = np.random.default_rng(config.seeds()["random_search"] + seed)
        for _ in range(n_evals):
            evaluate(lo + rng.random(len(names)) * (hi - lo))
    else:
        raise ValueError(method)
    df = pd.DataFrame(hist)
    path = _out(scale) / "opt" / f"{timing}_{cls}_{method}_{seed}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def optimise_robust(timing: str, cls: str, seed: int, scale: str = "full") -> Path:
    """NSGA-II on an ensemble of K calibrated engines (not only the twin).

    o1 = -mean(f1_i / f1_base_i), o2 = mean(f2_i / f2_base_i) over the K members (paired with each member's own baseline).
    Constraints: 80th percentile of ki_max over members <= 0.95, worst p_cyl_max <= 60 bar, at most 10 percent of
    members may break a design rule or plausibility check.
    """
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.optimize import minimize
    from pymoo.termination import get_termination

    names = config.hardware_class(cls)
    lo, hi = config.design_bounds(names)
    k = SCALE[scale]["rob_k"]
    members = load_members(timing, k, scale, seed_name="robustness_subsample")
    base_d = config.baseline_design()
    base = []
    for unc in members:
        r = study.eval_checked(study.flat_row(unc=unc, design=base_d, timing=timing))
        base.append((r["f1_torque_wot_mean_nm"], r[FUEL_KEY]))
    hist: list = []

    def evaluate(x):
        d = config.unit_to_design(((np.asarray(x) - lo) / (hi - lo))[None, :], names)[0]
        f1r, f2r, ki, pm, bad = [], [], [], [], 0
        for unc, b in zip(members, base):
            r = study.eval_checked(study.flat_row(unc=unc, design=d, timing=timing))
            if not (math.isfinite(r["f1_torque_wot_mean_nm"]) and math.isfinite(r[FUEL_KEY])):
                bad += 1
                continue
            f1r.append(r["f1_torque_wot_mean_nm"] / b[0])
            f2r.append(r[FUEL_KEY] / b[1])
            ki.append(r["ki_max"])
            pm.append(r["p_cyl_max_bar"])
            bad += int(r["rules_ok"] != 1.0 or r["plaus_ok"] != 1.0)
        if not f1r:
            return (0.0, 3.0), [1.0, 1.0, 1.0]
        o = (-float(np.mean(f1r)), float(np.mean(f2r)))
        c = [float(np.quantile(ki, 0.8)) - study.KI_LIMIT, float(max(pm)) - study.PMAX_LIMIT_BAR, bad / len(members) - 0.1]
        hist.append(dict(eval=len(hist) + 1, method="nsga2_robust", cls=cls, timing=timing, seed=seed, o1=o[0], o2=o[1],
                         g_knock=c[0], g_pmax=c[1], bad=c[2], feasible=float(max(c) <= 0.0),
                         **{f"d_{kk}": v for kk, v in d.items()}))
        return o, c

    class P(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=len(names), n_obj=2, n_ieq_constr=3, xl=lo, xu=hi)

        def _evaluate(self, x, out, *a, **kw):
            o, c = evaluate(x)
            out["F"], out["G"] = list(o), c

    minimize(P(), NSGA2(pop_size=SCALE[scale]["pop"]), get_termination("n_eval", SCALE[scale]["rob_evals"]),
             seed=seed, verbose=False)
    path = _out(scale) / "optrob" / f"{timing}_{cls}_nsga2robust_{seed}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(hist).to_parquet(path, index=False)
    return path


def pooled_front_robust(timing: str, cls: str, scale: str = "full") -> pd.DataFrame:
    files = sorted((_out(scale) / "optrob").glob(f"{timing}_{cls}_*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    f = df[df["feasible"] == 1.0].reset_index(drop=True)
    if f.empty:
        return f
    return f[analysis.pareto_mask(f[["o1", "o2"]].to_numpy())].sort_values("o1").reset_index(drop=True)


def pooled_front(timing: str, cls: str, scale: str = "full") -> pd.DataFrame:
    files = sorted((_out(scale) / "opt").glob(f"{timing}_{cls}_*_*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    f = df[df["feasible"] == 1.0].reset_index(drop=True)
    if f.empty:
        return f
    return f[analysis.pareto_mask(f[["o1", "o2"]].to_numpy())].sort_values("o1").reset_index(drop=True)


def _picked(timing: str, cls: str, which: str, scale: str) -> dict:
    d = json.loads((_out(scale) / f"picked_{timing}_{cls}.json").read_text(encoding="utf-8"))
    if which not in d:
        raise KeyError(f"design '{which}' not found for {timing}/{cls}; available: {list(d)}")
    return d[which]


def pick_designs(timing: str, cls: str, scale: str = "full", robust: bool = True) -> dict:
    """Two named designs from the pooled front: 'econ' (least fuel with torque not lower) and 'power' (most torque with fuel not higher)."""
    fr = pooled_front_robust(timing, cls, scale) if robust else pooled_front(timing, cls, scale)
    dcols = [c for c in fr.columns if c.startswith("d_")]
    out = {}
    e = fr[fr["o1"] <= -1.0]
    if len(e):
        out["econ"] = {c[2:]: float(e.sort_values("o2").iloc[0][c]) for c in dcols}
    p = fr[fr["o2"] <= 1.0]
    if len(p):
        out["power"] = {c[2:]: float(p.sort_values("o1").iloc[0][c]) for c in dcols}
    if len(fr):
        z1 = (fr["o1"] - fr["o1"].min()) / max(fr["o1"].max() - fr["o1"].min(), 1e-9)
        z2 = (fr["o2"] - fr["o2"].min()) / max(fr["o2"].max() - fr["o2"].min(), 1e-9)
        out["knee"] = {c[2:]: float(fr.iloc[int((z1**2 + z2**2).argmin())][c]) for c in dcols}
    (_out(scale) / f"picked_{timing}_{cls}{'' if robust else '_twin'}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


# ---------------------------------------------------------------- robustness, scenarios, value of information
def robust_paired(timing: str, cls: str, which: str, scale: str = "full") -> pd.DataFrame:
    design = _picked(timing, cls, which, scale)
    members = load_members(timing, SCALE[scale]["members"], scale)
    base = config.baseline_design()
    rows = []
    for k, unc in enumerate(members):
        rows.append(study.flat_row(unc=unc, design=base, timing=timing, member=k, arm="base"))
        rows.append(study.flat_row(unc=unc, design=design, timing=timing, member=k, arm="design"))
    df = run_batch("cd70.study:eval_checked", rows, _out(scale) / f"robust_{timing}_{cls}_{which}", chunk=100, n_jobs=_jobs(scale))
    b = df[df["arm"] == "base"].set_index("member")
    d = df[df["arm"] == "design"].set_index("member")
    out = pd.DataFrame({
        "member": b.index,
        "f1_base": b["f1_torque_wot_mean_nm"], "f1_des": d["f1_torque_wot_mean_nm"],
        "f2_base": b[FUEL_KEY], "f2_des": d[FUEL_KEY],
        "ki_base": b["ki_max"], "ki_des": d["ki_max"], "feasible_des": d["feasible"], "feasible_base": b["feasible"],
        "p_base": b["p_peak_kw"], "p_des": d["p_peak_kw"], "t060_base": b["t_0_60_s"], "t060_des": d["t_0_60_s"],
        "vtop_base": b["v_top_kmh"], "vtop_des": d["v_top_kmh"],
    }).reset_index(drop=True)
    out["torque_gain_pct"] = 100 * (out["f1_des"] / out["f1_base"] - 1)
    out["fuel_gain_pct"] = 100 * (1 - out["f2_des"] / out["f2_base"])  # positive = better
    out["power_gain_pct"] = 100 * (out["p_des"] / out["p_base"] - 1)
    for c in ("ki_des", "ki_base"):
        out[c] = out[c].astype(float)
    out.to_parquet(_out(scale) / f"paired_{timing}_{cls}_{which}.parquet", index=False)
    return out


def scenario_grid(timing: str, cls: str, which: str, scale: str = "full") -> pd.DataFrame:
    design = _picked(timing, cls, which, scale)
    g = config.scenarios()["grid"]
    members = load_members(timing, SCALE[scale]["grid_members"], scale)
    base = config.baseline_design()
    rows = []
    for ron in g["ron"]:
        for t in g["t_amb_c"]:
            for alt in g["alt_m"]:
                for k, unc in enumerate(members):
                    scen = {"ron": ron, "t_amb_c": t, "alt_m": alt}
                    rows.append(study.flat_row(unc=unc, design=base, scen=scen, timing=timing, member=k, arm="base"))
                    rows.append(study.flat_row(unc=unc, design=design, scen=scen, timing=timing, member=k, arm="design"))
    df = run_batch("cd70.study:eval_checked", rows, _out(scale) / f"grid_{timing}_{cls}_{which}", chunk=100, n_jobs=_jobs(scale))
    return df


def voi(timing: str, cls: str, which: str, scale: str = "full") -> pd.DataFrame:
    """Which uncertain inputs drive the size of the improvement? Random forest permutation importance + Spearman."""
    from scipy.stats import spearmanr
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import permutation_importance
    paired = pd.read_parquet(_out(scale) / f"paired_{timing}_{cls}_{which}.parquet")
    acc = pd.read_parquet(_out(scale) / f"accepted_{timing}.parquet")
    members = load_members(timing, SCALE[scale]["members"], scale)
    X = pd.DataFrame(members).iloc[paired["member"].to_numpy()].reset_index(drop=True)
    res = []
    for y in ("torque_gain_pct", "fuel_gain_pct"):
        t = paired[y].to_numpy(float)
        m = np.isfinite(t)
        if m.sum() < 10:
            continue
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=config.seeds()["voi_forest"], n_jobs=2)
        rf.fit(X[m], t[m])
        pi = permutation_importance(rf, X[m], t[m], n_repeats=10, random_state=1, n_jobs=2)
        for i, n in enumerate(X.columns):
            rho = spearmanr(X[n][m], t[m]).statistic if X[n][m].nunique() > 1 else float("nan")
            res.append(dict(var=n, y=y, perm_importance=float(pi.importances_mean[i]), spearman=float(rho), r2_train=float(rf.score(X[m], t[m]))))
    out = pd.DataFrame(res)
    out.to_parquet(_out(scale) / f"voi_{timing}_{cls}_{which}.parquet", index=False)
    del acc
    return out
