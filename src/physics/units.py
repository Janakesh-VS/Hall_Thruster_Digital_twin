"""
Explicit unit-conversion helpers for the physics layer.

Every conversion used anywhere in src/physics must go through one of these
functions rather than an inline literal, so a wrong conversion factor is a
one-place bug, not scattered across the codebase, and so it can be unit
tested directly (see tests/test_units.py).
"""

from __future__ import annotations

ELEMENTARY_CHARGE_C = 1.602176634e-19  # exact, CODATA 2018 (SI redefinition)
STANDARD_GRAVITY_M_S2 = 9.80665         # exact, defined standard (ISO 80000-3)
AMU_KG = 1.66053906660e-27              # CODATA 2018


def mg_per_s_to_kg_per_s(value_mg_s: float) -> float:
    """Exact mg/s -> kg/s conversion."""
    return value_mg_s * 1e-6


def kg_per_s_to_mg_per_s(value_kg_s: float) -> float:
    return value_kg_s * 1e6


def gauss_to_tesla(value_gauss: float) -> float:
    """Exact G -> T conversion (1 T = 1e4 G by definition)."""
    return value_gauss * 1e-4


def tesla_to_gauss(value_tesla: float) -> float:
    return value_tesla * 1e4


def eV_to_joules(value_eV: float) -> float:
    """Exact eV -> J conversion using the exact elementary charge."""
    return value_eV * ELEMENTARY_CHARGE_C


def joules_to_eV(value_j: float) -> float:
    return value_j / ELEMENTARY_CHARGE_C


def amu_to_kg(value_u: float) -> float:
    return value_u * AMU_KG


def watts_from_volts_amps(voltage_v: float, current_a: float) -> float:
    """P = V * I. Kept as a named function so unit-consistency is explicit at call sites."""
    return voltage_v * current_a


def specific_impulse_s(exhaust_velocity_m_s: float) -> float:
    """Isp = v_exhaust / g0."""
    return exhaust_velocity_m_s / STANDARD_GRAVITY_M_S2
