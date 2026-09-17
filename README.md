# PROMETHEUS — Adaptive Erosion Control Digital Twin
### Smart India Hackathon 2026 · Problem Statement SIH26226 · Team Prometheus

A transparent, parameterized, physics-informed digital twin of an adaptive
erosion-control architecture for Hall-effect thrusters — combining magnetic
field shaping, a rotating dielectric channel liner, and closed-loop control.

**This is a numerical demonstrator, not experimentally validated hardware.**
See `docs/VALIDATION.md` (added in a later phase) for what is verified,
literature-consistent, simulation-based, or still requiring experimental
validation.

## Status: Phase 1 & 2 of 15 complete

- [x] Phase 1 — Project architecture + configuration system
- [x] Phase 2 — Parameterized geometry (`config/geometry.yaml`, `src/geometry/`)
- [ ] Phase 3 — 3D visualization
- [ ] Phase 4 — Hall-thruster reduced-order physics model
- [ ] Phase 5 — Magnetic-field model
- [ ] Phase 6 — Rotating liner kinematics
- [ ] Phase 7 — Plasma-wall exposure model
- [ ] Phase 8 — Erosion model
- [ ] Phase 9 — Adaptive controller
- [ ] Phase 10 — Four-case comparison (baseline vs. PROMETHEUS)
- [ ] Phase 11 — Dashboard
- [ ] Phase 12 — Verification tests (expanding on Phase 2's geometry tests)
- [ ] Phase 13 — Validation / literature cross-check page
- [ ] Phase 14 — SIH demo mode
- [ ] Phase 15 — Documentation (auto-generated technical report)

## What's here right now

```
prometheus/
├── app/                    # dashboard (empty until Phase 11)
├── src/
│   └── geometry/
│       └── geometry.py     # ThrusterGeometry: loads, validates, converts units
├── config/
│   └── geometry.yaml       # single source of truth for every dimension,
│                           # each tagged SOURCE / LITERATURE / ASSUMED / USER-DEFINED
├── tests/
│   └── test_geometry.py    # unit conversion + validation-rule tests
├── run_dashboard.py        # placeholder — prints geometry summary for now
├── run_simulation.py       # placeholder — headless geometry load/validate
└── requirements.txt
```

## Running it

```bash
pip install -r requirements.txt

python run_dashboard.py      # prints the current reference geometry
python run_simulation.py     # headless: loads + validates geometry
pytest                       # runs geometry validation & unit-conversion tests
```

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

Phase 3 (3D visualization) will render this geometry interactively and add
the liner-rotation and cross-section views described in the master prompt.
