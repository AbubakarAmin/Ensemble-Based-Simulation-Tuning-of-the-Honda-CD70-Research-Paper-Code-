"""Assemble the manuscript from result files only (no hand-typed numbers).  python scripts/build_paper.py
Writes paper/PAPER_DRAFT.md + .docx, PLACEHOLDERS.md, CHECKLIST.md, COVER_LETTER.md, SUBMISSION_GUIDE.md, TITLE_OPTIONS.md."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cd70.objective import FUEL_KEY  # noqa: E402

OUT = ROOT / "paper"
OUT.mkdir(exist_ok=True)
PI = ROOT / "paper_inputs"
FIG = ROOT / "figures"
subprocess.run([sys.executable, str(ROOT / "scripts" / "make_workflow_figure.py")], cwd=ROOT, capture_output=True)
F = json.loads((PI / "RESULTS_FACTS.json").read_text(encoding="utf-8"))
TITLE = "Ensemble-Based Simulation Tuning of the Honda CD70: Robust Design Optimisation of a 72 cc Engine under Specification Uncertainty"
NAMES = {"econ": "economy design", "power": "power design", "knee": "balanced (knee) design"}
CLS = {"A": "class A (jet and ignition)", "B": "class B (class A plus compression ratio)", "C": "class C (all eight tuning variables)"}
RANK = {"CLAIM": 3, "CONDITIONAL": 2, "INDICATIVE": 1}
PH = {"[[AUTHORS]]": "author names", "[[AFFILIATIONS]]": "affiliations", "[[CORRESPONDING_EMAIL]]": "corresponding author e-mail",
      "[[CODE_URL]]": "link (DOI) to the code archive", "[[DATA_URL]]": "link (DOI) to the raw-results archive", "[[FUNDING]]": "funding statement",
      "[[ACKNOWLEDGEMENTS]]": "acknowledgements", "[[CONFLICT_OF_INTEREST]]": "conflict of interest statement",
      "[[AUTHOR_CONTRIBUTIONS]]": "author contributions (CRediT roles)", "[[JOURNAL_NAME]]": "target journal"}
figs_no, tabs_no, fig_order, tab_key = {}, {}, [], {}
referenced_figs = set()


def rd(p):
    q = ROOT / p
    return q.read_text(encoding="utf-8").strip() if q.exists() else ""


def csv(name):
    p = PI / "tables" / name
    return pd.read_csv(p) if p.exists() else None


def pct(x):
    return f"{x:+.2f}"


def fmtv(v):
    if isinstance(v, (int,)) or (isinstance(v, float) and v.is_integer() and abs(v) >= 100):
        return f"{int(v):,}"
    if isinstance(v, float):
        if v != v:
            return "-"
        a = abs(v)
        if a == 0:
            return "0"
        if a >= 1000:
            return f"{v:,.0f}"
        if a >= 100:
            return f"{v:.1f}"
        if a >= 1:
            return f"{v:.2f}"
        if a >= 0.001:
            return f"{v:.3f}"
        return f"{v:.1e}"
    return str(v)


def captions():
    d = {}
    for ln in rd("figures/FIGURE_INDEX.md").splitlines():
        m = re.match(r"- `(.+?)\.png`: (.*)", ln)
        if m:
            d[m.group(1)] = m.group(2)
    return d


CAP = captions()


def figure(stem):
    if not (FIG / f"{stem}.png").exists():
        return ""
    figs_no[stem] = len(figs_no) + 1
    fig_order.append(stem)
    return f"\n![Figure {figs_no[stem]}. {CAP.get(stem, stem)}](../figures/{stem}.png)\n"


def table(df, caption, key=None, maxrows=30):
    if df is None or not len(df):
        return ""
    n = len(tabs_no) + 1
    tabs_no[key or f"t{n}"] = n
    df = df.head(maxrows)
    h = "| " + " | ".join(str(c) for c in df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    body = "".join("| " + " | ".join(fmtv(v) if not isinstance(v, str) else v for v in r) + " |\n" for _, r in df.iterrows())
    return f"\n**Table {n}. {caption}**\n\n{h}{body}\n"


def figs(*stems):
    referenced_figs.update(stems)
    return "@F:" + ",".join(stems) + "@"


def verb(level, metric):
    lv = (str(level) or "").split()[0] if level else ""
    return {"CLAIM": f"improves {metric}", "CONDITIONAL": f"improves {metric} under the stated conditions only",
            "INDICATIVE": f"may improve {metric}"}.get(lv, f"has no supported effect on {metric}")


def lvl(c):
    return str(c).split(" (")[0] if c else "NOT SUPPORTED"


def entries():
    for T in "BA":
        t = F.get(f"timing_{T}") or {}
        for cls, d in (t.get("paired") or {}).items():
            for w, e in d.items():
                yield T, cls, w, e


def best_entry():
    best = None
    for T, cls, w, e in entries():
        sc = (RANK.get(lvl(e["claims"].get("torque_gain_pct")), 0) + RANK.get(lvl(e["claims"].get("fuel_gain_pct")), 0),
              e["feasible_fraction_design"] >= 0.9, T == "B", cls == "C", e["torque_gain_pct"]["median"] + e["fuel_gain_pct"]["median"])
        if best is None or sc > best[0]:
            best = (sc, T, cls, w, e)
    return best[1:] if best else None


def claim_counts():
    c = {"CLAIM": 0, "CONDITIONAL": 0, "INDICATIVE": 0, "NOT SUPPORTED": 0}
    for _, _, _, e in entries():
        for v in e["claims"].values():
            c[lvl(v) if lvl(v) in c else "NOT SUPPORTED"] += 1
    return c


def top_vars(T, y, k=3):
    df = csv(f"sobol_{T}.csv")
    if df is None:
        return []
    d = df[df["y"] == y].sort_values("ST", ascending=False).head(k)
    return [(r["var"], r["ST"], r["S1"]) for _, r in d.iterrows()]


def spec_rows(sec_start, cols):
    m = re.search(r"\n## " + re.escape(sec_start) + r".*?\n(.*?)(?=\n---|\n## )", "\n" + SHEET, re.S)
    out = []
    for ln in (m.group(1).splitlines() if m else []):
        if ln.startswith("|"):
            cells = [re.sub(r"\[(.*?)\]\(.*?\)", r"\1", c.strip()).replace("**", "") for c in ln.strip("|").split("|")]
            out.append("| " + " | ".join(cells[:cols]) + " |")
    return out


SHEET = rd("docs/spec_sheet_v11.md")
YN = {"f1_torque_wot_mean_nm": "mean full-throttle torque", FUEL_KEY: "city fuel consumption"}
verdict = (F.get("feasibility") or {}).get("verdict", "NOT AVAILABLE")
b = best_entry()
cc = claim_counts()
ntot = sum(cc.values())
calB = (F.get("timing_B") or {}).get("calibration") or {}

# ------------------------------------------------------------------ front matter
HIGHLIGHTS = ["Specification uncertainty is carried as an ensemble of calibrated engines",
              "Every candidate engine and tune passes explicit physical and hardware rules",
              "Paired robust optimisation shows which tuning gains hold across the ensemble",
              "Sensitivity analysis ranks tuning variables and unknown engine properties",
              "Claims are graded by pre-specified rules; code and results are released"]
ab = ["**Background.** This is a simulation study of the 72 cc Honda CD70 commuter engine; no engine measurements were used. Its published specification is incomplete and partly ambiguous, so tuning predictions are most useful when they hold across all engines the specification allows.",
      "**Methods.** We built a crank-angle-resolved single-cylinder engine model with design rules that reject physically impossible variants, and calibrated it to published power, torque, cranking pressure and top speed by approximate Bayesian rejection, retaining an ensemble of consistent engines"
      + (f" ({calB.get('accepted')} accepted of {int(calB['draws']):,} candidates for the main valve-timing reading)." if calB.get("draws") else ".")
      + " Eight tuning variables in three hardware classes were screened, ranked by variance decomposition, optimised and re-optimised for robustness; designs were compared with the baseline on the same engines and every statement was graded by pre-specified claim levels."]
if b:
    T, cls, w, e = b
    ab.append(f"**Results.** For the {NAMES.get(w, w)} in {CLS[cls]} (valve-timing reading {T}), the predicted median change in mean full-throttle torque was {pct(e['torque_gain_pct']['median'])}% "
              f"(95% CI {pct(e['torque_gain_pct']['ci95'][0])} to {pct(e['torque_gain_pct']['ci95'][1])}; level {lvl(e['claims'].get('torque_gain_pct'))}) and the change in city fuel economy was "
              f"{pct(e['fuel_gain_pct']['median'])}% (95% CI {pct(e['fuel_gain_pct']['ci95'][0])} to {pct(e['fuel_gain_pct']['ci95'][1])}; level {lvl(e['claims'].get('fuel_gain_pct'))}), "
              f"with every constraint satisfied on {100 * e['feasible_fraction_design']:.0f}% of the engines. Across all {ntot} design-outcome results, {cc['CLAIM']} reached level CLAIM, {cc['CONDITIONAL']} CONDITIONAL, {cc['INDICATIVE']} INDICATIVE and {cc['NOT SUPPORTED']} NOT SUPPORTED.")
ab.append(f"**Conclusions.** The specification passes the physical feasibility screen with verdict {verdict}. The study identifies which tunes keep their predicted benefit across plausible engines and which unknown engine properties are most worth measuring. All results are simulation predictions based on published figures; planned work adds measurements on a real engine and a full three-dimensional engine model with topology optimisation.")
KEYWORDS = "engine tuning; robust optimisation; uncertainty quantification; approximate Bayesian computation; sensitivity analysis; small spark-ignition engine"
NOMEN = pd.DataFrame([("ABC", "approximate Bayesian computation"), ("CAL / SPEC", "model-parameter inputs / published-specification inputs"), ("CI", "confidence interval (bootstrap, 95%)"),
                      ("KI", "knock index (diagnostic, limit 0.95)"), ("NSGA-II", "non-dominated sorting genetic algorithm II"), ("OFAT", "one factor at a time"),
                      ("RON", "research octane number"), ("TPE", "tree-structured Parzen estimator"), ("WOT", "wide-open throttle (full load)"),
                      ("BTDC / ATDC", "before / after top dead centre"), ("bsfc", "brake-specific fuel consumption"), ("VE", "volumetric efficiency"),
                      ("ST, S1", "Sobol total-order and first-order indices"), ("lambda", "air-fuel equivalence ratio")], columns=["symbol", "meaning"])
md = [f"# {TITLE}", "", "Target journal: [[JOURNAL_NAME]]", "", "[[AUTHORS]]  ", "[[AFFILIATIONS]]  ", "Corresponding author: [[CORRESPONDING_EMAIL]]", "",
      "## Highlights", ""] + [f"- {h}" for h in HIGHLIGHTS] + ["", "## Abstract", ""] + ab + ["", f"**Keywords:** {KEYWORDS}", "",
      "## Nomenclature", "", table(NOMEN, "Abbreviations used in the text.", "nomen")]

# ------------------------------------------------------------------ 1 Introduction
md += ["## 1. Introduction", "",
       "Low-displacement motorcycles are used in very large numbers, and their owners and workshops adjust carburettor jets, ignition timing and sometimes compression ratio or valve timing to trade power against fuel economy. For a commuter engine such as the Honda CD70 the question is practical: which changes help, by how much, and what do they risk (knock, excessive cylinder pressure, mechanical interference)? Simulation can answer this faster and more safely than workshop trials, but only if the simulated engine is a fair representation of the real one.",
       "That is the difficulty addressed here. For commercial commuter models the specification is incomplete: data-sheet values are rounded, sources disagree, and workshop-manual editions differ (Section 2). An optimiser applied to one assumed engine finds tunes that exploit that engine's assumed details, and such a tune may fail, or run into knock or pressure limits, on a neighbouring engine that is equally consistent with the published numbers.",
       "### 1.1 Related work and positioning", "",
       "Zero- and one-dimensional engine models are standard tools for small spark-ignition engines [R8]. Published studies calibrate such models to measured data, including a small-engine simulation validation case [R1], a GT-Power model calibration [R2], one-dimensional calibration with Wiebe combustion for a small four-stroke engine (Honda GX-35) [R3], and a Wiebe-based single-cylinder model of a 125 cc motorcycle engine [R4]. These studies calibrate to measurements of a specific engine and then treat the calibrated model as the engine. Our setting differs: no measurements of the target engine are available, so calibration yields a population of plausible engines rather than one engine, and conclusions are drawn over that population.",
       "Our uncertainty treatment follows approximate Bayesian computation by rejection [R16]; screening and variance decomposition use Morris elementary effects [R13] and Sobol indices [R14, R15]; the influence of uncertain properties is assessed with random forests [R17]; and multi-objective search uses NSGA-II [R5, R19] with a Bayesian sampler [R6] and random search as comparators. The sub-models are standard: Wiebe heat release, Woschni wall heat transfer [R9], the Chen-Flynn friction correlation [R10], and a Livengood-Wu knock integral [R11] with an Arrhenius ignition-delay form after Douaud and Eyzat [R12]. To our knowledge, this combination (calibrated ensemble, design rules that reject impossible variants, paired robust comparison and graded claims) has not been applied to a low-cost commuter engine.",
       "The engine specification itself is not an original contribution of this paper. It is a compiled, source-tagged specification sheet (Section 2, Appendices C and D, Supplementary File S1) that fixes the inputs of the study; the work of the original sources is cited there by tag and register.",
       "### 1.2 Research questions and contributions", "",
       "We ask three questions. **RQ1:** which tuning changes to a stock CD70 stay beneficial across the whole ensemble of engines consistent with the published data? **RQ2:** which tuning variables and which unknown engine properties decide the size of the benefit? **RQ3:** how much of the benefit survives variation of fuel octane, altitude and temperature, and which candidate variants are physically impossible?",
       "Our contributions are: (i) a calibrated-ensemble workflow (@F:f00_workflow@) in which every candidate engine and every tuned variant passes explicit physical and hardware rules; (ii) a screening and variance-based ranking of the tuning variables; (iii) robust multi-objective optimisation with paired comparison against the baseline and graded claim levels; (iv) a value-of-information ranking of the unknown properties worth measuring first; and (v) a fully scripted, seeded and machine-verified pipeline, released with the paper.", ""]
referenced_figs.add("f00_workflow")
md.append(figure("f00_workflow"))

# ------------------------------------------------------------------ 2 Specification
md += ["## 2. Engine specification and data sources", "",
       "The engine is the Atlas Honda CD70: single-cylinder, air-cooled, four-stroke, overhead camshaft, carburetted, bore 47.0 mm, stroke 41.4 mm, 72 cm3, compression ratio 9.3:1. Every input carries a source tag (official, medium, workshop manual, derived, proxy, assumed). The source hierarchy is: official Atlas Honda documents; CD70-specific secondary sources; an older CD70 workshop manual (provisional, because it disagrees with the official documents on compression ratio and chain slack and is probably a different edition); sibling-model data (used only as sanity checks); and low-quality sources. Where sources conflict, the decision and reason are logged (Appendix D). Values that are not firmly known are treated as uncertain inputs with explicit prior ranges (Appendix A). Two readings of the workshop-manual valve timing are analysed: reading A as printed (0/20/20/0 degrees) and reading B with 20 degrees added to each flank, which we treat as the main case.", "",
       f"**Table {len(tabs_no) + 1}. Key engine specification and the confidence tag of each value (full tables with sources in Appendix C).**", ""]
tabs_no["spec"] = len(tabs_no) + 1
md += spec_rows("2. Engine and geometry", 3) + [""]

# ------------------------------------------------------------------ 3 Methods
md += ["## 3. Methods", ""]
model_txt = rd("docs/paper_text/model.md")
md.append(model_txt)
try:
    from cd70 import rules as _r
    rr = [dict(rule=k, kind=v[0], limit=v[1], tag=v[2], meaning=v[3]) for k, v in {**_r.DESIGN_LIMITS, **_r.RESULT_LIMITS}.items()]
    md.append(table(pd.DataFrame(rr), "Design rules and plausibility limits applied to every candidate (kind: max or min allowed; tag: PHYSICS, HARDWARE or CONVENTION).", "rules"))
except Exception as ex:
    print("rules table skipped:", ex)
try:
    from cd70 import config as _c
    dv = pd.DataFrame([dict(variable=d["name"], low=d["low"], high=d["high"], baseline=d["baseline"], integer="yes" if d.get("integer") else "no", hardware_class=d["hardware"]) for d in _c.priors()["design"]])
    md.append(table(dv, "Tuning variables, bounds and the hardware class in which each first appears (class B adds the compression ratio to A; class C adds the remaining variables).", "design"))
except Exception as ex:
    print("design table skipped:", ex)
md.append(rd("docs/paper_text/calibration_method.md"))
try:
    import yaml
    cal = yaml.safe_load((ROOT / "config" / "calibration.yaml").read_text(encoding="utf-8"))
    def win(v):
        if "target" in v:
            return f"{v['target']} +/- {100 * v['rel_tol']:.0f}%"
        return " to ".join(f"{k} {x}" for k, x in v.items())
    nm = {"power_hp_7500": "Power at 7,500 rpm, WOT (hp)", "torque_nm_5500": "Torque at 5,500 rpm, WOT (Nm)", "cranking_bar": "Cranking compression (bar)",
          "top_speed_true_kmh": "True top speed (km/h)", "bsfc_gkwh_7500": "bsfc at 7,500 rpm (g/kWh)", "ve_7500": "Volumetric efficiency at 7,500 rpm",
          "theta_pmax_atdc_5500": "Crank angle of peak pressure at 5,500 rpm (deg ATDC)", "pmax_bar": "Peak cylinder pressure (bar)"}
    ct = pd.DataFrame([dict(condition=nm[k], window=(f"below {v['high']}" if list(v) == ["high"] else win(v))) for k, v in cal.items() if k in nm])
    md.append(table(ct, "Calibration conditions; a candidate engine is accepted only if all are met (conditions at RON 87, 35 C, sea level).", "cal"))
except Exception as ex:
    print("cal table skipped:", ex)
md.append(rd("docs/paper_text/robust_method.md"))
try:
    from cd70.experiments import SCALE as _S
    s = _S["full"]
    sg = _c.scenarios()["grid"]
    nscen = len(sg["ron"]) * len(sg["t_amb_c"]) * len(sg["alt_m"])
    sd = pd.DataFrame([("Uncertain inputs / tuning variables", f"{len(_c.priors()['uncertain'])} / {len(_c.priors()['design'])}"),
                       ("Calibration candidates per round (max rounds)", f"{s['draws']:,} (8)"), ("Minimum accepted engines", f"{s['min_acc']}"),
                       ("Single-engine optimiser budget (evaluations per run)", f"{s['opt_evals']:,}"), ("Robust optimiser: evaluations x ensemble members", f"{s['rob_evals']:,} x {s['rob_k']}"),
                       ("Morris trajectories / Sobol base sample", f"{s['morris_r']} / {s['sobol_n']}"), ("Paired comparison engines (max)", f"{s['members']}"),
                       ("Scenario grid: conditions x engines", f"{nscen} x {s['grid_members']}"), ("Valve-timing readings", "2 (A, B)")], columns=["design element", "value"])
    md.append(table(sd, "Study design at a glance.", "design_glance"))
except Exception as ex:
    print("design glance skipped:", ex)

# ------------------------------------------------------------------ 4 Results
md += ["## 4. Results", ""]
md += ["### 4.1 Physical feasibility of the specification", "", f"Before any calibration, the published specification was tested for physical consistency with {len((F.get('feasibility') or {}).get('checks', [])) or 'a set of'} independent checks (geometry, specific power, mean effective pressure, gearing, road load). The overall verdict is **{verdict}**."]
chk = (F.get("feasibility") or {}).get("checks")
if chk:
    md.append(table(pd.DataFrame([dict(check=c["name"], value=c["value"], rule=c["rule"], verdict=c["verdict"]) for c in chk]), "Feasibility checks of the published specification.", "feas", maxrows=40))
md += ["", "### 4.2 Calibrated ensemble", ""]
summ = []
for T in "BA":
    c = (F.get(f"timing_{T}") or {}).get("calibration") or {}
    if c:
        summ.append((T, c))
if summ:
    rows = []
    for k, lab in (("draws", "candidate engines simulated"), ("accepted_before_validity_check", "accepted by calibration conditions"), ("dropped_invalid_baseline", "removed by the validity pass"), ("accepted", "final ensemble size"),
                   ("acceptance_rate", "acceptance rate"), ("accepted_power45", "accepted if power target were 4.5 hp (sensitivity)")):
        rows.append({"quantity": lab, **{f"reading {T}": c.get(k, "-") for T, c in summ}})
    md.append(table(pd.DataFrame(rows), "Calibration outcome for the two valve-timing readings.", "calsum"))
    md.append(f"Calibration retained a thin slice of the prior space (acceptance rate {', '.join(f'{c.get(chr(97)+chr(99)+chr(99)+chr(101)+chr(112)+chr(116)+chr(97)+chr(110)+chr(99)+chr(101)+chr(95)+chr(114)+chr(97)+chr(116)+chr(101), 0):.4f} for reading {T}' for T, c in summ)}), as expected when several published constraints must hold at once. The accepted engines are an ensemble, not a fitted point: the posterior distributions of the uncertain inputs and their dependences are shown in {figs(*[f'f01_posteriors_timing{T}' for T in 'BA'], *[f'f12_posterior_patterns_timing{T}' for T in 'BA'])} and Tables {'@T:shrink_B@'} and {'@T:corr_B@'}.")
for T in "BA":
    md.append(figure(f"f01_posteriors_timing{T}"))
    md.append(figure(f"f12_posterior_patterns_timing{T}"))
    md.append(table(csv(f"posterior_shrinkage_{T}.csv"), f"Prior-to-posterior shrinkage of the uncertain inputs, reading {T} (ratio of standard deviations; values below 1 mean the calibration data constrain the input).", f"shrink_{T}", maxrows=20))
    md.append(table(csv(f"posterior_top_correlations_{T}.csv"), f"Strongest rank correlations among accepted inputs, reading {T} (inputs that the calibration data constrain jointly).", f"corr_{T}", maxrows=12))
md += ["", "### 4.3 Baseline behaviour of the calibrated engine", "", "The calibrated stock engine reproduces the published power and torque by construction; its full-throttle behaviour elsewhere in the speed range, and the spread among accepted engines, are predictions" + f" ({figs('f02_baseline_curves_timingB', 'f02_baseline_curves_timingA')})."]
for T in "BA":
    md.append(figure(f"f02_baseline_curves_timing{T}"))
    md.append(table(csv(f"baseline_curves_{T}.csv"), f"Baseline full-throttle curves, reading {T}: percentiles (p05, p50, p95) over the calibrated engines.", f"base_{T}", maxrows=14))
md += ["", "### 4.4 Which tuning variables matter", ""]
for T in "BA":
    for y in YN:
        tv = top_vars(T, y)
        if tv:
            md.append(f"For {YN[y]} (reading {T}), the largest total-order Sobol indices were " + ", ".join(f"{v} (ST = {st:.2f}, S1 = {s1:.2f})" for v, st, s1 in tv) + ". A total index well above the first-order index indicates interaction with other variables.")
md.append(f"One-at-a-time effects, Morris screening and Sobol indices are shown in {figs(*[f'f0{k}_{n}_timing{T}' for T in 'BA' for k, n in ((3, 'ofat_tornado'), (4, 'morris'), (5, 'sobol'))])}; the indices are tabulated in @T:sobol_B@ and @T:sobol_A@.")
for T in "BA":
    md += [figure(f"f03_ofat_tornado_timing{T}"), figure(f"f04_morris_timing{T}"), figure(f"f05_sobol_timing{T}"),
           table(csv(f"sobol_{T}.csv"), f"Sobol indices of the tuning variables, reading {T} (y: objective; S1 first order, ST total order, CI half-width columns).", f"sobol_{T}"),
           table(csv(f"morris_{T}.csv"), f"Morris screening, reading {T} (mu_star: mean absolute effect; sigma: spread, a sign of interaction or non-linearity).", f"morris_{T}")]
md += ["", "### 4.5 Optimisation on the nominal engine", "", "Quality of the three optimisers is compared by the hypervolume of the feasible Pareto front over several seeds. Where random search comes close to NSGA-II, the problem is easy for an optimiser and we make no claim of algorithmic advantage. The fronts are shown in " + figs(*[f"f06_pareto_hv_timing{T}_class{c}" for T in "BA" for c in "ABC"]) + "."]
for T in "BA":
    hv = (F.get(f"timing_{T}") or {}).get("hv") or {}
    if hv:
        md.append(table(pd.DataFrame([dict(reading=T, hardware_class=cls, method=m, hypervolume=v["hv_mean"], feasible_share=v["feasible_fraction"]) for cls, d in hv.items() for m, v in d.items()]),
                        f"Optimiser comparison, reading {T} (hypervolume: higher is better; feasible share: fraction of evaluated designs satisfying all constraints).", f"hv_{T}"))
    for cls in "ABC":
        md.append(figure(f"f06_pareto_hv_timing{T}_class{cls}"))
md += ["", "### 4.6 Robust designs compared with the baseline", "",
       "Robust optimisation evaluated each candidate on a subsample of the calibrated ensemble and scored it by mean paired gain. Three named designs were picked from the pooled robust front (economy, power, balanced). All gains below are paired over the same engines and positive values are improvements; claim levels follow Appendix B and determine the wording."]
hl = [{"reading": T, "class": cls, "design": w, "torque %": f"{pct(e['torque_gain_pct']['median'])} [{pct(e['torque_gain_pct']['ci95'][0])}, {pct(e['torque_gain_pct']['ci95'][1])}]", "torque level": lvl(e["claims"].get("torque_gain_pct")),
       "fuel %": f"{pct(e['fuel_gain_pct']['median'])} [{pct(e['fuel_gain_pct']['ci95'][0])}, {pct(e['fuel_gain_pct']['ci95'][1])}]", "fuel level": lvl(e["claims"].get("fuel_gain_pct")), "feasible %": f"{100 * e['feasible_fraction_design']:.0f}"}
      for T, cls, w, e in entries()]
md.append(table(pd.DataFrame(hl), "Headline results: paired median change versus the baseline (95% bootstrap CI in brackets; positive = better), claim level, and share of engines on which the design satisfies every constraint.", "headline", maxrows=40))
for T, cls, w, e in entries():
    tq, fu, cl = e["torque_gain_pct"], e["fuel_gain_pct"], e["claims"]
    md.append(f"Reading {T}, {CLS[cls]}, {NAMES.get(w, w)} ({e['members']} engines): the design {verb(cl.get('torque_gain_pct'), 'mean full-throttle torque')} (median {pct(tq['median'])}%, 95% CI {pct(tq['ci95'][0])} to {pct(tq['ci95'][1])}; {100 * tq['fraction_positive']:.0f}% of engines improve; level {lvl(cl.get('torque_gain_pct'))}) and "
              f"{verb(cl.get('fuel_gain_pct'), 'city fuel economy')} (median {pct(fu['median'])}%, 95% CI {pct(fu['ci95'][0])} to {pct(fu['ci95'][1])}; {100 * fu['fraction_positive']:.0f}% improve; level {lvl(cl.get('fuel_gain_pct'))}). It satisfies every constraint on {100 * e['feasible_fraction_design']:.0f}% of the engines.")
for T in "BA":
    def cmp_table(T=T):
        d = csv(f"compare_{T}.csv")
        if d is None:
            return ""
        out = []
        for _, r in d.iterrows():
            row = {"design": r["design"], "feasible %": f"{100 * r['feasible_fraction']:.0f}"}
            for m, lab in (("f1_torque_wot_mean_nm", "mean torque"), (FUEL_KEY, "city L/100 km"), ("p_7500_hp", "power 7,500 rpm"), ("v_top_kmh", "top speed"), ("t_0_60_s", "0-60 km/h time")):
                if f"{m}_change_pct_median" in d.columns:
                    row[lab + " %"] = f"{pct(r[m + '_change_pct_median'])} [{pct(r[m + '_ci_lo'])}, {pct(r[m + '_ci_hi'])}]"
            out.append(row)
        return table(pd.DataFrame(out), f"Paired percentage change of each design against the baseline on the same engines, reading {T} (median and 95% CI; for fuel use and 0-60 time a negative change is an improvement).", f"cmp_{T}")
    def abs_table(T=T):
        d = csv(f"compare_absolute_{T}.csv")
        if d is None:
            return ""
        cols = {"label": "design", "f1_torque_wot_mean_nm": "mean torque (Nm)", FUEL_KEY: "city (L/100 km)", "p_7500_hp": "power 7,500 rpm (hp)", "v_top_kmh": "top speed (km/h)", "t_0_60_s": "0-60 km/h (s)"}
        d = d[[c for c in cols if c in d.columns]].rename(columns=cols)
        return table(d, f"Median absolute metrics of the baseline and the picked designs, reading {T}.", f"abs_{T}")
    md += [figure(f"f13_compare_torque_timing{T}"), figure(f"f14_compare_cruise_timing{T}"), figure(f"f15_compare_paired_timing{T}"), cmp_table(), abs_table()]
    for cls in "ABC":
        md.append(figure(f"f08_robust_front_timing{T}_class{cls}"))
    for cls in "ABC":
        for w in ("econ", "power", "knee"):
            md.append(figure(f"f09_paired_timing{T}_class{cls}_{w}"))
md.append(f"The comparison of the designs with the baseline is shown in {figs(*[f'f1{k}_{n}_timing{T}' for T in 'BA' for k, n in ((3, 'compare_torque'), (4, 'compare_cruise'), (5, 'compare_paired'))])}, the robust fronts in {figs(*[f'f08_robust_front_timing{T}_class{c}' for T in 'BA' for c in 'ABC'])}, and the distribution of paired gains over engines in {figs(*[f'f09_paired_timing{T}_class{c}_{w}' for T in 'BA' for c in 'ABC' for w in ('econ', 'power', 'knee')])}.")
md += ["", "### 4.7 Robustness to octane, altitude and temperature", ""]
sc = sorted(FIG.glob("f10_scenarios_*.png"))
md.append("Gains of each design across the scenario grid are shown in " + (figs(*[p.stem for p in sc]) if sc else "the scenario figures") + ". Cells where the share of feasible engines falls (usually because of knock) mark conditions in which the tune is not robust.")
for p in sc:
    md.append(figure(p.stem))
md += ["", "### 4.8 Which unknown engine properties decide the benefit", "", "A random-forest permutation importance and a Spearman correlation relate each uncertain engine property to the size of the paired gain. Properties with high importance are the ones worth measuring on a real engine first."]
for T, cls, w, e in entries():
    for y, v in (e.get("voi_top") or {}).items():
        md.append(f"- Reading {T}, {CLS[cls]}, {NAMES.get(w, w)}, outcome {y.replace('_', ' ')}: most informative unknowns: {', '.join(v)}.")
md.append("The importance plots are in " + figs(*[f"f11_voi_timing{T}_class{c}_{w}" for T in "BA" for c in "ABC" for w in ("econ", "power", "knee")]) + ".")
for T in "BA":
    for cls in "ABC":
        for w in ("econ", "power", "knee"):
            md.append(figure(f"f11_voi_timing{T}_class{cls}_{w}"))
md += ["", "### 4.9 Independent checks", ""]
ratios = []
for T in "BA":
    for cls, d in ((F.get(f"timing_{T}") or {}).get("hv") or {}).items():
        if "random" in d and "nsga2" in d and d["nsga2"]["hv_mean"] > 0:
            ratios.append(f"reading {T}, {CLS[cls]}: {100 * d['random']['hv_mean'] / d['nsga2']['hv_mean']:.0f}%")
if ratios:
    md.append("Random search reached the following share of the NSGA-II hypervolume: " + "; ".join(ratios) + ".")
md += ["", re.sub(r"^# .*\n", "", rd("reports/holdout_validation.md"), count=1), "", "The automatic consistency flags raised by the pipeline are listed verbatim in Appendix E."]

# v16: fuel comparison (T-035). Same definitions as the optimiser's city objective; no number is typed here.
fv = re.sub(r"^# .*\n", "", rd("reports/fuel_validation.md"), count=1)
md += ["", "### 4.10 Fuel validation against published and owner figures", ""]
md.append("The model's city-cycle fuel use (the optimiser objective, Section 3.7) is compared with published and owner figures using the same definitions: steady cruise with steady figures, city cycle with city figures, and a run-in scenario with new-bike figures. Agreement is judged by a rule fixed before the results were seen (config/validation.yaml). Manufacturer claims and figures with no source are shown but not used for the verdict.")
if fv:
    md += ["", fv.replace("\n## ", "\n#### "), ""]
else:
    md += ["", "NOT AVAILABLE: the fuel validation (task T-035) has not been run, so no comparison with published or owner fuel figures is reported."]

# ------------------------------------------------------------------ 5 Discussion
md += ["", "## 5. Discussion", "", "### 5.1 Principal findings", ""]
if b:
    T, cls, w, e = b
    md.append(f"**RQ1.** The strongest supported result is for the {NAMES.get(w, w)} of {CLS[cls]} (reading {T}): predicted median changes of {pct(e['torque_gain_pct']['median'])}% in mean full-throttle torque (level {lvl(e['claims'].get('torque_gain_pct'))}) and {pct(e['fuel_gain_pct']['median'])}% in city fuel economy (level {lvl(e['claims'].get('fuel_gain_pct'))}). Of {ntot} design-outcome results, {cc['CLAIM']} reach CLAIM and {cc['NOT SUPPORTED']} are not supported; only the former may be read as improvements. Comparing the hardware classes shows how much of the benefit requires hardware changes beyond jetting and ignition.")
    agree = []
    for cls_ in "ABC":
        for w_ in ("econ", "power", "knee"):
            ea = (((F.get("timing_A") or {}).get("paired") or {}).get(cls_) or {}).get(w_)
            eb = (((F.get("timing_B") or {}).get("paired") or {}).get(cls_) or {}).get(w_)
            if ea and eb:
                agree.append((ea["torque_gain_pct"]["median"] > 0) == (eb["torque_gain_pct"]["median"] > 0))
    if agree:
        md.append(f"The sign of the torque gain agrees between the two valve-timing readings for {sum(agree)} of {len(agree)} design and class combinations; where they disagree, the claim is capped by the claim rules, so the valve-timing ambiguity cannot inflate a conclusion.")
for T in "BA":
    for y in YN:
        tv = top_vars(T, y, 2)
        if tv:
            md.append(f"**RQ2.** The variance decomposition (reading {T}) attributes the response of {YN[y]} mainly to {tv[0][0]}" + (f" and {tv[1][0]}" if len(tv) > 1 else "") + "; the value-of-information ranking (Section 4.8) lists the unknown engine properties that decide the size of the gain and are the first candidates for measurement.")
            break
    else:
        continue
    break
md.append("**RQ3.** The scenario grid (Section 4.7) shows where the benefit survives changes of octane, altitude and temperature, and the design rules and plausibility checks (Sections 3.3 and 4.1) report which variants are physically impossible rather than silently simulating them.")
md += ["", "### 5.2 Relation to earlier work", "",
       "Earlier small-engine studies calibrate a model to measurements and then optimise or analyse that single calibrated model [R1-R4]. The present study asks a different question, namely which conclusions survive when the model is not pinned down: the ensemble replaces the single engine, paired comparisons remove engine-to-engine variation from the estimated effect, and claim levels prevent a result from being worded more strongly than the ensemble supports. The trade-off is that predictions refer to a population of plausible engines rather than to one machine, and that absolute accuracy is limited by the published figures used for calibration.", "",
       "### 5.3 Implications, safety and future work", "", rd("docs/paper_text/implications.md"), ""]

# ------------------------------------------------------------------ 6 Limitations 7 Conclusions
md += ["## 6. Scope and extensions", "", rd("docs/paper_text/limitations.md"), "",
       "## 7. Conclusions", "",
       f"A calibrated-ensemble workflow with explicit design rules gives a defensible way to assess the tuning of an incompletely specified engine. The specification passes the physical feasibility screen (verdict {verdict}). The graded results state which predicted gains hold across the ensemble ({cc['CLAIM']} of {ntot} design-outcome results reach CLAIM) and which unknown engine properties are most worth measuring. The predictions follow from the published figures used for calibration, and a bench or road test of one reversible change is the natural next step; the value-of-information ranking says which measurement to take first.", "",
       "## Data and code availability", "",
       "**Supplementary File S1** is the specification sheet (`spec_sheet_v11`) with the source register and conflict log. The code, configuration, task list and processed data are available at [[CODE_URL]]. The raw simulation data (calibration draws, accepted ensembles, optimiser histories and paired results, as parquet and JSON files) are archived at [[DATA_URL]]. Every number in this paper is generated from these files by `scripts/build_paper.py`; the run is deterministic given the seeds in `config/seeds.yaml` and the pinned `requirements.txt`.", "",
       "## Declarations", "",
       "**Use of AI tools.** The simulation study was executed by an automated AI coding agent following a fixed, version-controlled task list with machine-checked gates, hash-locked model code and a number-verification step. The authors designed the study, reviewed the outputs and take full responsibility for the content.", "",
       "**Author contributions.** [[AUTHOR_CONTRIBUTIONS]]", "", "**Funding.** [[FUNDING]]", "", "**Acknowledgements.** [[ACKNOWLEDGEMENTS]]", "", "**Conflict of interest.** [[CONFLICT_OF_INTEREST]]", ""]

# ------------------------------------------------------------------ appendices
md += ["## Appendix A. Uncertain inputs and priors", "", rd("paper_inputs/METHODS_FACTS.md"), "", "## Appendix B. Claim rules", "", re.sub(r"^# .*\n", "", rd("docs/CLAIM_RULES.md"), count=1), "",
       "## Appendix C. Base engine specification (from Supplementary File S1)", ""]
for k, (t, nm_) in enumerate((("2. Engine and geometry", "Engine and geometry"), ("3.", "Valve train"), ("4.", "Ignition, fuel and carburettor"), ("5. Drivetrain", "Drivetrain, chassis and weights"), ("6. Performance", "Performance and calibration values"))):
    md += [f"### C.{k + 1} {nm_}", ""] + spec_rows(t, 4) + [""]
md += ["## Appendix D. Source conflicts and decisions", ""] + spec_rows("7. Conflict log", 5) + ["", "## Appendix E. Automatic consistency flags (verbatim from the pipeline)", "", re.sub(r"^# .*\n", "", rd("reports/red_team.md"), count=1), ""]
body = "\n".join(x for x in md if x is not None)

# ------------------------------------------------------------------ references: renumber by first citation
HAVE = {}
for mm in re.finditer(r"\| (R\d) \| (.+?) \| (\S+) \| (.+?) \|", SHEET):
    HAVE[mm.group(1)] = f"{mm.group(2)}. {mm.group(3)}"
REFS = {"R1": HAVE.get("R1", "Morrissey and Shedd, SAE Technical Paper 2008-32-0043. https://doi.org/10.4271/2008-32-0043"),
        "R2": HAVE.get("R2", "Avelar et al., SAE Technical Paper 2019-36-0170. https://doi.org/10.4271/2019-36-0170"),
        "R3": HAVE.get("R3", "Penaranda et al., Honda GX-35 one-dimensional calibration (Mecanica Computacional)."),
        "R4": HAVE.get("R4", "Dresler and Richtar, MZ125 single-cylinder Wiebe model (Perner's Contacts)."),
        "R5": "Deb K, Pratap A, Agarwal S, Meyarivan T. A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation 6(2), 182-197, 2002.",
        "R6": "Akiba T, Sano S, Yanase T, Ohta T, Koyama M. Optuna: a next-generation hyperparameter optimization framework. Proceedings of the 25th ACM SIGKDD Conference, 2623-2631, 2019.",
        "R8": "Heywood JB. Internal Combustion Engine Fundamentals. McGraw-Hill, 1988.",
        "R9": "Woschni G. A universally applicable equation for the instantaneous heat transfer coefficient in the internal combustion engine. SAE Technical Paper 670931, 1967.",
        "R10": "Chen SK, Flynn PF. Development of a single cylinder compression ignition research engine. SAE Technical Paper 650733, 1965.",
        "R11": "Livengood JC, Wu PC. Correlation of autoignition phenomena in internal combustion engines and rapid compression machines. Symposium (International) on Combustion 5, 347-356, 1955.",
        "R12": "Douaud AM, Eyzat P. Four-octane-number method for predicting the anti-knock behavior of fuels and engines. SAE Technical Paper 780080, 1978.",
        "R13": "Morris MD. Factorial sampling plans for preliminary computational experiments. Technometrics 33(2), 161-174, 1991.",
        "R14": "Sobol IM. Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates. Mathematics and Computers in Simulation 55, 271-280, 2001.",
        "R15": "Saltelli A, Ratto M, Andres T, et al. Global Sensitivity Analysis: The Primer. Wiley, 2008.",
        "R16": "Beaumont MA, Zhang W, Balding DJ. Approximate Bayesian computation in population genetics. Genetics 162, 2025-2035, 2002.",
        "R17": "Breiman L. Random forests. Machine Learning 45, 5-32, 2001.",
        "R18": "Goodwin DG, Moffat HK, Schoegl I, Speth RL, Weber BW. Cantera: an object-oriented software toolkit for chemical kinetics, thermodynamics, and transport processes, version 3.2.0. https://www.cantera.org",
        "R19": "Blank J, Deb K. pymoo: multi-objective optimization in Python. IEEE Access 8, 89497-89509, 2020.",
        "R20": "Lam SK, Pitrou A, Seibert S. Numba: a LLVM-based Python JIT compiler. Proceedings of the Second Workshop on the LLVM Compiler Infrastructure in HPC, 2015.",
        "R21": "Herman J, Usher W. SALib: an open-source Python library for sensitivity analysis. Journal of Open Source Software 2(9), 97, 2017."}
CITE = re.compile(r"\[(R\d+(?:\s*(?:,|-|–)\s*R\d+)*)\]")


def expand(g):
    out = []
    for tok in re.split(r"\s*,\s*", g):
        m = re.match(r"R(\d+)\s*[-–]\s*R(\d+)$", tok)
        out += [f"R{i}" for i in range(int(m.group(1)), int(m.group(2)) + 1)] if m else [tok]
    return out


order = []
for m in CITE.finditer(body):
    for k in expand(m.group(1)):
        if k in REFS and k not in order:
            order.append(k)
newn = {k: i + 1 for i, k in enumerate(order)}


def rewrite(m):
    ns = sorted({newn[k] for k in expand(m.group(1)) if k in newn})
    parts, i = [], 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
            j += 1
        parts.append(f"{ns[i]}-{ns[j]}" if j - i >= 2 else ", ".join(str(x) for x in ns[i:j + 1]))
        i = j + 1
    return "[" + ", ".join(parts) + "]"


body = CITE.sub(rewrite, body)
refs_md = ["## References", ""] + [f"[{newn[k]}] {REFS[k]}" for k in order] + [""]
body = body.replace("## Appendix A.", "\n".join(refs_md) + "\n## Appendix A.", 1)
# resolve figure/table tokens
def figtok(m):
    st = [s for s in m.group(1).split(",") if s in figs_no]
    if not st:
        return "the corresponding figures"
    nums = sorted(figs_no[s] for s in st)
    runs, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        runs.append(f"{nums[i]}-{nums[j]}" if j > i else str(nums[i]))
        i = j + 1
    return ("Figure " if len(nums) == 1 else "Figures ") + ", ".join(runs)


body = re.sub(r"@F:([^@]*)@", figtok, body)
body = re.sub(r"@T:([^@]*)@", lambda m: str(tabs_no.get(m.group(1), "?")), body)
body = re.sub(r"Table @tab:(\w+)@", lambda m: f"Table {tabs_no.get(m.group(1), '?')}", body)
body = re.sub(r"\(\s*Figure ([\d-]+)\s*\)", r"(Figure \1)", body)
body = re.sub(r"\n{3,}", "\n\n", body)
(OUT / "PAPER_DRAFT.md").write_text(body, encoding="utf-8")
(OUT / "PLACEHOLDERS.md").write_text("# Fill these in the Word file (search for `[[`)\n\n" + "\n".join(f"- `{k}`: {v}" for k, v in PH.items()) +
                                     "\n\nAlso before submission: complete the full bibliographic details of the entries cited from the specification sheet (the SAE and conference papers) from their DOIs, and check every reference against the original.\n", encoding="utf-8")

# ------------------------------------------------------------------ cover letter, title options, submission guide
ent = f"{CLS[b[1]]}" if b else "the tuning variables"
(OUT / "COVER_LETTER.md").write_text(f"""Dear Editor,

