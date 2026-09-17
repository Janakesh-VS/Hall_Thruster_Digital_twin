import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.geometry.geometry import (
    GeometryValidationError,
    ThrusterGeometry,
    deg_to_rad,
    inch_to_mm,
    mm_to_inch,
    mm_to_m,
    rad_to_deg,
)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "geometry.yaml"


# ---------------------------------------------------------------------------
# 1. Unit conversion tests
# ---------------------------------------------------------------------------
def test_mm_to_inch_exact():
    assert mm_to_inch(25.4) == pytest.approx(1.0, abs=1e-12)


def test_inch_to_mm_exact():
    assert inch_to_mm(1.0) == pytest.approx(25.4, abs=1e-12)


def test_round_trip_mm_inch():
    original = 42.5
    assert mm_to_inch(inch_to_mm(original)) == pytest.approx(original, abs=1e-9)


def test_mm_to_m():
    assert mm_to_m(1000.0) == pytest.approx(1.0)


def test_deg_rad_round_trip():
    assert rad_to_deg(deg_to_rad(72.0)) == pytest.approx(72.0)


# ---------------------------------------------------------------------------
# 2. Geometry validity tests
# ---------------------------------------------------------------------------
def test_reference_geometry_loads_and_validates():
    geom = ThrusterGeometry(CONFIG_PATH)
    assert geom.params["channel_length"].value > 0


def test_channel_width_is_derived_and_positive():
    geom = ThrusterGeometry(CONFIG_PATH)
    assert geom.channel_width_mm == pytest.approx(
        geom.params["channel_outer_radius"].value - geom.params["channel_inner_radius"].value
    )
    assert geom.channel_width_mm > 0


def test_every_parameter_has_status_tag():
    geom = ThrusterGeometry(CONFIG_PATH)
    valid_statuses = {"SOURCE", "LITERATURE", "ASSUMED", "USER-DEFINED"}
    for name, param in geom.params.items():
        assert param.status in valid_statuses, f"{name} has invalid status {param.status}"


# ---------------------------------------------------------------------------
# 3. Validation-rule tests (each should reject an invalid override)
# ---------------------------------------------------------------------------
def test_rejects_negative_dimension():
    geom = ThrusterGeometry(CONFIG_PATH)
    with pytest.raises(GeometryValidationError):
        geom.override("wall_thickness", -1.0)


def test_rejects_inner_radius_greater_than_outer():
    geom = ThrusterGeometry(CONFIG_PATH)
    with pytest.raises(GeometryValidationError):
        geom.override("channel_inner_radius", 999.0)


def test_rejects_liner_thicker_than_wall():
    geom = ThrusterGeometry(CONFIG_PATH)
    with pytest.raises(GeometryValidationError):
        geom.override("liner_thickness", 100.0)


def test_rejects_liner_radius_outside_channel():
    geom = ThrusterGeometry(CONFIG_PATH)
    with pytest.raises(GeometryValidationError):
        geom.override("liner_radius", 5.0)


def test_rejects_coil_intersecting_channel():
    geom = ThrusterGeometry(CONFIG_PATH)
    with pytest.raises(GeometryValidationError):
        geom.override("coil_inner_radius", 1.0)


def test_valid_override_is_applied_and_marked_user_defined():
    geom = ThrusterGeometry(CONFIG_PATH)
    geom.override("channel_length", 30.0)
    assert geom.params["channel_length"].value == 30.0
    assert geom.params["channel_length"].status == "USER-DEFINED"


def test_invalid_override_does_not_mutate_state():
    geom = ThrusterGeometry(CONFIG_PATH)
    original = geom.params["wall_thickness"].value
    with pytest.raises(GeometryValidationError):
        geom.override("wall_thickness", -5.0)
    assert geom.params["wall_thickness"].value == original


# ---------------------------------------------------------------------------
# 4. Reproducibility test
# ---------------------------------------------------------------------------
def test_loading_twice_gives_identical_reference_values():
    a = ThrusterGeometry(CONFIG_PATH)
    b = ThrusterGeometry(CONFIG_PATH)
    for key in a.params:
        assert a.params[key].value == b.params[key].value


def test_export_to_dict_contains_status_for_every_param():
    geom = ThrusterGeometry(CONFIG_PATH)
    d = geom.to_dict()
    for key, entry in d["parameters"].items():
        assert "status" in entry and entry["status"]
