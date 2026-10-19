# Design notes (pack author, not for the agent)

Related work checked on 10 Oct 2026:
- LEAP 71 Noyron: a proprietary "computational engineering model" that encodes physics, design rules and manufacturing constraints into code and produces engine hardware (liquid rocket engines, heat exchangers) automatically. Not available; the transferable idea is the rule layer + closed automatic loop. Implemented as `rules.py`, `study.eval_checked`, task gates.
- PicoGK (Apache-2.0, C#/.NET voxel geometry kernel) and LEAP71_ShapeKernel: geometry generation for 3D-printed parts; no thermodynamics. Not useful until a geometry/CFD study of the CD70 ports exists. Future work: parametric port geometry -> OpenFOAM discharge coefficients to replace the `cd_scale` calibration parameter.
- NovaTurbo (MIT, Python, PyTorch surrogate + NSGA-II + Brayton cycle for micro turbojets): same pattern (surrogate + NSGA-II + physics + validation) but for gas turbines. Confirms our pattern; no reusable piston-engine code.
- OpenFOAM: 3-D CFD. Needs real geometry and hours per cycle; infeasible for thousands of designs on 8 GB; would not remove the main uncertainty (unknown engine details).
- jlk.ae (Josefine Lissner and Lin Kayser, founders of LEAP 71): background reading on computational engineering and implicit modelling.

Decision: own 0-D kernel (tested against textbook limits) + reuse libraries; make the uncertainty the object of study.
