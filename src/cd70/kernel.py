"""Numba kernel: one engine point (one rpm, one throttle) of a single-cylinder 4-stroke SI engine.

LOCKED FILE for the agent: do not edit unless a task says so. Equations are in docs/MODEL_SPEC.md.

Crank angle convention (degrees, 0..720): 0 = TDC at the start of the intake stroke,
180 = BDC, 360 = TDC firing, 540 = BDC, 720 = TDC again.

States (RK4, per degree of crank angle):
  y0 m_u   unburned fresh charge in the cylinder, kg
  y1 m_b   burned gas (including residual) in the cylinder, kg
  y2 T     cylinder temperature, K (one temperature for both parts)
  y3 p_i   intake plenum pressure, Pa (isothermal at T_i)
  y4 p_e   exhaust plenum pressure, Pa (isothermal at T_ex)
  y5 W     cumulative p dV work, J
  y6 Qw    cumulative wall heat loss, J
  y7 KI    Livengood-Wu knock integral
  y8 min   cumulative mass in from atmosphere, kg
  y9 mout  cumulative mass out to atmosphere, kg
  y10 Qc   cumulative chemical heat release, J
  y11 H    cumulative net enthalpy inflow to the cylinder, J
  y12 Mlk  cumulative mass leaked past the rings (blow-by) to the crankcase at ambient pressure, kg
"""

import math

import numpy as np
from numba import njit

from cd70.gasdata import CV_B, CV_U, DT_TAB, N_TAB, T0_TAB, U_B, U_U

R_GAS = 287.0
LHV = 43.5e6
AFR_ST = 14.7
DEG = math.pi / 180.0
WIEBE_A = 6.908
GAMMA_FLOW = 1.35
GAMMA_UNBURNED = 1.35
P_STD = 101325.0
T_CAL = 308.15  # calibration ambient (35 C); lambda is defined at this air density

NAMES = (
    "bore_m", "stroke_m", "conrod_m", "cr",
    "iv_open_deg", "iv_dur_deg", "ev_open_deg", "ev_dur_deg",
    "lift_in_m", "lift_ex_m", "clearance_m",
    "head_in_m", "head_ex_m", "stem_in_m", "stem_ex_m", "cd_valve",
    "venturi_m", "cd_throttle", "muffler_area_m2", "cd_muffler", "leak_area_m2",
    "v_intake_m3", "v_exhaust_m3", "t_exhaust_k",
    "lambda_wot", "lambda_cruise", "lambda_idle", "fuel_mult_main", "charge_heat_k",
    "ign_low_deg", "ign_4000_deg", "ign_above_deg",
    "burn_dur_deg", "wiebe_m", "spark_delay_deg", "eta_comb",
    "fmep_scale", "t_wall_offset_k", "knock_k", "ron",
    "t_amb_k", "p_amb_pa",
    "const_gamma", "wall_on", "burn_on", "fuel_on",
    "rpm", "alpha", "max_cycles", "dt_max_s", "dth_deg",
)
(
    I_BORE, I_STROKE, I_CONROD, I_CR,
    I_IV_OPEN, I_IV_DUR, I_EV_OPEN, I_EV_DUR,
    I_LIFT_IN, I_LIFT_EX, I_CLEAR,
    I_HEAD_IN, I_HEAD_EX, I_STEM_IN, I_STEM_EX, I_CD_VALVE,
    I_VENTURI, I_CD_THR, I_MUF_AREA, I_CD_MUF, I_LEAK,
    I_V_INTAKE, I_V_EXH, I_T_EXH,
    I_LAM_WOT, I_LAM_CRUISE, I_LAM_IDLE, I_FM_MAIN, I_CHARGE_HEAT,
    I_IGN_LOW, I_IGN_4000, I_IGN_ABOVE,
    I_BURN_DUR, I_WIEBE_M, I_DELAY, I_ETA,
    I_FMEP_SCALE, I_TW_OFF, I_KNOCK_K, I_RON,
    I_T_AMB, I_P_AMB,
    I_CONST_GAMMA, I_WALL_ON, I_BURN_ON, I_FUEL_ON,
    I_RPM, I_ALPHA, I_MAX_CYC, I_DT_MAX, I_DTH,
) = range(len(NAMES))

