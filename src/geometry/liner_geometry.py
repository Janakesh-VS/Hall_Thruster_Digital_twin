"""
Rotating dielectric liner — kinematic state and control interface.

Phase 3 scope: expose a clean `set_liner_angle(theta_deg)` interface that
the 3D visualization reads from, so the liner in the viewer is driven by
real state rather than a decorative animation. The full time-integrated
kinematics (theta(t) = theta_0 + integral(omega dt), acceleration limits
enforced over time) is Phase 6 — this module defines the state object and
the instantaneous-limit checks that Phase 6 will call on every timestep.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.geometry.geometry import ThrusterGeometry


class LinerKinematicsError(ValueError):
    """Raised when a requested liner state violates a configured motion limit."""


@dataclass
class LinerState:
    theta_deg: float = 0.0
    angular_velocity_rpm: float = 0.0

    def theta_rad(self) -> float:
        import math
        return math.radians(self.theta_deg)


class LinerController:
    """
    Holds the liner's current angular state and enforces the max
    speed / acceleration limits defined in config/geometry.yaml. This is
    the single place the 3D visualization and the future controller
    (Phase 9) both read liner position from.
    """

    def __init__(self, geometry: ThrusterGeometry | None = None):
        self.geometry = geometry or ThrusterGeometry()
        self.max_speed_rpm = self.geometry.params["liner_max_angular_speed"].value
        self.state = LinerState()

    def set_liner_angle(self, theta_deg: float) -> None:
        """
        Directly set the liner's angular position (mod 360), for
        visualization / demo purposes. Phase 6 will replace direct
        position-setting with time-integrated motion subject to the
        acceleration limit; this method remains the interface both use.
        """
        self.state.theta_deg = theta_deg % 360.0

    def set_angular_velocity(self, omega_rpm: float) -> None:
        if abs(omega_rpm) > self.max_speed_rpm:
            raise LinerKinematicsError(
                f"Requested angular velocity {omega_rpm} RPM exceeds "
                f"liner_max_angular_speed ({self.max_speed_rpm} RPM)."
            )
        self.state.angular_velocity_rpm = omega_rpm

    def step(self, dt_s: float) -> None:
        """Advance theta by the current angular velocity over dt_s seconds."""
        delta_deg = self.state.angular_velocity_rpm * 6.0 * dt_s  # RPM -> deg/s is *6
        self.set_liner_angle(self.state.theta_deg + delta_deg)
