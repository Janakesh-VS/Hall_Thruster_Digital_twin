"""
Structured result schema for the reduced-order Hall-thruster physics model.

Only fields that are actually calculated are populated; nothing here is a
placeholder filled with an invented number. `model_status` and
`assumptions` travel with every result so downstream consumers (3D
visualization, dashboard, future erosion model) can display honestly what
kind of number they are looking at.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlasmaState:
    """
    Reduced-order plasma state at a single operating point. This is NOT a
    spatially resolved plasma solution — it is a 0-D (single-point,
    steady-state) description consistent with the "reduced-order, not full
    kinetic" scope of Phase 4.
    """
    ion_velocity_m_s: float          # MODELLED (Boeuf & Garrigues, eq. 2.17)
    ion_energy_eV: float             # MODELLED (= e * (Vd - voltage_loss), i.e. q*(Vd-Delta))
    ion_flux_particles_s: float      # ESTIMATED (from mass flow, utilization, charge state)
    magnetic_field_T: float          # MODEL INPUT (not computed — Phase 5 placeholder)
    magnetic_field_axial_T: float    # MODEL INPUT
    magnetic_field_radial_T: float   # MODEL INPUT
    discharge_voltage_V: float       # MODEL INPUT
    discharge_current_A: float       # MODEL INPUT
    mass_flow_rate_kg_s: float       # MODEL INPUT


@dataclass
class HallThrusterResult:
    """
    Full output of one reduced-order Hall-thruster evaluation. Every field
    is either a MODEL INPUT (operator-set), MODELLED (calculated from a
    literature equation), or ESTIMATED (calculated with an additional
    ASSUMED efficiency factor). `model_status` records which is which so
    nothing is displayed as more certain than it is.
    """
    propellant: str
    discharge_voltage_V: float
    discharge_current_A: float
    discharge_power_W: float
    mass_flow_rate_kg_s: float
    magnetic_field_T: float

    ion_velocity_m_s: float          # MODELLED
    ion_energy_eV: float             # MODELLED
    ion_flux_particles_s: float      # ESTIMATED
    thrust_ideal_N: float            # IDEAL (all mass flow converted, no efficiency losses)
    thrust_estimate_N: float         # ESTIMATED (thrust_ideal * mass_utilization_efficiency)
    isp_estimate_s: float            # ESTIMATED (thrust_estimate / (mdot * g0))

    plasma_state: PlasmaState

    assumptions: list[str] = field(default_factory=list)
    model_status: dict[str, str] = field(default_factory=dict)

    def is_finite(self) -> bool:
        """Sanity check used by tests and by the dashboard before display."""
        import math
        values = [
            self.discharge_power_W,
            self.ion_velocity_m_s,
            self.ion_energy_eV,
            self.ion_flux_particles_s,
            self.thrust_ideal_N,
            self.thrust_estimate_N,
            self.isp_estimate_s,
        ]
        return all(math.isfinite(v) for v in values)

    def to_dict(self) -> dict:
        return {
            "propellant": self.propellant,
            "discharge_voltage_V": self.discharge_voltage_V,
            "discharge_current_A": self.discharge_current_A,
            "discharge_power_W": self.discharge_power_W,
            "mass_flow_rate_kg_s": self.mass_flow_rate_kg_s,
            "magnetic_field_T": self.magnetic_field_T,
            "ion_velocity_m_s": self.ion_velocity_m_s,
            "ion_energy_eV": self.ion_energy_eV,
            "ion_flux_particles_s": self.ion_flux_particles_s,
            "thrust_ideal_N": self.thrust_ideal_N,
            "thrust_estimate_N": self.thrust_estimate_N,
            "isp_estimate_s": self.isp_estimate_s,
            "assumptions": self.assumptions,
            "model_status": self.model_status,
        }
