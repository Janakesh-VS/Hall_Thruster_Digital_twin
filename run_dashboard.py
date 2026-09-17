"""
PROMETHEUS dashboard entry point.

Run with:  python run_dashboard.py

Status: PLACEHOLDER — the interactive dashboard (Panels 1-7 + comparison
page, per the master prompt) is built in a later phase. For now this
confirms the geometry layer loads and prints a summary, so the project
is runnable end-to-end from day one.
"""

from src.geometry.geometry import ThrusterGeometry


def main() -> None:
    geom = ThrusterGeometry()
    print("=" * 60)
    print("PROMETHEUS — Adaptive Erosion Control Digital Twin")
    print(f"Geometry config version: {geom.metadata.get('geometry_version')}")
    print("=" * 60)
    print(geom.metadata.get("note", "").strip())
    print()
    print(f"{'Parameter':28s} {'Value (mm)':>12s} {'Value (in)':>12s}  Status")
    print("-" * 70)
    for name, param in geom.params.items():
        if param.unit != "mm":
            continue
        print(f"{name:28s} {param.value:12.3f} {param.as_inch():12.3f}  {param.status}")
    print()
    print("[Dashboard UI not yet implemented — this is the Phase 1/2 skeleton.]")
    print("Next: `pytest` to run geometry validation tests.")


if __name__ == "__main__":
    main()