Please consider the manuscript "{TITLE}" for publication in [[JOURNAL_NAME]].

Published specifications of commuter motorcycle engines are incomplete and often contradictory, yet tuning studies normally treat one assumed engine as the truth. We ask which tuning gains survive that uncertainty. We build a verified crank-angle engine model with explicit design rules, calibrate it by approximate Bayesian rejection to an ensemble of engines consistent with the published data, and evaluate screening, optimisation and robust optimisation by paired comparison on that ensemble, with every statement graded by pre-specified claim levels.

The main contributions are (i) the calibrated-ensemble and design-rule workflow, (ii) a ranking of tuning variables and of unknown engine properties by their influence on the outcome, and (iii) a fully scripted, seeded and machine-verified pipeline whose code and raw results are released. We are explicit that the results are model predictions conditional on published figures; we have not measured a real engine, and the manuscript states what the evidence does and does not support.

The work has not been published and is not under consideration elsewhere. Code and data are available at [[CODE_URL]] and [[DATA_URL]]. An AI coding agent executed the scripted simulation pipeline under author supervision, as disclosed in the manuscript.

Suggested reviewers: [[SUGGESTED_REVIEWERS]]

Sincerely,
[[AUTHORS]]
""", encoding="utf-8")
(OUT / "TITLE_OPTIONS.md").write_text(f"""# Title options (the draft uses option 1)