RES_NAMES = (
    "imep_net_pa", "w_net_j", "pmax_pa", "th_pmax_deg", "m_u_ivc_kg", "y_f", "lam",
    "p_ivc_pa", "t_ivc_k", "ki_end", "t_evo_k", "qw_j", "qc_j", "h_in_j", "du_j",
    "m_in_kg", "m_out_kg", "dm_sys_kg", "cycles_used", "converged", "nstep", "dth_deg",
    "tmax_k", "m_fuel_kg", "ve_air", "th_ivc_deg", "v_ivc_m3", "energy_resid_j", "m_leak_kg",
)
(
    R_IMEP, R_WNET, R_PMAX, R_THPMAX, R_MUIVC, R_YF, R_LAM,
    R_PIVC, R_TIVC, R_KI, R_TEVO, R_QW, R_QC, R_H, R_DU,
    R_MIN, R_MOUT, R_DMSYS, R_CYC, R_CONV, R_NSTEP, R_DTH,
    R_TMAX, R_MFUEL, R_VE, R_THIVC, R_VIVC, R_ERES, R_MLEAK,
) = range(len(RES_NAMES))

TRACE_NAMES = ("th", "p", "T", "V", "xb", "lift_in", "lift_ex", "p_i", "p_e", "m_u", "m_b", "ki")
NTR = len(TRACE_NAMES)

# derived-constant array indexes
(
    D_AP, D_VD, D_VC, D_R, D_L, D_OMEGA, D_SP, D_TI, D_T0, D_P0, D_YF, D_ETA_CHEM,
    D_TH_IGN, D_TH0, D_ATH, D_HC, D_LAM, D_AMUF, D_TH_IVC, D_SIZE,
) = range(20)

# reference-state array indexes (Woschni reference and fresh charge at intake valve closing)
REF_P, REF_T, REF_V, REF_MU, REF_SIZE = 0, 1, 2, 3, 4


@njit(cache=True)
def _tab(T, arr):
    x = (T - T0_TAB) / DT_TAB
    if x < 0.0:
        x = 0.0
    if x > N_TAB - 1.001:
        x = N_TAB - 1.001
    i = int(x)
    f = x - i
    return arr[i] * (1.0 - f) + arr[i + 1] * f


@njit(cache=True)
def cv_u_f(T, cg):
    if cg > 0.0:
        return R_GAS / (cg - 1.0)
    return _tab(T, CV_U)


@njit(cache=True)
def cv_b_f(T, cg):
    if cg > 0.0:
        return R_GAS / (cg - 1.0)
    return _tab(T, CV_B)


@njit(cache=True)
def u_u_f(T, cg):
    if cg > 0.0:
        return R_GAS / (cg - 1.0) * (T - 300.0)
    return _tab(T, U_U)


@njit(cache=True)
def u_b_f(T, cg):
    if cg > 0.0:
        return R_GAS / (cg - 1.0) * (T - 300.0)
    return _tab(T, U_B)


@njit(cache=True)
def smoothstep(e0, e1, x):
    t = (x - e0) / (e1 - e0)
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0
    return t * t * (3.0 - 2.0 * t)


@njit(cache=True)
def lambda_of_alpha(alpha, lam_wot, lam_cruise, lam_idle, fm_main, rho_ratio):
    """Carburettor mixture map in terms of throttle AREA fraction alpha (0..1 of the venturi area).

    Flow chokes early, so steady cruise (about 2 Nm at 4,300 rpm) sits at alpha of about 0.03 and idle below 0.004.
    idle circuit: alpha <= 0.004 gives lam_idle, blending to lam_cruise by 0.015.
    cruise / needle region: lam_cruise up to alpha 0.15.
    power enrichment and main jet: ramp from alpha 0.15 to 1.0 (full lam_wot, full main jet effect at alpha = 1).
    """
    if alpha >= 0.15:
        s_pow = smoothstep(0.15, 1.0, alpha)
        lam_ref = lam_cruise + (lam_wot - lam_cruise) * s_pow
    else:
        s_pow = 0.0
        lam_ref = lam_idle + (lam_cruise - lam_idle) * smoothstep(0.004, 0.015, alpha)
    fuel_mult = 1.0 + s_pow * (fm_main - 1.0)
    return lam_ref / fuel_mult * math.sqrt(rho_ratio)


