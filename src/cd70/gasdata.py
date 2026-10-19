"""Gas property tables (loaded once). Made by scripts/derive_gas_props.py with Cantera.

T_K       uniform temperature grid, K
CV_U/U_U  unburned charge (air + fuel vapour): cv in J/kg/K, sensible energy in J/kg (zero at 300 K)
CV_B/U_B  burned gas (equilibrium products, includes dissociation): same units

If you regenerate the .npz file, delete src/cd70/__pycache__ so Numba recompiles.
"""

from pathlib import Path

import numpy as np

_DATA = np.load(Path(__file__).resolve().parent / "data" / "gas_tables.npz")

T_K = np.ascontiguousarray(_DATA["T_k"], dtype=np.float64)
CV_U = np.ascontiguousarray(_DATA["cv_u"], dtype=np.float64)
U_U = np.ascontiguousarray(_DATA["u_u"], dtype=np.float64)
CV_B = np.ascontiguousarray(_DATA["cv_b"], dtype=np.float64)
U_B = np.ascontiguousarray(_DATA["u_b"], dtype=np.float64)

T0_TAB = float(T_K[0])
DT_TAB = float(T_K[1] - T_K[0])
N_TAB = int(T_K.size)
