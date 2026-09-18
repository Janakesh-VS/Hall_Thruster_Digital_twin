"""
Reduced-order Hall-thruster physics model.

SCOPE (per project master prompt): a transparent, dimensionally-consistent,
0-D (single operating point) reduced-order model — NOT a kinetic/PIC plasma
simulation. Every equation below is cited; nothing is an uncited or
invented relationship.

=============================================================================
EQUATION 1 — ION EXHAUST VELOCITY
=============================================================================
Equation:
    v_i = sqrt( 2 * e * (V_d - Delta) / m_i )

Purpose:
    Mean ion exhaust velocity resulting from acceleration through the
    discharge potential.

Variables:
    v_i    = mean ion exhaust velocity                [m/s]
    e      = elementary charge                        [C]
    V_d    = discharge voltage                         [V]
    Delta  = voltage losses (potential not converted
             into directed ion kinetic energy)          [V]
    m_i    = ion mass (propellant atomic mass / charge state) [kg]

Assumptions:
    - Ions are singly charged (charge state from propellant table).
    - All ions are created at the same location and fall through the same
      potential drop (no spatial spread in acceleration potential).
    - Voltage losses Delta are neglected by default (Delta = 0), following
      the cited source's baseline case; can be set nonzero if better data
      is available.

Source:
    Boeuf, J.-P. & Garrigues, L., "Sizing of Hall Effect Thrusters with
    Input Power and Thrust Level: An Empirical Approach", arXiv:0810.3994,
    Eq. (2.17): v_i_bar = sqrt(2e/m_i * (U_d - Delta)).

Validity / limitations:
    - Ignores electron temperature, multiply-charged ions, and beam
      divergence (all present in real Hall thrusters).
    - Valid as an order-of-magnitude / scaling estimate, not a
      high-fidelity prediction.

=============================================================================
EQUATION 2 — ION KINETIC ENERGY
=============================================================================
Equation:
    E_i [eV] = (V_d - Delta)     (for a singly-charged ion; energy in eV
                                   numerically equals the accelerating
                                   potential in volts)
    E_i [J]  = e * (V_d - Delta)

Purpose:
    Mean ion kinetic energy after acceleration.

Source:
    Direct consequence of Equation 1's assumption (ions fall through the
    full discharge potential); consistent with the same Boeuf & Garrigues
    scaling framework.

=============================================================================
EQUATION 3 — DISCHARGE POWER
=============================================================================
Equation:
    P_d = V_d * I_d

Source:
    Standard definition; also used explicitly in Hall-thruster power
    balance literature, e.g. P_dis = V_D * I_D (Helicon Hall Thruster
    patent literature, Eq. 4, consistent with standard electric-propulsion
    textbook treatment).

=============================================================================
EQUATION 4 — ION FLUX (particle rate)
=============================================================================
Equation:
    N_dot_ion = (eta_m * m_dot) / m_i

Purpose:
    Estimated number of ions exhausted per second, from the mass flow
    assumed to be ionized (mass utilization efficiency eta_m).

Variables:
    eta_m  = mass utilization efficiency (ASSUMED, see
             config/operating_conditions.yaml)                [fraction]
    m_dot  = propellant mass flow rate                        [kg/s]
    m_i    = ion mass                                          [kg]

Status: ESTIMATED (depends on an ASSUMED efficiency factor, not measured).

=============================================================================
EQUATION 5 — THRUST
=============================================================================
Equation (IDEAL, all propellant mass flow converted to beam ions with no
losses):
    T_ideal = m_dot * v_i

Equation (ESTIMATED, with mass utilization efficiency):
    T_estimate = eta_m * m_dot * v_i

Source:
    Standard rocket-equation-consistent thrust relation for electric
    propulsion (thrust = mass flow rate x exhaust velocity), applied here
    with the v_i from Equation 1. Consistent with the general treatment in
    Boeuf & Garrigues (2009) and Dannenmayer & Mazouffre, "Elementary
    Scaling Relations for Hall Effect Thrusters" (2011).

Status: T_ideal = IDEAL (upper bound, no losses). T_estimate = ESTIMATED.
Neither is an experimentally measured thrust.

=============================================================================
EQUATION 6 — SPECIFIC IMPULSE
=============================================================================
Equation:
    Isp = T_estimate / (m_dot * g0)      [equivalently, for this reduced
                                           model, Isp = eta_m * v_i / g0]

Source:
    Standard definition; g0 = 9.80665 m/s^2 (ISO 80000-3).

Status: ESTIMATED / MODELLED — not an experimentally measured Isp.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.physics.plasma_state import HallThrusterResult, PlasmaState
from src.physics.propellants import PropellantTable
from src.physics.units import (
    ELEMENTARY_CHARGE_C,
    STANDARD_GRAVITY_M_S2,
    mg_per_s_to_kg_per_s,
    watts_from_volts_amps,
)


class PhysicsValidationError(ValueError):
    """Raised when requested operating conditions are not physically valid."""


@dataclass
class OperatingConditions:
    propellant: str
    discharge_voltage_V: float
    discharge_current_A: float
    mass_flow_rate_mg_s: float
    magnetic_field_T: float
    magnetic_field_axial_fraction: float = 0.1
    voltage_loss_V: float = 0.0
    mass_utilization_efficiency: float = 0.7

    @classmethod
    def from_yaml(cls, config_path: str | Path | None = None) -> "OperatingConditions":
        if config_path is None:
            config_path = (
                Path(__file__).resolve().parents[2] / "config" / "operating_conditions.yaml"
            )
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)["reference_operating_point"]
        return cls(
            propellant=raw["propellant"]["value"],
            discharge_voltage_V=raw["discharge_voltage"]["value"],
            discharge_current_A=raw["discharge_current"]["value"],
            mass_flow_rate_mg_s=raw["mass_flow_rate"]["value"],
            magnetic_field_T=raw["magnetic_field_magnitude"]["value"],
            magnetic_field_axial_fraction=raw["magnetic_field_axial_fraction"]["value"],
            voltage_loss_V=raw["voltage_loss"]["value"],
            mass_utilization_efficiency=raw["mass_utilization_efficiency"]["value"],
        )

    def validate(self) -> None:
        errors: list[str] = []
        if self.discharge_voltage_V <= 0:
            errors.append("discharge_voltage_V must be > 0.")
        if self.discharge_voltage_V - self.voltage_loss_V <= 0:
            errors.append("discharge_voltage_V must exceed voltage_loss_V (net accelerating potential must be > 0).")
        if self.discharge_current_A < 0:
            errors.append("discharge_current_A must be >= 0.")
        if self.mass_flow_rate_mg_s <= 0:
            errors.append("mass_flow_rate_mg_s must be > 0.")
        if self.magnetic_field_T < 0:
            errors.append("magnetic_field_T must be >= 0.")
        if not (0.0 <= self.magnetic_field_axial_fraction <= 1.0):
            errors.append("magnetic_field_axial_fraction must be in [0, 1].")
        if not (0.0 < self.mass_utilization_efficiency <= 1.0):
            errors.append("mass_utilization_efficiency must be in (0, 1].")
        if errors:
            raise PhysicsValidationError(
                "Invalid operating conditions:\n- " + "\n- ".join(errors)
            )


class HallThrusterModel:
    """
    Reduced-order Hall-thruster physics model. See module docstring for the
    cited equations. Stateless per call: `evaluate()` takes an
    OperatingConditions and returns a HallThrusterResult; it does not read
    or write any external state.
    """

    def __init__(self, propellant_table: PropellantTable | None = None):
        self.propellants = propellant_table or PropellantTable()

    def evaluate(self, conditions: OperatingConditions) -> HallThrusterResult:
        conditions.validate()

        propellant = self.propellants.get(conditions.propellant)
        m_i = propellant.atomic_mass_kg / max(propellant.charge_state, 1)
        # (dividing by charge state is a no-op for charge_state=1; kept
        #  explicit so a future multiply-charged extension is a one-line
        #  change, not a silent bug)

        Vd = conditions.discharge_voltage_V
        Id = conditions.discharge_current_A
        Delta = conditions.voltage_loss_V
        mdot_kg_s = mg_per_s_to_kg_per_s(conditions.mass_flow_rate_mg_s)
        eta_m = conditions.mass_utilization_efficiency
        B = conditions.magnetic_field_T
        B_axial = B * conditions.magnetic_field_axial_fraction
        B_radial = math.sqrt(max(B**2 - B_axial**2, 0.0))

        net_potential = Vd - Delta  # > 0 guaranteed by validate()

        # Equation 1: ion exhaust velocity (Boeuf & Garrigues, arXiv:0810.3994, Eq. 2.17)
        v_i = math.sqrt(2.0 * ELEMENTARY_CHARGE_C * net_potential / m_i)

        # Equation 2: ion kinetic energy (eV numerically == net accelerating potential in V)
        ion_energy_eV = net_potential

        # Equation 3: discharge power
        P_d = watts_from_volts_amps(Vd, Id)

        # Equation 4: ion flux (particles/s), ESTIMATED via mass utilization efficiency
        n_dot_ion = (eta_m * mdot_kg_s) / m_i

        # Equation 5: thrust
        thrust_ideal = mdot_kg_s * v_i                 # IDEAL — full mass flow, no losses
        thrust_estimate = eta_m * mdot_kg_s * v_i       # ESTIMATED — with mass utilization

        # Equation 6: specific impulse
        isp_estimate = thrust_estimate / (mdot_kg_s * STANDARD_GRAVITY_M_S2)

        plasma_state = PlasmaState(
            ion_velocity_m_s=v_i,
            ion_energy_eV=ion_energy_eV,
            ion_flux_particles_s=n_dot_ion,
            magnetic_field_T=B,
            magnetic_field_axial_T=B_axial,
            magnetic_field_radial_T=B_radial,
            discharge_voltage_V=Vd,
            discharge_current_A=Id,
            mass_flow_rate_kg_s=mdot_kg_s,
        )

        result = HallThrusterResult(
            propellant=conditions.propellant,
            discharge_voltage_V=Vd,
            discharge_current_A=Id,
            discharge_power_W=P_d,
            mass_flow_rate_kg_s=mdot_kg_s,
            magnetic_field_T=B,
            ion_velocity_m_s=v_i,
            ion_energy_eV=ion_energy_eV,
            ion_flux_particles_s=n_dot_ion,
            thrust_ideal_N=thrust_ideal,
            thrust_estimate_N=thrust_estimate,
            isp_estimate_s=isp_estimate,
            plasma_state=plasma_state,
            assumptions=[
                "Ions assumed singly-charged (no multiply-charged ion correction).",
                "Ions assumed created at a single location, falling through the full net potential (Vd - Delta).",
                f"Voltage loss Delta = {Delta} V (ASSUMED/LITERATURE — see config/operating_conditions.yaml).",
                f"Mass utilization efficiency eta_m = {eta_m} (ASSUMED — see config/operating_conditions.yaml).",
                "Magnetic field is a MODEL INPUT here, not computed (Phase 5 will add a real field model).",
                "0-D model: no spatial resolution of the discharge channel.",
            ],
            model_status={
                "ion_velocity_m_s": "MODELLED (Boeuf & Garrigues, arXiv:0810.3994, Eq. 2.17)",
                "ion_energy_eV": "MODELLED",
                "discharge_power_W": "MODELLED (P = V*I)",
                "ion_flux_particles_s": "ESTIMATED (depends on assumed mass_utilization_efficiency)",
                "thrust_ideal_N": "IDEAL (upper bound, no losses)",
                "thrust_estimate_N": "ESTIMATED",
                "isp_estimate_s": "ESTIMATED",
                "magnetic_field_T": "MODEL INPUT (not computed by this phase)",
            },
        )
        return result


if __name__ == "__main__":
    model = HallThrusterModel()
    conditions = OperatingConditions.from_yaml()
    result = model.evaluate(conditions)
    print(f"Propellant: {result.propellant}")
    print(f"Discharge power: {result.discharge_power_W:.1f} W")
    print(f"Ion velocity: {result.ion_velocity_m_s:.1f} m/s")
    print(f"Ion energy: {result.ion_energy_eV:.1f} eV")
    print(f"Thrust (ideal): {result.thrust_ideal_N * 1000:.2f} mN")
    print(f"Thrust (estimate): {result.thrust_estimate_N * 1000:.2f} mN")
    print(f"Isp (estimate): {result.isp_estimate_s:.1f} s")
    print(f"Finite check: {result.is_finite()}")