@njit(cache=True)
def spark_adv(rpm, a_low, a_4000, a_above):
    if rpm <= 1500.0:
        return a_low
    if rpm <= 4000.0:
        return a_low + (a_4000 - a_low) * (rpm - 1500.0) / 2500.0
    if rpm <= 5000.0:
        return a_4000 + (a_above - a_4000) * (rpm - 4000.0) / 1000.0
    return a_above


@njit(cache=True)
def wiebe(th, th0, dur, m):
    xi = (th - th0) / dur
    if xi <= 0.0:
        return 0.0, 0.0
    if xi >= 1.0:
        return 1.0 - math.exp(-WIEBE_A), 0.0
    e = math.exp(-WIEBE_A * xi ** (m + 1.0))
    return 1.0 - e, WIEBE_A * (m + 1.0) * xi ** m * e / dur


@njit(cache=True)
def piston_x(th_deg, r, L):
    t = (th_deg % 360.0) * DEG
    s = math.sin(t)
    return r * (1.0 - math.cos(t)) + L - math.sqrt(L * L - r * r * s * s)


@njit(cache=True)
def piston_dx(th_deg, r, L):
    """dx/d(theta) per DEGREE of crank angle, m/deg."""
    t = (th_deg % 360.0) * DEG
    s = math.sin(t)
    c = math.cos(t)
    return (r * s + r * r * s * c / math.sqrt(L * L - r * r * s * s)) * DEG


@njit(cache=True)
def valve_lift(th, open_deg, dur_deg, lmax, clearance):
    phi = (th - open_deg) % 720.0
    if phi >= dur_deg:
        return 0.0
    s = math.sin(math.pi * phi / dur_deg)
    lift = lmax * s * s - clearance
    if lift < 0.0:
        return 0.0
    return lift


@njit(cache=True)
def valve_area(lift, head_d, stem_d):
    """Flow area = smaller of curtain area and throat area (throat diameter = 0.92 head diameter)."""
    curtain = math.pi * head_d * lift
    dt = 0.92 * head_d
    throat = 0.25 * math.pi * (dt * dt - stem_d * stem_d)
    return curtain if curtain < throat else throat


@njit(cache=True)
def psi_flow(pr):
    crit = (2.0 / (GAMMA_FLOW + 1.0)) ** (GAMMA_FLOW / (GAMMA_FLOW - 1.0))
    if pr < crit:
        pr = crit
    g = GAMMA_FLOW
    return math.sqrt(2.0 * g / (g - 1.0) * (pr ** (2.0 / g) - pr ** ((g + 1.0) / g)))


@njit(cache=True)
def orifice(p1, T1, p2, T2, area):
    """Signed mass flow, side 1 to side 2, kg/s. `area` already includes the discharge coefficient."""
    if area <= 0.0:
        return 0.0
    if p1 >= p2:
        return area * p1 / math.sqrt(R_GAS * T1) * psi_flow(p2 / p1)
    return -area * p2 / math.sqrt(R_GAS * T2) * psi_flow(p1 / p2)


