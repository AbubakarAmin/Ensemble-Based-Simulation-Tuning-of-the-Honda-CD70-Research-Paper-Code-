# Model specification (what src/cd70/kernel.py computes)

Single-cylinder, 4-stroke, zero-dimensional (thermodynamic) cycle simulation. Crank angle 0..720 deg; 0 = TDC at start of intake, 360 = firing TDC.
Integrated with fixed-step RK4 (step <= 1 deg and <= 25 microseconds); repeated until indicated work and trapped mass converge (4 to 14 cycles). Numba-compiled, about 15-30 ms per engine point.

## State and sub-models
- Cylinder: unburned mass, burned mass, one temperature. Gas properties from Cantera tables (unburned = air + propane/methane surrogate vapour at lambda 0.9, burned = equilibrium products incl. dissociation), built by `scripts/derive_gas_props.py` into `src/cd70/data/gas_tables.npz`.
- Intake plenum (isothermal, volume v_intake, carburettor venturi/throttle as compressible orifice), exhaust plenum (isothermal, 900 K assumed, muffler orifice). Intake charge heating `charge_heat_k`.
- Valves: lift = Lmax sin^2(pi phi / duration) minus clearance; flow area = min(curtain area, throat area (0.92 head diameter)); compressible orifice flow with discharge coefficient `cd_scale`.
- Combustion: Wiebe burn (a = 6.908, shape `wiebe_m`, duration `burn_dur_deg`), spark delay `spark_delay_deg`, combustion efficiency `eta_comb` x mixture factor. Mixture lambda is a function of throttle (idle / cruise / full-load values; main-jet size changes fuel flow by (jet/jet_true)^2 at high load).
- Heat transfer: Woschni (assumed constants). Wall temperature offset `t_wall_offset_k`.
- Friction: Chen-Flynn (assumed coefficients) x `fmep_scale`. Brake torque = indicated net work minus friction.
- Blow-by: orifice leak `leak_area_mm2` (mass leaves the cylinder when p > ambient).
- Knock: Douaud-Eyzat / Livengood-Wu integral on the unburned zone (isentropic from intake closing). Index scaled so the baseline at calibration conditions has max index = `knock_margin_base`. KI is a diagnostic: it never feeds back into the cycle. Octane dependence and ambient temperature enter through the correlation.
- Ignition: three-point advance curve (low-speed, 4000 rpm, above) with design offsets.

## Vehicle (src/cd70/vehicle.py)
Gears 3.272/1.937/1.350/1.043, primary 3.722, final drive 41/14, rolling radius 0.279 m, road-load terms are uncertain inputs (nominal: mass 155 kg bike + rider, range 140-170; Crr 0.02, range 0.014-0.030; CdA 0.45 m2, range 0.25-0.65; drivetrain efficiency 0.86, range 0.80-0.92). Road-load inputs (drag area, rolling resistance, mass, drivetrain efficiency) and the speedometer over-read are uncertain inputs. Top speed uses the WOT power at 12 points to 7500 rpm plus 8000-9500 rpm (extrapolation). Cruise throttle solved by root finding so engine torque equals road load. 0-60 km/h time (indicative) and gear-limited top speed (reported only).

## Verified by tests (tests/locked/test_kernel.py)
Geometry, valve events, motoring isentropic compression (spread 6e-11), Otto efficiency within 0.03% of theory, energy closure (residual/Qc ~ 2e-6), mass balance incl. leak, step-size independence (~2e-6), knock scaling laws, throttle monotonic, no NaN across a grid.

## What is assumed, not measured
Friction constants, exhaust temperature and plenum volumes, Woschni constants, knock constants, discharge coefficients, valve lift (6.5 mm, 6-7 range), spark delay, burn duration. These are either calibrated (ranges in config/priors.yaml group CAL) or carried as uncertainty (group SPEC).