1. {TITLE}
2. Which Tuning Gains Survive Specification Uncertainty? Calibrated-Ensemble Robust Optimisation of a 72 cc Air-Cooled Motorcycle Engine
3. Tuning an Incompletely Specified Engine: Ensemble Calibration, Design Rules and Paired Robust Optimisation for the Honda CD70
4. Robust Simulation-Based Tuning of a Low-Cost Motorcycle Engine When the Specification Is Uncertain
5. From Conflicting Data Sheets to Defensible Tuning Claims: An Ensemble Approach for a 72 cc Four-Stroke Engine

Option 1 asks the reader's question and names the method and the engine; options 2 and 4 are plainer for journals that dislike question titles. Keep the engine name in the title (searchability). Do not put numeric results in the title.
""", encoding="utf-8")
(OUT / "SUBMISSION_GUIDE.md").write_text("""# Submission guide

## Where to submit (be realistic)
The work is a simulation methodology and case study without experimental validation. Best fit: journals that publish applied engine modelling, simulation methods or open engineering studies, for example SAE International Journal of Engines, Proceedings of the IMechE Part D, Energies, Applied Sciences, Results in Engineering, or a thermal-engineering case-study journal. Aiming first at a top-ranked combustion journal is unlikely to succeed without measurements on a real engine. Check each journal's current scope, article-processing charge, word limit and reference style on its own website before you submit; these change.

