import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.physics.hall_thruster import (
    HallThrusterModel,
    OperatingConditions,
    PhysicsValidationError,
)

OPS_YAML = Path(__file__).resolve().parents[1] / "config" / "operating_conditions.yaml"


def base_conditions() -> OperatingConditions:
    return OperatingConditions.from_yaml(OPS_YAML)


# ---------------------------------------------------------------------------
# 1. Increasing discharge voltage increases ideal ion energy
# ---------------------------------------------------------------------------
def test_higher_voltage_increases_ion_energy():
    model = HallThrusterModel()
    low = model.evaluate(replace(base_conditions(), discharge_voltage_V=200.0))
    high = model.evaluate(replace(base_conditions(), discharge_voltage_V=400.0))
    assert high.ion_energy_eV > low.ion_energy_eV


# ---------------------------------------------------------------------------
# 2. Increasing discharge voltage increases ion velocity (v ~ sqrt(V))
# ---------------------------------------------------------------------------
def test_higher_voltage_increases_ion_velocity_like_sqrt():
    model = HallThrusterModel()
    v200 = model.evaluate(replace(base_conditions(), discharge_voltage_V=200.0)).ion_velocity_m_s
    v800 = model.evaluate(replace(base_conditions(), discharge_voltage_V=800.0)).ion_velocity_m_s
    # voltage x4 -> velocity x2 (sqrt scaling), allow generous tolerance
    assert v800 > v200
    assert v800 / v200 == pytest.approx(2.0, rel=0.05)


# ---------------------------------------------------------------------------
# 3. Increasing discharge current increases discharge power
# ---------------------------------------------------------------------------
def test_higher_current_increases_power():
    model = HallThrusterModel()
    low = model.evaluate(replace(base_conditions(), discharge_current_A=2.0))
    high = model.evaluate(replace(base_conditions(), discharge_current_A=8.0))
    assert high.discharge_power_W > low.discharge_power_W


# ---------------------------------------------------------------------------
# 4. Mass flow must never go negative / zero is rejected
# ---------------------------------------------------------------------------
def test_zero_or_negative_mass_flow_rejected():
    model = HallThrusterModel()
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), mass_flow_rate_mg_s=0.0))
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), mass_flow_rate_mg_s=-1.0))


# ---------------------------------------------------------------------------
# 5. Ion velocity must be non-negative
# ---------------------------------------------------------------------------
def test_ion_velocity_non_negative():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert result.ion_velocity_m_s >= 0


# ---------------------------------------------------------------------------
# 6. Ion energy must be non-negative
# ---------------------------------------------------------------------------
def test_ion_energy_non_negative():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert result.ion_energy_eV >= 0


# ---------------------------------------------------------------------------
# 7. Magnetic field must remain finite
# ---------------------------------------------------------------------------
def test_magnetic_field_finite():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert math.isfinite(result.magnetic_field_T)
    assert math.isfinite(result.plasma_state.magnetic_field_axial_T)
    assert math.isfinite(result.plasma_state.magnetic_field_radial_T)


# ---------------------------------------------------------------------------
# 8. No calculation may return NaN or infinity for valid inputs
# ---------------------------------------------------------------------------
def test_all_outputs_finite_for_valid_inputs():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert result.is_finite()


# ---------------------------------------------------------------------------
# 9. Invalid geometry is rejected — covered in test_geometry.py; here we
#    additionally verify the physics layer doesn't silently proceed with
#    an operating point that has zero net accelerating potential.
# ---------------------------------------------------------------------------
def test_voltage_loss_exceeding_discharge_voltage_rejected():
    model = HallThrusterModel()
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), discharge_voltage_V=100.0, voltage_loss_V=150.0))


# ---------------------------------------------------------------------------
# 10. Invalid operating conditions must be rejected
# ---------------------------------------------------------------------------
def test_invalid_mass_utilization_efficiency_rejected():
    model = HallThrusterModel()
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), mass_utilization_efficiency=0.0))
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), mass_utilization_efficiency=1.5))


def test_negative_current_rejected():
    model = HallThrusterModel()
    with pytest.raises(PhysicsValidationError):
        model.evaluate(replace(base_conditions(), discharge_current_A=-1.0))


# ---------------------------------------------------------------------------
# 11. Unit conversion correctness inside the physics pipeline
# ---------------------------------------------------------------------------
def test_mass_flow_unit_conversion_applied_correctly():
    model = HallThrusterModel()
    result = model.evaluate(replace(base_conditions(), mass_flow_rate_mg_s=5.0))
    assert result.mass_flow_rate_kg_s == pytest.approx(5.0e-6)


# ---------------------------------------------------------------------------
# 12. Propellant (ion) mass must be physically valid (i.e. unknown
#     propellant is rejected rather than silently defaulting)
# ---------------------------------------------------------------------------
def test_unknown_propellant_rejected():
    model = HallThrusterModel()
    with pytest.raises(KeyError):
        model.evaluate(replace(base_conditions(), propellant="unobtainium"))


# ---------------------------------------------------------------------------
# Extra: thrust_estimate must never exceed thrust_ideal (efficiency <= 1)
# ---------------------------------------------------------------------------
def test_thrust_estimate_does_not_exceed_ideal():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert result.thrust_estimate_N <= result.thrust_ideal_N + 1e-12


def test_result_carries_model_status_and_assumptions():
    model = HallThrusterModel()
    result = model.evaluate(base_conditions())
    assert result.assumptions
    assert result.model_status
    assert "ion_velocity_m_s" in result.model_status
