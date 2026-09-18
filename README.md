# PROMETHEUS — Adaptive Erosion Control Digital Twin
### Smart India Hackathon 2026 · Problem Statement SIH26226 · Team Prometheus

A transparent, parameterized, physics-informed digital twin of an adaptive
erosion-control architecture for Hall-effect thrusters — combining magnetic
field shaping, a rotating dielectric channel liner, and closed-loop control.

**This is a numerical demonstrator, not experimentally validated hardware.**
See `docs/VALIDATION.md` (added in a later phase) for what is verified,
literature-consistent, simulation-based, or still requiring experimental
validation.

## Status: Phase 1-4 of 15 complete

- [x] Phase 1 — Project architecture + configuration system
- [x] Phase 2 — Parameterized geometry (`config/geometry.yaml`, `src/geometry/`)
- [x] Phase 3 — 3D digital-twin visualization (`src/geometry/visualization.py`), driven by geometry + physics state
- [x] Phase 4 — Hall-thruster reduced-order physics model (`src/physics/`), equations cited in `docs/EQUATIONS.md`
- [ ] Phase 5 — Full magnetic-field model (currently a scalar model-input placeholder, `src/magnetic/interface.py`)
- [ ] Phase 6 — Rotating liner kinematics (currently instantaneous `set_liner_angle()` only, `src/geometry/liner_geometry.py`)
- [ ] Phase 7 — Plasma-wall exposure model
- [ ] Phase 8 — Erosion model
- [ ] Phase 9 — Adaptive controller
- [ ] Phase 10 — Four-case comparison (baseline vs. PROMETHEUS)
- [ ] Phase 11 — Full dashboard (Panels 1-7 + comparison page); `run_dashboard.py` is currently a minimal functional viewer
- [x] Phase 12 (partial) — 43 automated tests passing (geometry, units, physics sanity checks, visualization)
- [ ] Phase 13 — Validation / literature cross-check page
- [ ] Phase 14 — SIH demo mode
- [ ] Phase 15 — Documentation (auto-generated technical report; `docs/EQUATIONS.md` written manually so far)

## What's here right now

```
prometheus/
├── app/                          # full dashboard (empty until Phase 11)
├── src/
│   ├── geometry/
│   │   ├── geometry.py           # ThrusterGeometry: loads, validates, converts units
│   │   ├── liner_geometry.py     # LinerController: theta state + motion-limit checks
│   │   └── visualization.py      # ThrusterVisualization3D: builds the 3D digital twin
│   ├── physics/
│   │   ├── units.py               # explicit, tested unit conversions
│   │   ├── propellants.py         # Xe/Kr/Ar properties from config/physics.yaml
│   │   ├── plasma_state.py        # PlasmaState / HallThrusterResult schemas
│   │   └── hall_thruster.py       # the reduced-order physics model (equations cited inline)
│   └── magnetic/
│       └── interface.py           # MagneticFieldSpec — placeholder for Phase 5
├── config/
│   ├── geometry.yaml               # every dimension, tagged SOURCE/LITERATURE/ASSUMED/USER-DEFINED
│   ├── physics.yaml                 # physical constants + propellant properties (tagged SOURCE)
│   └── operating_conditions.yaml    # reference operating point (tagged, see file header)
├── results/
│   ├── reference_case.json/.csv     # reproducible reference simulation (written by run_simulation.py)
│   └── digital_twin_3d.html         # self-contained 3D viewer (written by run_dashboard.py)
├── docs/
│   └── EQUATIONS.md                 # every Phase 4 equation, with its literature source
├── tests/                            # 43 tests: geometry, units, physics sanity, visualization
├── run_dashboard.py                  # minimal functional viewer: geometry + physics + 3D HTML
├── run_simulation.py                 # headless: geometry + physics + reference-case export
└── requirements.txt
```

## Running it

```bash
pip install -r requirements.txt

python run_dashboard.py      # prints geometry + physics, writes results/digital_twin_3d.html
                              # -> open that HTML file in any browser (fully offline)
python run_simulation.py     # headless: geometry + physics, exports results/reference_case.{json,csv}
pytest                       # runs all 43 tests
```

## On the physics

`src/physics/hall_thruster.py` implements a **reduced-order (0-D)** model —
ion exhaust velocity, ion energy, discharge power, ion flux, thrust, and
Isp — at a single operating point. Every equation is cited to a primary
source (mainly Boeuf & Garrigues, arXiv:0810.3994) in the module docstring
and in `docs/EQUATIONS.md`. Every result carries `model_status` labels
(`MODELLED` / `ESTIMATED` / `IDEAL` / `MODEL INPUT`) so nothing is
displayed as more certain than it is. This is **not** a kinetic/PIC plasma
simulation and **not** an experimentally validated result.

## On the geometry values

The SIH presentation defines the **concept and system architecture** but does
**not** provide a dimensioned engineering drawing of PROMETHEUS. Rather than
silently inventing "real" dimensions, `config/geometry.yaml` tags every value:

| Status | Meaning |
|---|---|
| `SOURCE` | Taken from a specific cited drawing/document |
| `LITERATURE` | Order-of-magnitude value consistent with published Hall-thruster designs (e.g. SPT-100-class channel dimensions), used to keep the reference geometry physically plausible |
| `ASSUMED` | Chosen by the team for this reference geometry, no external source |
| `USER-DEFINED` | Overridden via the dashboard/API at runtime |

Every dimension is editable; `ThrusterGeometry.override()` re-validates
(radii ordering, liner-fits-in-wall, coil/channel non-intersection, sensor
placement, etc.) before accepting a change, and rolls back on failure.

## Next step

Phase 5 (magnetic-field model) will replace the scalar `MagneticFieldSpec`
placeholder in `src/magnetic/interface.py` with a real reduced-order or
FEMM-derived field computed from coil current/geometry, feeding directly
into the plasma-wall exposure model in Phase 7.