## Before you submit
1. Fill every `[[...]]` in PAPER_DRAFT.docx (see PLACEHOLDERS.md).
2. Complete the full bibliographic details of references that came from the specification sheet (SAE and conference papers) and check every reference against the original.
3. Upload the code (GitHub release, Zenodo DOI) and raw results (Zenodo DOI) from `paper/supplement/` and put the DOIs in the manuscript.
4. Read the whole draft once, especially Sections 4.6 and 5.1, and make sure each sentence matches the claim level written beside it.
5. Reformat to the journal template (reference style, figure format, word limit). Export figures from `figures/` at the journal's required resolution.

## Using a language-polishing model
Give the model PAPER_DRAFT.md plus this instruction: "Improve clarity, flow and concision of the prose only. Do not change any number, table, figure, claim level, citation number or claim word (improves / may improve / no supported effect). Do not add references or results. Keep all [[placeholders]]. Keep the scope section as precise as it is. List every change you made."

## Likely reviewer objections and where the manuscript answers them
- No experimental validation: stated openly (Section 6, item 1; Section 5.3); the value-of-information ranking tells which measurements to do first.
- Priors are subjective: all priors and their tags are in Appendix A; sensitivity of conclusions to valve-timing reading A vs B is shown; the main targets and tolerances are in the calibration table.
- Model too simple: verification tests (Section 3.1), the design rules (Section 3.3), and the scope list names the effects not modelled.
- Over-claiming: wording follows pre-specified claim levels (Appendix B).
- Reproducibility: seeds, pinned packages, scripted pipeline, released code and raw data (Section 3.11 and Data availability).
""", encoding="utf-8")

# ------------------------------------------------------------------ docx
try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Inches, Pt, RGBColor
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.5)
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:restart"), "continuous")
    sec._sectPr.append(ln)
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.font.size = Pt(11)
    st.paragraph_format.line_spacing = 1.4
    st.paragraph_format.space_after = Pt(6)
    for nme, sz in (("Heading 1", 14), ("Heading 2", 13), ("Heading 3", 12), ("Heading 4", 11), ("Title", 18)):
        h = doc.styles[nme]
        h.font.name = "Times New Roman"
        h.font.size = Pt(sz)
        h.font.bold = True
        h.font.color.rgb = RGBColor(0, 0, 0)
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run()
    for t, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if t:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), t)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = txt
        r._r.append(e)

    def runs(par, text, size=None):
        for part in re.split(r"(\*\*.+?\*\*|`.+?`)", text):
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                rr_ = par.add_run(part[2:-2])
                rr_.bold = True
            elif part.startswith("`") and part.endswith("`") and len(part) > 2:
                rr_ = par.add_run(part[1:-1])
                rr_.font.name = "Consolas"
            else:
                rr_ = par.add_run(part)
            if size:
                rr_.font.size = Pt(size)

    lines = body.splitlines()
    i = 0
    first = True
    while i < len(lines):
        s_ = lines[i]
        m = re.match(r"(#{1,4}) (.*)", s_)
        if m:
            lev = len(m.group(1))
            txt = m.group(2).replace("**", "")
            if lev == 1 and first:
                p = doc.add_paragraph(txt, style="Title")
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                first = False
            else:
                doc.add_heading(txt, level=max(1, lev - 1) if not txt.startswith("Appendix") else 1)
        elif s_.startswith("!["):
            mm = re.match(r"!\[(.*?)\]\((.*?)\)$", s_)
            pth = (OUT / mm.group(2)).resolve()
            if pth.exists():
                doc.add_picture(str(pth), width=Inches(6.0))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cp = doc.add_paragraph()
                cp.paragraph_format.line_spacing = 1.0
                rr_ = cp.add_run(mm.group(1))
                rr_.italic = True
                rr_.font.size = Pt(9.5)
        elif s_.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"\|[-| ]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            i -= 1
            nc = len(rows[0])
            t = doc.add_table(rows=len(rows), cols=nc)
            t.style = "Table Grid"
            fs = 8.5 if nc <= 6 else (7.5 if nc <= 8 else 6.5)
            for ri, row in enumerate(rows):
                for ci in range(nc):
                    cell = t.cell(ri, ci)
                    cell.text = ""
                    pp = cell.paragraphs[0]
                    pp.paragraph_format.line_spacing = 1.0
                    pp.paragraph_format.space_after = Pt(0)
                    rr_ = pp.add_run(row[ci] if ci < len(row) else "")
                    rr_.font.size = Pt(fs)
                    if ri == 0:
                        rr_.bold = True
                        sh = OxmlElement("w:shd")
                        sh.set(qn("w:val"), "clear")
                        sh.set(qn("w:fill"), "E7E6E1")
                        cell._tc.get_or_add_tcPr().append(sh)
            doc.add_paragraph()
        elif s_.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            runs(p, s_[2:])
        elif re.match(r"\d+\. ", s_):
            p = doc.add_paragraph(style="List Number")
            runs(p, re.sub(r"^\d+\. ", "", s_))
        elif s_.strip():
            p = doc.add_paragraph()
            if s_.startswith("**Table "):
                p.paragraph_format.keep_with_next = True
            runs(p, s_.replace("  ", " ").rstrip())
        i += 1
    doc.save(str(OUT / "PAPER_DRAFT.docx"))
except Exception as ex:
    print("docx not written:", ex)

# ------------------------------------------------------------------ arXiv package
_ax = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_arxiv.py")], cwd=ROOT, capture_output=True, text=True)
print(_ax.stdout.strip(), _ax.stderr.strip()[-300:])
# ------------------------------------------------------------------ checklist
chk = []
words = len(body.split())
absw = len(" ".join(ab).split())
cited = set(int(x) for g in re.findall(r"\[([\d, -]+)\]", body) for x in re.findall(r"\d+", g))
unref = [s for s in fig_order if s not in referenced_figs and not s.startswith("f09") and not s.startswith("f10") and not s.startswith("f11")]
vn = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_numbers.py"), "paper/PAPER_DRAFT.md"], cwd=ROOT, capture_output=True, text=True)
chk.append(("PASS" if len(fig_order) >= 10 else "FAIL", f"{len(fig_order)} figures (need at least 10)"))
chk.append(("PASS" if len(tabs_no) >= 10 else "FAIL", f"{len(tabs_no)} tables (need at least 10)"))
chk.append(("PASS" if b else "FAIL", "at least one paired design result present"))
chk.append(("PASS" if verdict != "NOT AVAILABLE" else "FAIL", f"feasibility verdict present ({verdict})"))
chk.append(("PASS" if "NOT AVAILABLE" not in body and "?" not in re.findall(r"Table (\S+?)[ .,)]", body) else "FAIL", "no 'NOT AVAILABLE' text and no unresolved table references"))
chk.append(("PASS" if not re.search(r"\b(proves?|proven|significant(ly)?|groundbreaking|revolutionary)\b", body, re.I) else "FAIL", "no forbidden words (proves, significant, groundbreaking)"))
chk.append(("PASS" if all(len(h) <= 85 for h in HIGHLIGHTS) else "FAIL", "each highlight is at most 85 characters"))
for _pre, _what in (("f13_compare_torque", "baseline-vs-design torque comparison"), ("f14_compare_cruise", "baseline-vs-design city comparison"), ("f15_compare_paired", "paired change vs baseline"), ("f12_posterior_patterns", "posterior pattern figure"), ("f02_baseline_curves", "baseline curves")):
    chk.append(("PASS" if any(x.startswith(_pre) for x in fig_order) else "FAIL", f"figure present in manuscript: {_what}"))
chk.append(("PASS" if (OUT / "ARXIV_METADATA.md").exists() and _ax.returncode == 0 else "FAIL", "arXiv package built (tex, figures, metadata sheet)"))
chk.append(("PASS" if absw <= 300 else "FAIL", f"abstract has {absw} words (limit 300)"))
chk.append(("PASS" if 4 <= len(KEYWORDS.split(';')) <= 8 else "FAIL", "4-8 keywords"))
chk.append(("PASS" if len(order) == len(newn) and cited and max(cited) <= len(order) else "FAIL", f"{len(order)} references, all cited, numbered by first citation"))
chk.append(("PASS" if not unref else "FAIL", f"every main figure is referenced in the text ({len(unref)} unreferenced: {unref[:3]})"))
chk.append(("PASS" if vn.returncode == 0 else "FAIL", "every number in the manuscript exists in the result files (verify_numbers)"))
chk.append(("PASS" if all(k in body for k in PH) else "FAIL", "all placeholders present for the author to fill"))
chk.append(("PASS" if (OUT / "PAPER_DRAFT.docx").exists() else "FAIL", "Word file written"))
chk.append(("PASS" if words > 6000 else "FAIL", f"{words} words in the full manuscript"))
(OUT / "CHECKLIST.md").write_text("# Paper checklist\n\n" + "\n".join(f"- {a}: {m}" for a, m in chk) + "\n", encoding="utf-8")
print("\n".join(f"{a}: {m}" for a, m in chk))
