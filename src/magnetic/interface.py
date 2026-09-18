"""
Minimal interface between Phase 4 (physics) and the future Phase 5
magnetic-field model.

For now this is a plain data holder for a scalar/vector magnetic field
value supplied as a MODEL INPUT (see config/operating_conditions.yaml).
Phase 5 will replace `MagneticFieldSpec.from_scalar_input` with a real
reduced-order or FEMM-derived field model; nothing downstream should need
to change its interface to consume that upgrade, since both expose the
same MagneticFieldSpec fields.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MagneticFieldSpec:
    magnitude_T: float
    axial_T: float
    radial_T: float
    status: str = "MODEL INPUT (placeholder — Phase 5 will compute this from coil geometry/current)"

    @classmethod
    def from_scalar_input(cls, magnitude_T: float, axial_fraction: float) -> "MagneticFieldSpec":
        axial_fraction = min(max(axial_fraction, 0.0), 1.0)
        axial = magnitude_T * axial_fraction
        radial = math.sqrt(max(magnitude_T**2 - axial**2, 0.0))
        return cls(magnitude_T=magnitude_T, axial_T=axial, radial_T=radial)
