"""
PROMETHEUS headless simulation entry point (no GUI).

Run with:  python run_simulation.py

Status: Phases 1-4 implemented (geometry + reduced-order Hall-thruster
physics). Erosion, magnetic-field (beyond a scalar model input), and
controller pipelines (Phases 5-10) are not implemented yet.

This script:
  1. Loads and validates the reference geometry (config/geometry.yaml).
  2. Loads the reference/assumed operating point (config/operating_conditions.yaml).
  3. Evaluates the reduced-order Hall-thruster physics model.
  4. Exports a reproducible reference case to results/reference_case.json
     and results/reference_case.csv.

Nothing here is presented as an experimentally validated result — see the
"model_status" and "assumptions" fields in the exported JSON.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.geometry.geometry import ThrusterGeometry
from src.physics.hall_thruster import HallThrusterModel, OperatingConditions

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def export_reference_case(geometry: ThrusterGeometry, conditions: OperatingConditions, result) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "geometry_version": geometry.metadata.get("geometry_version"),
        "model_status_note": (
            "Digital-twin numerical result. Geometry is REFERENCE/ASSUMED "
            "(not flight hardware). Physics is a REDUCED-ORDER model. "
            "NOT experimentally validated."
        ),
        "operating_conditions": {
            "propellant": conditions.propellant,
            "discharge_voltage_V": conditions.discharge_voltage_V,
            "discharge_current_A": conditions.discharge_current_A,
            "mass_flow_rate_mg_s": conditions.mass_flow_rate_mg_s,
            "magnetic_field_T": conditions.magnetic_field_T,
            "voltage_loss_V": conditions.voltage_loss_V,
            "mass_utilization_efficiency": conditions.mass_utilization_efficiency,
        },
        "geometry_key_dimensions_mm": {
            name: geometry.params[name].value
            for name in (
                "channel_length", "channel_inner_radius", "channel_outer_radius",
                "liner_radius", "liner_thickness", "wall_thickness",
            )
        },
        "results": result.to_dict(),
    }

    json_path = RESULTS_DIR / "reference_case.json"
    with open(json_path, "w") as f:
        json.dump(record, f, indent=2)

    csv_path = RESULTS_DIR / "reference_case.csv"
    flat = {
        "timestamp_utc": record["timestamp_utc"],
        "geometry_version": record["geometry_version"],
        **{f"input.{k}": v for k, v in record["operating_conditions"].items()},
        **{f"geometry.{k}_mm": v for k, v in record["geometry_key_dimensions_mm"].items()},
        **{f"output.{k}": v for k, v in result.to_dict().items() if k not in ("assumptions", "model_status")},
    }
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(flat.keys()))
        writer.writeheader()
        writer.writerow(flat)

    print(f"Exported: {json_path}")
    print(f"Exported: {csv_path}")


def main() -> None:
    geom = ThrusterGeometry()
    print("Geometry loaded and validated successfully.")
    print(f"Channel width (derived): {geom.channel_width_mm:.3f} mm")

    conditions = OperatingConditions.from_yaml()
    model = HallThrusterModel()
    result = model.evaluate(conditions)

    print()
    print("--- Reduced-order Hall-thruster physics (reference operating point) ---")
    print(f"Propellant:            {result.propellant}")
    print(f"Discharge voltage:     {result.discharge_voltage_V:.1f} V")
    print(f"Discharge current:     {result.discharge_current_A:.2f} A")
    print(f"Discharge power:       {result.discharge_power_W:.1f} W")
    print(f"Ion velocity:          {result.ion_velocity_m_s:,.1f} m/s   [MODELLED]")
    print(f"Ion energy:            {result.ion_energy_eV:.1f} eV       [MODELLED]")
    print(f"Ion flux:              {result.ion_flux_particles_s:.3e} particles/s [ESTIMATED]")
    print(f"Thrust (ideal):        {result.thrust_ideal_N * 1000:.2f} mN   [IDEAL, no losses]")
    print(f"Thrust (estimate):     {result.thrust_estimate_N * 1000:.2f} mN   [ESTIMATED]")
    print(f"Isp (estimate):        {result.isp_estimate_s:.1f} s       [ESTIMATED]")
    print(f"All outputs finite:    {result.is_finite()}")

    export_reference_case(geom, conditions, result)

    print()
    print("[Erosion, full magnetic-field, and controller pipeline: Phases 5-10 pending.]")


if __name__ == "__main__":
    main()
