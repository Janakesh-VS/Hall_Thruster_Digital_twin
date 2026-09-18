"""
PROMETHEUS dashboard entry point.

Run with:  python run_dashboard.py

Status: MINIMAL FUNCTIONAL VIEWER, not the final Panels 1-7 dashboard
(that's Phase 11, and will likely be Dash or Streamlit). Per the master
prompt's instruction to keep this "a minimal functional viewer rather than
a fake finished dashboard" until the architecture is ready for it, this
script currently:

  1. Prints the reference geometry (with status tags).
  2. Evaluates the reduced-order physics model at the reference operating
     point and prints the results.
  3. Generates results/digital_twin_3d.html — a self-contained, offline-
     viewable 3D digital twin driven by that geometry + physics state.
     Open it in any browser.
"""

from pathlib import Path

from src.geometry.geometry import ThrusterGeometry
from src.geometry.liner_geometry import LinerController
from src.geometry.visualization import ThrusterVisualization3D, save_html
from src.physics.hall_thruster import HallThrusterModel, OperatingConditions

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def main() -> None:
    geom = ThrusterGeometry()

    print("=" * 70)
    print("PROMETHEUS — Adaptive Erosion Control Digital Twin")
    print(f"Geometry config version: {geom.metadata.get('geometry_version')}")
    print("REFERENCE / ASSUMED GEOMETRY — NOT FLIGHT-HARDWARE DIMENSIONS")
    print("=" * 70)

    print(f"\n{'Parameter':28s} {'Value (mm)':>12s} {'Value (in)':>12s}  Status")
    print("-" * 72)
    for name, param in geom.params.items():
        if param.unit != "mm":
            continue
        print(f"{name:28s} {param.value:12.3f} {param.as_inch():12.3f}  {param.status}")

    conditions = OperatingConditions.from_yaml()
    model = HallThrusterModel()
    result = model.evaluate(conditions)

    print(f"\n{'--- Reduced-order Hall-thruster physics ---':s}")
    print(f"Vd={result.discharge_voltage_V:.0f} V  Id={result.discharge_current_A:.2f} A  "
          f"P={result.discharge_power_W:.0f} W  B={result.magnetic_field_T*1000:.1f} mT")
    print(f"Ion velocity (modelled): {result.ion_velocity_m_s:,.0f} m/s")
    print(f"Ion energy (modelled):   {result.ion_energy_eV:.0f} eV")
    print(f"Thrust (estimate):       {result.thrust_estimate_N*1000:.2f} mN")
    print(f"Isp (estimate):          {result.isp_estimate_s:.0f} s")

    liner = LinerController(geom)
    liner.set_liner_angle(45.0)  # arbitrary demo angle for the viewer

    viz = ThrusterVisualization3D(geometry=geom, liner_state=liner.state, physics_result=result)
    fig = viz.build()
    out_path = save_html(fig, RESULTS_DIR / "digital_twin_3d.html")

    print()
    print(f"3D digital twin written to: {out_path}")
    print("Open this file in any web browser (fully offline, no server needed).")
    print()
    print("[Full Panels 1-7 dashboard UI: Phase 11 pending.]")
    print("Run `python run_simulation.py` for the headless physics-only path,")
    print("or `pytest` to run all verification tests.")


if __name__ == "__main__":
    main()
