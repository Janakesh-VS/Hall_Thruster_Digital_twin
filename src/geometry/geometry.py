"""
PROMETHEUS geometry module.

Single source of truth for all thruster dimensions. Loads
config/geometry.yaml, exposes dimensions in SI units (metres) for physics
code, and provides exact mm <-> inch conversion for display purposes.

Design rules (from project master prompt):
  - No dimension is hard-coded here; every value comes from geometry.yaml.
  - Every parameter carries its `status` (SOURCE / LITERATURE / ASSUMED /
    USER-DEFINED) so the UI can flag reference/assumed values honestly.
  - All internal physics calculations use SI units (metres, radians).
  - Display/UI layers convert to mm or inch as needed; conversion is exact
    (1 inch = 25.4 mm, no rounding at the conversion step).
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

MM_PER_INCH = 25.4  # exact, by definition


# ---------------------------------------------------------------------------
# Unit conversion helpers (exact — no internal rounding)
# ---------------------------------------------------------------------------
def mm_to_inch(value_mm: float) -> float:
    """Exact mm -> inch conversion."""
    return value_mm / MM_PER_INCH


def inch_to_mm(value_in: float) -> float:
    """Exact inch -> mm conversion."""
    return value_in * MM_PER_INCH


def mm_to_m(value_mm: float) -> float:
    return value_mm / 1000.0


def deg_to_rad(value_deg: float) -> float:
    return math.radians(value_deg)


def rad_to_deg(value_rad: float) -> float:
    return math.degrees(value_rad)


# ---------------------------------------------------------------------------
# Parameter wrapper: keeps value + provenance together everywhere
# ---------------------------------------------------------------------------
@dataclass
class Parameter:
    name: str
    value: Any
    unit: str
    source: str
    status: str
    description: str = ""

    def as_mm(self) -> float:
        if self.unit != "mm":
            raise ValueError(f"Parameter '{self.name}' is not stored in mm (unit={self.unit})")
        return float(self.value)

    def as_m(self) -> float:
        return mm_to_m(self.as_mm())

    def as_inch(self) -> float:
        return mm_to_inch(self.as_mm())

    def display(self, unit_system: str = "mm") -> str:
        if self.unit == "mm":
            if unit_system == "inch":
                return f"{mm_to_inch(self.value):.3f} in"
            return f"{self.value:.3f} mm"
        if self.unit == "deg":
            return f"{self.value:.2f} deg"
        return f"{self.value} {self.unit}"


class GeometryValidationError(ValueError):
    """Raised when the loaded/edited geometry violates a physical constraint."""


# ---------------------------------------------------------------------------
# Main geometry model
# ---------------------------------------------------------------------------
class ThrusterGeometry:
    """
    Loads config/geometry.yaml and exposes a validated, unit-aware geometry
    model. This is the ONLY place geometry should be read from; downstream
    modules (magnetic, plasma, erosion, visualization) must go through this
    class rather than re-reading the YAML or hard-coding dimensions.
    """

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[2] / "config" / "geometry.yaml"
        self.config_path = Path(config_path)
        self._raw: dict = {}
        self.params: dict[str, Parameter] = {}
        self.sensors: dict[str, dict[str, Parameter]] = {}
        self.discretization: dict[str, Parameter] = {}
        self.metadata: dict = {}
        self.load()

    # -- loading -----------------------------------------------------------
    def load(self) -> None:
        with open(self.config_path, "r") as f:
            self._raw = yaml.safe_load(f)

        self.metadata = self._raw.get("metadata", {})

        skip_keys = {"metadata", "sensors", "discretization"}
        self.params = {}
        for key, entry in self._raw.items():
            if key in skip_keys:
                continue
            self.params[key] = self._parse_param(key, entry)

        self.sensors = {}
        for sensor_name, sensor_fields in self._raw.get("sensors", {}).items():
            self.sensors[sensor_name] = {
                field_name: self._parse_param(f"{sensor_name}.{field_name}", entry)
                for field_name, entry in sensor_fields.items()
            }

        self.discretization = {
            key: self._parse_param(key, entry)
            for key, entry in self._raw.get("discretization", {}).items()
        }

        self.validate()

    @staticmethod
    def _parse_param(name: str, entry: dict) -> Parameter:
        return Parameter(
            name=name,
            value=entry["value"],
            unit=entry["unit"],
            source=entry["source"],
            status=entry["status"],
            description=entry.get("description", "").strip(),
        )

    # -- derived quantities --------------------------------------------------
    @property
    def channel_width_mm(self) -> float:
        return self.params["channel_outer_radius"].as_mm() - self.params["channel_inner_radius"].as_mm()

    # -- validation (master prompt "DIMENSIONAL ACCURACY" section) ---------
    def validate(self) -> None:
        errors: list[str] = []
        p = self.params

        def mm(key: str) -> float:
            return p[key].as_mm()

        # no negative dimensions
        for key, param in p.items():
            if param.unit == "mm" and isinstance(param.value, (int, float)) and param.value < 0:
                errors.append(f"'{key}' is negative ({param.value} mm).")

        # inner radius < outer radius (channel)
        if mm("channel_inner_radius") >= mm("channel_outer_radius"):
            errors.append("channel_inner_radius must be < channel_outer_radius.")

        # inner radius < outer radius (coils, poles)
        if mm("coil_inner_radius") >= mm("coil_outer_radius"):
            errors.append("coil_inner_radius must be < coil_outer_radius.")
        if mm("inner_pole_radius") >= mm("outer_pole_radius"):
            errors.append("inner_pole_radius must be < outer_pole_radius.")

        # wall thickness > 0
        if mm("wall_thickness") <= 0:
            errors.append("wall_thickness must be > 0.")

        # liner must fit within the channel wall with minimum clearance
        clearance = mm("mechanical_clearance_min")
        if mm("liner_thickness") + clearance > mm("wall_thickness"):
            errors.append(
                f"liner_thickness ({mm('liner_thickness')} mm) + minimum clearance "
                f"({clearance} mm) exceeds wall_thickness ({mm('wall_thickness')} mm)."
            )

        # liner radius must lie within the channel
        if not (mm("channel_inner_radius") < mm("liner_radius") < mm("channel_outer_radius")):
            errors.append("liner_radius must lie strictly between channel_inner_radius and channel_outer_radius.")

        # liner axial length must not exceed channel length
        if mm("liner_axial_length") > mm("channel_length"):
            errors.append("liner_axial_length must not exceed channel_length.")

        # coil geometry must not intersect the discharge channel
        if mm("coil_inner_radius") < mm("channel_outer_radius"):
            errors.append(
                "coil_inner_radius must be >= channel_outer_radius (coils must not intersect the channel)."
            )

        # sensor positions must lie within a physically valid range
        for sensor_name, fields in self.sensors.items():
            axial = fields.get("axial_position")
            radial = fields.get("radial_position")
            if axial is not None and not (0.0 <= axial.as_mm() <= mm("channel_length") + 1e-9):
                errors.append(f"Sensor '{sensor_name}' axial_position lies outside [0, channel_length].")
            if radial is not None and not (
                mm("channel_inner_radius") - 1e-9 <= radial.as_mm() <= mm("coil_outer_radius") + 1e-9
            ):
                errors.append(f"Sensor '{sensor_name}' radial_position lies outside a plausible radial range.")

        if errors:
            raise GeometryValidationError(
                "Geometry validation failed with the following issue(s):\n- " + "\n- ".join(errors)
            )

    # -- editing -------------------------------------------------------------
    def override(self, name: str, value: float, status: str = "USER-DEFINED") -> None:
        """
        Apply a user/judge override to a single geometry parameter (mm-valued
        parameters only), re-validate, and raise GeometryValidationError
        (without applying the change) if the result would be invalid.
        """
        if name not in self.params:
            raise KeyError(f"Unknown geometry parameter: {name}")

        backup = copy.deepcopy(self.params)
        self.params[name].value = value
        self.params[name].status = status
        try:
            self.validate()
        except GeometryValidationError:
            self.params = backup
            raise

    # -- export ---------------------------------------------------------------
    def to_dict(self, unit_system: str = "mm") -> dict:
        out = {"metadata": self.metadata, "parameters": {}, "sensors": {}, "discretization": {}}
        for key, param in self.params.items():
            out["parameters"][key] = {
                "value": param.value,
                "display": param.display(unit_system),
                "unit": param.unit,
                "source": param.source,
                "status": param.status,
                "description": param.description,
            }
        for sensor_name, fields in self.sensors.items():
            out["sensors"][sensor_name] = {
                fname: {
                    "value": fparam.value,
                    "display": fparam.display(unit_system),
                    "unit": fparam.unit,
                    "status": fparam.status,
                }
                for fname, fparam in fields.items()
            }
        for key, param in self.discretization.items():
            out["discretization"][key] = param.value
        out["derived"] = {"channel_width_mm": self.channel_width_mm}
        return out


if __name__ == "__main__":
    geom = ThrusterGeometry()
    print(f"Loaded geometry v{geom.metadata.get('geometry_version')}")
    print(f"Channel width (derived): {geom.channel_width_mm:.3f} mm")
    print(f"Channel length: {geom.params['channel_length'].display()} "
          f"({geom.params['channel_length'].display('inch')})")
    print("Validation: OK")
