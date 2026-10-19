"""Derive gas property tables with Cantera and save them to src/cd70/data/gas_tables.npz.

Needs `pip install cantera`. The agent does NOT need to run this: the .npz file is committed.
Run only if data/gas_tables.npz is lost. Output arrays:
  T_k        temperature grid (K), uniform step
  cv_u, u_u  unburned charge (air + iso-octane vapour, lambda 0.90): cv in J/kg/K, sensible u in J/kg (zero at 300 K)
  cv_b, u_b  burned gas (equilibrium products at 40 bar, lambda 1.0, includes dissociation): same units
Reference: iso-octane as gasoline surrogate, GRI-free species set from Cantera's gri30 (contains C3 max, so
iso-octane is replaced by the heat-capacity-equivalent mix described below).
"""
from pathlib import Path

import cantera as ct
import numpy as np

OUT = Path(__file__).resolve().parents[1] / "src" / "cd70" / "data" / "gas_tables.npz"
T_GRID = np.arange(250.0, 3501.0, 10.0)
R_SPEC = 287.0

# --- unburned: air + fuel vapour. gri30 has no C8, so use n-heptane-like heat capacity by mixing
# CH4/C3H8 as a surrogate with the same carbon-to-hydrogen ratio of gasoline (~C8H15).
# Simple and reproducible: 85 mass percent propane + 15 percent methane has cp close to gasoline vapour at 400-700 K.
gas = ct.Solution("gri30.yaml")
lam = 0.90
afr_st = 14.7
y_f = 1.0 / (1.0 + afr_st * lam)


def mix_unburned(T):
    gas.TPY = T, 1.0e5, "O2:0.2329, N2:0.7671"  # air by mass
    air_y = gas.Y.copy()
    gas.TPY = T, 1.0e5, "C3H8:0.85, CH4:0.15"
    fuel_y = gas.Y.copy()
    y = (1.0 - y_f) * air_y + y_f * fuel_y
    gas.TPY = T, 1.0e5, y
    return gas.cv_mass


cv_u = np.array([mix_unburned(T) for T in T_GRID])

# --- burned: equilibrium products, lambda 1, at 40 bar: cv_eq via finite differences at constant volume
eq = ct.Solution("gri30.yaml")
phi = 1.0 / 1.0
eq.set_equivalence_ratio(phi, "C3H8:0.85, CH4:0.15", "O2:1, N2:3.76")


def u_eq(T, rho):
    eq.TD = T, rho
    eq.equilibrate("TV")
    return eq.u / eq.mean_molecular_weight * eq.mean_molecular_weight  # J/kg via mass basis below


def cv_equilibrium(T, p_ref=40.0e5):
    eq.TP = T, p_ref
    rho = eq.density
    h = 5.0
    eq.TD = T - h, rho
    eq.equilibrate("TV")
    u1 = eq.int_energy_mass
    eq.TD = T + h, rho
    eq.equilibrate("TV")
    u2 = eq.int_energy_mass
    return (u2 - u1) / (2 * h)


cv_b = np.array([cv_equilibrium(T) for T in T_GRID])

# sensible energies, zero at 300 K, by trapezoid integration on the uniform grid
def cumulative(cv):
    u = np.concatenate([[0.0], np.cumsum(0.5 * (cv[1:] + cv[:-1]) * np.diff(T_GRID))])
    i300 = int(np.argmin(np.abs(T_GRID - 300.0)))
    return u - u[i300]


u_u = cumulative(cv_u)
u_b = cumulative(cv_b)
np.savez(OUT, T_k=T_GRID, cv_u=cv_u, u_u=u_u, cv_b=cv_b, u_b=u_b)
print("saved", OUT)
print("cv_u 300/1000/2000 K:", np.interp([300, 1000, 2000], T_GRID, cv_u))
print("cv_b 300/1000/2000/3000 K:", np.interp([300, 1000, 2000, 3000], T_GRID, cv_b))
print("gamma_u 600 K:", np.interp(600, T_GRID, cv_u) and (np.interp(600, T_GRID, cv_u) + R_SPEC) / np.interp(600, T_GRID, cv_u))