@njit(cache=True)
def rhs(th, y, P, D, ref, dy):
    m_u = y[0]
    m_b = y[1]
    T = y[2]
    p_i = y[3]
    p_e = y[4]
    cg = P[I_CONST_GAMMA]
    if m_u < 0.0:
        m_u = 0.0
    m = m_u + m_b
    r = D[D_R]
    L = D[D_L]
    omega = D[D_OMEGA]
    V = D[D_VC] + D[D_AP] * piston_x(th, r, L)
    dVdth = D[D_AP] * piston_dx(th, r, L)
    p = m * R_GAS * T / V
    T_i = D[D_TI]
    T_ex = P[I_T_EXH]
    p0 = D[D_P0]
    T0 = D[D_T0]

    li = valve_lift(th, P[I_IV_OPEN], P[I_IV_DUR], P[I_LIFT_IN], P[I_CLEAR])
    le = valve_lift(th, P[I_EV_OPEN], P[I_EV_DUR], P[I_LIFT_EX], P[I_CLEAR])
    a_iv = P[I_CD_VALVE] * valve_area(li, P[I_HEAD_IN], P[I_STEM_IN])
    a_ev = P[I_CD_VALVE] * valve_area(le, P[I_HEAD_EX], P[I_STEM_EX])

    mdot_iv = orifice(p_i, T_i, p, T, a_iv)  # intake plenum -> cylinder
    mdot_ev = orifice(p, T, p_e, T_ex, a_ev)  # cylinder -> exhaust plenum
    mdot_th = orifice(p0, T0, p_i, T_i, D[D_ATH])  # atmosphere -> intake plenum
    mdot_mf = orifice(p_e, T_ex, p0, T0, D[D_AMUF])  # exhaust plenum -> atmosphere
    mdot_lk = 0.0  # blow-by past the rings, cylinder -> crankcase (ambient pressure), outflow only
    if p > p0 and P[I_LEAK] > 0.0:
        mdot_lk = orifice(p, T, p0, T, P[I_LEAK])

    # combustion
    xb, dxb = 0.0, 0.0
    if P[I_BURN_ON] > 0.5:
        xb, dxb = wiebe(th, D[D_TH0], P[I_BURN_DUR], P[I_WIEBE_M])
    # conversion of unburned to burned mass: a fraction dxb/(1-xb) of the CURRENT unburned mass per degree,
    # which equals m_u0 * dxb when nothing leaks and stays consistent (never negative) when mass leaves
    dconv = 0.0
    if xb < 1.0 - 1.0e-9 and m_u > 0.0:
        dconv = m_u * dxb / (1.0 - xb)
    dqc = LHV * D[D_YF] * D[D_ETA_CHEM] * dconv

    # species flows (kg per degree)
    dmu = -dconv
    dmb = dconv
    hdot = 0.0
    u_u_T = u_u_f(T, cg)
    u_b_T = u_b_f(T, cg)
    cv_u_T = cv_u_f(T, cg)
    cv_b_T = cv_b_f(T, cg)
    h_cyl = (m_u * u_u_T + m_b * u_b_T) / m + R_GAS * T
    if mdot_iv >= 0.0:
        dmu += mdot_iv / omega
        hdot += mdot_iv / omega * (u_u_f(T_i, cg) + R_GAS * T_i)
    else:
        dmu += mdot_iv / omega * m_u / m
        dmb += mdot_iv / omega * m_b / m
        hdot += mdot_iv / omega * h_cyl
    if mdot_ev >= 0.0:
        dmu -= mdot_ev / omega * m_u / m
        dmb -= mdot_ev / omega * m_b / m
        hdot -= mdot_ev / omega * h_cyl
    else:
        dmb += -mdot_ev / omega
        hdot += -mdot_ev / omega * (u_b_f(T_ex, cg) + R_GAS * T_ex)
    if mdot_lk > 0.0:
        dmu -= mdot_lk / omega * m_u / m
        dmb -= mdot_lk / omega * m_b / m
        hdot -= mdot_lk / omega * h_cyl

    # wall heat transfer (Woschni)
    dqw = 0.0
    if P[I_WALL_ON] > 0.5:
        valves_open = (li > 0.0) or (le > 0.0)
        if valves_open:
            c1 = 6.18
            c2 = 0.0
        elif th < D[D_TH_IGN]:
            c1 = 2.28
            c2 = 0.0
        else:
            c1 = 2.28
            c2 = 3.24e-3
        p_mot = ref[REF_P] * (ref[REF_V] / V) ** 1.3
        dp_term = p - p_mot
        if dp_term < 0.0:
            dp_term = 0.0
        w = c1 * D[D_SP] + c2 * (D[D_VD] * ref[REF_T] / (ref[REF_P] * ref[REF_V])) * dp_term
        if w < 0.1:
            w = 0.1
        B = P[I_BORE]
        h_w = 3.26 * B ** (-0.2) * (p / 1000.0) ** 0.8 * T ** (-0.55) * w ** 0.8
        x = piston_x(th, r, L)
        a_liner = math.pi * B * (x + D[D_HC])
        a_end = D[D_AP]
        a_tot = 2.0 * a_end + a_liner
        tw = (a_end * (450.0 + P[I_TW_OFF]) + a_end * (500.0 + P[I_TW_OFF])
              + a_liner * (400.0 + P[I_TW_OFF])) / a_tot
        dqw = h_w * a_tot * (T - tw) / omega

    num = -p * dVdth - dqw + dqc + hdot - u_u_T * dmu - u_b_T * dmb
    den = m_u * cv_u_T + m_b * cv_b_T
    dy[0] = dmu
    dy[1] = dmb
    dy[2] = num / den
    dy[3] = R_GAS * T_i / P[I_V_INTAKE] * (mdot_th - mdot_iv) / omega
    dy[4] = R_GAS * T_ex / P[I_V_EXH] * (mdot_ev - mdot_mf) / omega
    dy[5] = p * dVdth
    dy[6] = dqw
    # knock integral: unburned gas follows the cylinder pressure isentropically from valve closing
    dki = 0.0
    if P[I_BURN_ON] > 0.5 and ref[REF_MU] > 0.0:
        phi_ivc = (th - D[D_TH_IVC]) % 720.0
        if phi_ivc < 400.0 and xb < 0.98 and p > ref[REF_P]:
            tu = ref[REF_T] * (p / ref[REF_P]) ** ((GAMMA_UNBURNED - 1.0) / GAMMA_UNBURNED)
            tau = 0.01768 * (P[I_RON] / 100.0) ** 3.402 * (p / P_STD) ** (-1.7) * math.exp(3800.0 / tu)
            dki = 1.0 / (P[I_KNOCK_K] * tau) / omega
    dy[7] = dki
    dy[8] = mdot_th / omega
    dy[9] = mdot_mf / omega
    dy[10] = dqc
    dy[11] = hdot
    dy[12] = mdot_lk / omega


