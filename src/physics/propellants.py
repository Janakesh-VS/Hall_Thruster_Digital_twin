"""
Propellant property loader.

Reads config/physics.yaml so propellant properties (atomic mass, ionization
energy, assumed charge state) are never hard-coded inside the physics
calculations themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from src.physics.units import amu_to_kg


@dataclass(frozen=True)
class Propellant:
    name: str
    symbol: str
    atomic_mass_kg: float
    atomic_mass_u: float
    first_ionization_energy_eV: float
    charge_state: int
    atomic_mass_status: str  # SOURCE / LITERATURE / ASSUMED / USER-DEFINED


class PropellantTable:
    """Loads all propellant species defined in config/physics.yaml."""

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[2] / "config" / "physics.yaml"
        self.config_path = Path(config_path)
        with open(self.config_path, "r") as f:
            raw = yaml.safe_load(f)

        self.constants = raw["constants"]
        self._propellants: dict[str, Propellant] = {}
        for name, entry in raw["propellants"].items():
            atomic_mass_u = entry["atomic_mass_u"]["value"]
            self._propellants[name] = Propellant(
                name=name,
                symbol=entry["symbol"],
                atomic_mass_kg=amu_to_kg(atomic_mass_u),
                atomic_mass_u=atomic_mass_u,
                first_ionization_energy_eV=entry["first_ionization_energy_eV"]["value"],
                charge_state=int(entry["default_charge_state"]["value"]),
                atomic_mass_status=entry["atomic_mass_u"]["status"],
            )

    def get(self, name: str) -> Propellant:
        key = name.strip().lower()
        if key not in self._propellants:
            available = ", ".join(sorted(self._propellants))
            raise KeyError(f"Unknown propellant '{name}'. Available: {available}")
        return self._propellants[key]

    def available(self) -> list[str]:
        return sorted(self._propellants)
