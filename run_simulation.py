"""
PROMETHEUS headless simulation entry point (no GUI).

Run with:  python run_simulation.py

Status: PLACEHOLDER — the physics/magnetic/plasma/erosion/controller
pipeline (Phases 4-10) is not implemented yet. This currently just loads
and validates the geometry, confirming the "runnable without dashboard"
requirement from day one of the project.
"""

from src.geometry.geometry import ThrusterGeometry


def main() -> None:
    geom = ThrusterGeometry()
    print("Geometry loaded and validated successfully.")
    print(f"Channel width (derived): {geom.channel_width_mm:.3f} mm")
    print("[Physics pipeline not yet implemented — Phases 4-10 pending.]")


if __name__ == "__main__":
    main()