@njit(cache=True)
def rk4_step(th, y, h, P, D, ref, k1, k2, k3, k4, yt):
    n = y.size
    rhs(th, y, P, D, ref, k1)
    for i in range(n):
        yt[i] = y[i] + 0.5 * h * k1[i]
    rhs(th + 0.5 * h, yt, P, D, ref, k2)
    for i in range(n):
        yt[i] = y[i] + 0.5 * h * k2[i]
    rhs(th + 0.5 * h, yt, P, D, ref, k3)
    for i in range(n):
        yt[i] = y[i] + h * k3[i]
    rhs(th + h, yt, P, D, ref, k4)
    for i in range(n):
        y[i] += h / 6.0 * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])


@njit(cache=True)
def run(P):
    B = P[I_BORE]
    S = P[I_STROKE]
    L = P[I_CONROD]
    Ap = 0.25 * math.pi * B * B
    Vd = Ap * S
    Vc = Vd / (P[I_CR] - 1.0)
    r = 0.5 * S
    rpm = P[I_RPM]
    omega = 6.0 * rpm
    dth = P[I_DTH]
    if dth <= 0.0:
        dth = P[I_DT_MAX] * omega
        if dth > 1.0:
            dth = 1.0
    nstep = int(math.ceil(720.0 / dth - 1e-9))
    dth = 720.0 / nstep
    T0 = P[I_T_AMB]
    p0 = P[I_P_AMB]
    T_i = T0 + P[I_CHARGE_HEAT]
    T_ex = P[I_T_EXH]
    rho0 = p0 / (R_GAS * T0)
    rho_ref = P_STD / (R_GAS * T_CAL)
    alpha = P[I_ALPHA]
    lam = lambda_of_alpha(alpha, P[I_LAM_WOT], P[I_LAM_CRUISE], P[I_LAM_IDLE], P[I_FM_MAIN], rho0 / rho_ref)
    yf = 1.0 / (1.0 + AFR_ST * lam)
    if P[I_FUEL_ON] < 0.5:
        yf = 0.0
    lam_e = min(lam, 1.0) + 0.4 * max(0.0, 1.0 - lam)
    eta_chem = P[I_ETA] * lam_e
    adv = spark_adv(rpm, P[I_IGN_LOW], P[I_IGN_4000], P[I_IGN_ABOVE])
    th_ign = 360.0 - adv
    th0 = th_ign + P[I_DELAY]

    D = np.zeros(D_SIZE)
    D[D_AP] = Ap
    D[D_VD] = Vd
    D[D_VC] = Vc
    D[D_R] = r
    D[D_L] = L
    D[D_OMEGA] = omega
    D[D_SP] = 2.0 * S * rpm / 60.0
    D[D_TI] = T_i
    D[D_T0] = T0
    D[D_P0] = p0
    D[D_YF] = yf
    D[D_ETA_CHEM] = eta_chem
    D[D_TH_IGN] = th_ign
    D[D_TH0] = th0
    D[D_ATH] = P[I_CD_THR] * alpha * 0.25 * math.pi * P[I_VENTURI] ** 2
    D[D_HC] = Vc / Ap
    D[D_LAM] = lam
    D[D_AMUF] = P[I_CD_MUF] * P[I_MUF_AREA]
    D[D_TH_IVC] = (P[I_IV_OPEN] + P[I_IV_DUR]) % 720.0

    cg = P[I_CONST_GAMMA]
    y = np.zeros(13)
    y[0] = 0.0
    y[1] = p0 * Vc / (R_GAS * T_ex)
    y[2] = T_ex
    y[3] = p0
    y[4] = p0
    ref = np.zeros(REF_SIZE)
    v_ivc_guess = Vc + Ap * piston_x(D[D_TH_IVC], r, L)
    ref[REF_P] = p0
    ref[REF_T] = T_i
    ref[REF_V] = v_ivc_guess
    ref[REF_MU] = 0.8 * p0 * Vd / (R_GAS * T_i)

    k1 = np.zeros(13)
    k2 = np.zeros(13)
    k3 = np.zeros(13)
    k4 = np.zeros(13)
    yt = np.zeros(13)
    trace = np.zeros((NTR, nstep + 1))
    res = np.zeros(len(RES_NAMES))
    imep_prev = 1.0e30
    mu_prev = 1.0e30
    max_cyc = int(P[I_MAX_CYC])
    iv_open = P[I_IV_OPEN]
    iv_dur = P[I_IV_DUR]
    ev_open = P[I_EV_OPEN]
    th_evo = ev_open % 720.0
    cycles_used = 0
    converged = 0.0
    for cyc in range(max_cyc):
        cycles_used = cyc + 1
        for i in range(5, 13):
            y[i] = 0.0
        u_start = y[0] * u_u_f(y[2], cg) + y[1] * u_b_f(y[2], cg)
        m_start = y[0] + y[1] + y[3] * P[I_V_INTAKE] / (R_GAS * T_i) + y[4] * P[I_V_EXH] / (R_GAS * T_ex)
        pmax = 0.0
        thpmax = 0.0
        tmax = 0.0
        t_evo = 0.0
        evo_done = False
        th = 0.0
        for s in range(nstep):
            m = y[0] + y[1]
            if y[0] < 0.0:
                y[0] = 0.0
                m = y[0] + y[1]
            V = Vc + Ap * piston_x(th, r, L)
            p = m * R_GAS * y[2] / V
            xb, _d = wiebe(th, th0, P[I_BURN_DUR], P[I_WIEBE_M]) if P[I_BURN_ON] > 0.5 else (0.0, 0.0)
            trace[0, s] = th
            trace[1, s] = p
            trace[2, s] = y[2]
            trace[3, s] = V
            trace[4, s] = xb
            trace[5, s] = valve_lift(th, iv_open, iv_dur, P[I_LIFT_IN], P[I_CLEAR])
            trace[6, s] = valve_lift(th, ev_open, P[I_EV_DUR], P[I_LIFT_EX], P[I_CLEAR])
            trace[7, s] = y[3]
            trace[8, s] = y[4]
            trace[9, s] = y[0]
            trace[10, s] = y[1]
            trace[11, s] = y[7]
            if p > pmax:
                pmax = p
                thpmax = th
            if y[2] > tmax:
                tmax = y[2]
            if (not evo_done) and th >= th_evo and th_evo > 360.0:
                t_evo = y[2]
                evo_done = True
            phi_prev = (th - iv_open) % 720.0
            rk4_step(th, y, dth, P, D, ref, k1, k2, k3, k4, yt)
            if phi_prev < iv_dur and phi_prev + dth >= iv_dur:
                th_n = th + dth
                m_n = y[0] + y[1]
                v_n = Vc + Ap * piston_x(th_n, r, L)
                ref[REF_P] = m_n * R_GAS * y[2] / v_n
                ref[REF_T] = y[2]
                ref[REF_V] = v_n
                ref[REF_MU] = y[0]
            th += dth
        m = y[0] + y[1]
        V = Vc + Ap * piston_x(th, r, L)
        trace[0, nstep] = th
        trace[1, nstep] = m * R_GAS * y[2] / V
        trace[2, nstep] = y[2]
        trace[3, nstep] = V
        trace[4, nstep] = trace[4, nstep - 1]
        trace[5, nstep] = valve_lift(th, iv_open, iv_dur, P[I_LIFT_IN], P[I_CLEAR])
        trace[6, nstep] = valve_lift(th, ev_open, P[I_EV_DUR], P[I_LIFT_EX], P[I_CLEAR])
        trace[7, nstep] = y[3]
        trace[8, nstep] = y[4]
        trace[9, nstep] = y[0]
        trace[10, nstep] = y[1]
        trace[11, nstep] = y[7]
        imep = y[5] / Vd
        m_end = y[0] + y[1] + y[3] * P[I_V_INTAKE] / (R_GAS * T_i) + y[4] * P[I_V_EXH] / (R_GAS * T_ex)
        u_end = y[0] * u_u_f(y[2], cg) + y[1] * u_b_f(y[2], cg)
        mu_ivc = ref[REF_MU]
        res[R_IMEP] = imep
        res[R_WNET] = y[5]
        res[R_PMAX] = pmax
        res[R_THPMAX] = thpmax
        res[R_MUIVC] = mu_ivc
        res[R_YF] = yf
        res[R_LAM] = lam
        res[R_PIVC] = ref[REF_P]
        res[R_TIVC] = ref[REF_T]
        res[R_KI] = y[7]
        res[R_TEVO] = t_evo
        res[R_QW] = y[6]
        res[R_QC] = y[10]
        res[R_H] = y[11]
        res[R_DU] = u_end - u_start
        res[R_MIN] = y[8]
        res[R_MOUT] = y[9]
        res[R_DMSYS] = m_end - m_start
        res[R_TMAX] = tmax
        res[R_MFUEL] = yf * mu_ivc
        res[R_VE] = mu_ivc * (1.0 - yf) / (rho0 * Vd)
        res[R_THIVC] = D[D_TH_IVC]
        res[R_VIVC] = ref[REF_V]
        res[R_ERES] = (u_end - u_start) - (-y[5] - y[6] + y[10] + y[11])
        res[R_MLEAK] = y[12]
        if cyc >= 3:
            if abs(imep - imep_prev) <= 1.0e-3 * max(abs(imep), 1.0e3) and abs(mu_ivc - mu_prev) <= 2.0e-3 * mu_ivc:
                converged = 1.0
                break
        imep_prev = imep
        mu_prev = mu_ivc
    res[R_CYC] = cycles_used
    res[R_CONV] = converged
    res[R_NSTEP] = nstep
    res[R_DTH] = dth
    return res, trace
