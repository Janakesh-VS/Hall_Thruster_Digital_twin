"""
3D digital-twin visualization.

Everything drawn here is generated from `ThrusterGeometry` (which in turn
reads config/geometry.yaml) plus, optionally, a `HallThrusterResult` and a
`LinerState`. No dimension is hard-coded in this module: change
geometry.yaml and the 3D model changes with it.

Coordinate convention (per master prompt):
    X = axial direction
    theta = circumferential angle
    a point at radius r, angle theta, axial position x is placed at
        (x, r*cos(theta), r*sin(theta))
    i.e. Y and Z together span the radial/circumferential plane.

This is a geometry + physics-state renderer, not a plasma physics solver:
the "plasma region" surface is explicitly labeled as a modelled region
whose color intensity reflects `ion_energy_eV` from the physics model, not
an independent visual effect.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from src.geometry.geometry import ThrusterGeometry
from src.geometry.liner_geometry import LinerState
from src.physics.plasma_state import HallThrusterResult

N_THETA_DEFAULT = 72


def _cylinder_surface(
    radius_mm: float,
    z0_mm: float,
    z1_mm: float,
    theta0_deg: float = 0.0,
    theta1_deg: float = 360.0,
    n_theta: int = N_THETA_DEFAULT,
    n_z: int = 2,
):
    """Returns (x, y, z) meshgrids for a cylindrical surface segment."""
    theta = np.radians(np.linspace(theta0_deg, theta1_deg, n_theta))
    z = np.linspace(z0_mm, z1_mm, n_z)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x = z_grid
    y = radius_mm * np.cos(theta_grid)
    z_out = radius_mm * np.sin(theta_grid)
    return x, y, z_out


def _ring_outline(radius_mm: float, z_mm: float, n_theta: int = N_THETA_DEFAULT):
    theta = np.radians(np.linspace(0, 360, n_theta))
    x = np.full_like(theta, z_mm)
    y = radius_mm * np.cos(theta)
    z = radius_mm * np.sin(theta)
    return x, y, z


class ThrusterVisualization3D:
    """Builds a Plotly Figure representing the current geometry + state."""

    def __init__(
        self,
        geometry: ThrusterGeometry | None = None,
        liner_state: LinerState | None = None,
        physics_result: HallThrusterResult | None = None,
    ):
        self.geometry = geometry or ThrusterGeometry()
        self.liner_state = liner_state or LinerState()
        self.physics_result = physics_result

    # -- component builders --------------------------------------------------
    def _add_channel_walls(self, fig: go.Figure) -> None:
        g = self.geometry.params
        z0, z1 = 0.0, g["channel_length"].value

        x, y, z = _cylinder_surface(g["channel_inner_radius"].value, z0, z1)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.35,
            colorscale=[[0, "#cfd8dc"], [1, "#cfd8dc"]],
            name="Inner dielectric wall", hoverinfo="name",
        ))

        x, y, z = _cylinder_surface(g["channel_outer_radius"].value, z0, z1)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.35,
            colorscale=[[0, "#cfd8dc"], [1, "#cfd8dc"]],
            name="Outer dielectric wall", hoverinfo="name",
        ))

    def _add_poles(self, fig: go.Figure) -> None:
        g = self.geometry.params
        z0, z1 = -5.0, g["channel_length"].value

        x, y, z = _cylinder_surface(g["inner_pole_radius"].value, z0, z1)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.55,
            colorscale=[[0, "#455a64"], [1, "#455a64"]],
            name="Inner magnetic pole", hoverinfo="name",
        ))

        x, y, z = _cylinder_surface(g["outer_pole_radius"].value, z0, z1)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.25,
            colorscale=[[0, "#455a64"], [1, "#455a64"]],
            name="Outer magnetic pole", hoverinfo="name",
        ))

    def _add_coils(self, fig: go.Figure) -> None:
        g = self.geometry.params
        z0, z1 = 0.0, g["channel_length"].value
        for r in (g["coil_inner_radius"].value, g["coil_outer_radius"].value):
            x, y, z = _cylinder_surface(r, z0, z1)
            fig.add_trace(go.Surface(
                x=x, y=y, z=z, showscale=False, opacity=0.4,
                colorscale=[[0, "#d4822a"], [1, "#d4822a"]],
                name="Electromagnetic coil region", hoverinfo="name",
            ))

    def _add_liner(self, fig: go.Figure) -> None:
        """
        The liner is drawn as a translucent full cylinder PLUS an opaque
        angular stripe that marks the liner's current theta so rotation is
        visible when set_liner_angle() changes. This is real state, not a
        camera trick: the stripe's theta comes directly from self.liner_state.
        """
        g = self.geometry.params
        r = g["liner_radius"].value
        half_len = g["liner_axial_length"].value / 2.0
        mid = g["channel_length"].value / 2.0
        z0, z1 = mid - half_len, mid + half_len

        x, y, z = _cylinder_surface(r, z0, z1)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.2,
            colorscale=[[0, "#8e24aa"], [1, "#8e24aa"]],
            name="Rotating dielectric liner", hoverinfo="name",
        ))

        theta0 = self.liner_state.theta_deg
        x, y, z = _cylinder_surface(r * 1.01, z0, z1, theta0_deg=theta0, theta1_deg=theta0 + 12.0, n_theta=8)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.95,
            colorscale=[[0, "#e91e63"], [1, "#e91e63"]],
            name=f"Liner reference mark (theta={theta0:.1f} deg)", hoverinfo="name",
        ))

    def _add_plasma_region(self, fig: go.Figure) -> None:
        g = self.geometry.params
        z0, z1 = 0.0, g["channel_length"].value
        r_mid = (g["channel_inner_radius"].value + g["channel_outer_radius"].value) / 2.0

        # Color intensity reflects ion_energy_eV from the physics model when
        # available; otherwise the region is shown neutrally with no implied
        # physics state.
        if self.physics_result is not None:
            energy_eV = self.physics_result.ion_energy_eV
            label = f"MODELLED PLASMA REGION (reduced-order) — ion energy ~{energy_eV:.0f} eV"
            colorscale = [[0, "#1a1a40"], [1, "#7b5fd1"]]
            intensity_val = min(energy_eV / 600.0, 1.0)  # normalized against a ~600 eV reference scale
        else:
            label = "MODELLED PLASMA REGION (reduced-order) — no physics result loaded"
            colorscale = [[0, "#333355"], [1, "#333355"]]
            intensity_val = 0.5

        x, y, z = _cylinder_surface(r_mid, z0, z1)
        intensity = np.full_like(x, intensity_val)
        fig.add_trace(go.Surface(
            x=x, y=y, z=z, showscale=False, opacity=0.3,
            surfacecolor=intensity, colorscale=colorscale, cmin=0, cmax=1,
            name=label, hoverinfo="name",
        ))

    def _add_exit_plane(self, fig: go.Figure) -> None:
        g = self.geometry.params
        z = g["exit_plane_position"].value
        x, y, zz = _ring_outline(g["channel_outer_radius"].value, z)
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=zz, mode="lines",
            line=dict(color="#ff5252", width=5),
            name="Exit plane", hoverinfo="name",
        ))

    def _add_sensors(self, fig: go.Figure) -> None:
        xs, ys, zs, labels = [], [], [], []
        for sensor_name, fields in self.geometry.sensors.items():
            if "axial_position" not in fields or "radial_position" not in fields:
                # e.g. optical_encoder only specifies an axial position (it
                # sits on the rotation shaft, not at a specific radius) —
                # skip rather than inventing a radial coordinate for it.
                continue
            axial = fields["axial_position"].value
            radial = fields["radial_position"].value
            theta = np.radians(fields["theta_position"].value if "theta_position" in fields else 0.0)
            xs.append(axial)
            ys.append(radial * np.cos(theta))
            zs.append(radial * np.sin(theta))
            labels.append(sensor_name.replace("_", " "))
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="markers+text",
            marker=dict(size=5, color="#00e676", symbol="diamond"),
            text=labels, textposition="top center",
            name="Sensor locations", hoverinfo="text",
        ))

    def _add_axes(self, fig: go.Figure) -> None:
        g = self.geometry.params
        L = g["channel_length"].value * 1.5
        # X (axial)
        fig.add_trace(go.Scatter3d(
            x=[0, L], y=[0, 0], z=[0, 0], mode="lines+text",
            line=dict(color="red", width=4), text=["", "X (axial)"],
            textposition="top center", name="X axis", showlegend=False, hoverinfo="skip",
        ))
        # Y (radial)
        R = g["coil_outer_radius"].value * 1.2
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, R], z=[0, 0], mode="lines+text",
            line=dict(color="green", width=4), text=["", "Y (radial)"],
            textposition="top center", name="Y axis", showlegend=False, hoverinfo="skip",
        ))
        # Z (radial/circumferential plane)
        fig.add_trace(go.Scatter3d(
            x=[0, 0], y=[0, 0], z=[0, R], mode="lines+text",
            line=dict(color="blue", width=4), text=["", "Z (radial)"],
            textposition="top center", name="Z axis", showlegend=False, hoverinfo="skip",
        ))

    # -- assembly -------------------------------------------------------------
    def build(self, show_axes: bool = True) -> go.Figure:
        fig = go.Figure()
        self._add_poles(fig)
        self._add_channel_walls(fig)
        self._add_coils(fig)
        self._add_liner(fig)
        self._add_plasma_region(fig)
        self._add_exit_plane(fig)
        self._add_sensors(fig)
        if show_axes:
            self._add_axes(fig)

        status_lines = [
            "REFERENCE / ASSUMED GEOMETRY — NOT FLIGHT-HARDWARE DIMENSIONS",
            f"Liner angle (theta): {self.liner_state.theta_deg:.1f} deg",
        ]
        if self.physics_result is not None:
            r = self.physics_result
            status_lines += [
                f"Vd = {r.discharge_voltage_V:.0f} V   Id = {r.discharge_current_A:.2f} A   "
                f"P = {r.discharge_power_W:.0f} W   B = {r.magnetic_field_T*1000:.1f} mT",
                f"Ion velocity (modelled) = {r.ion_velocity_m_s:,.0f} m/s   "
                f"Ion energy (modelled) = {r.ion_energy_eV:.0f} eV",
                f"Thrust (estimate) = {r.thrust_estimate_N*1000:.2f} mN   "
                f"Isp (estimate) = {r.isp_estimate_s:.0f} s",
            ]
        else:
            status_lines.append("Physics model status: NOT LOADED")

        fig.update_layout(
            title="PROMETHEUS — Digital Twin (Phase 3+4): Reference Geometry + Reduced-Order Physics",
            scene=dict(
                xaxis_title="X — axial (mm)",
                yaxis_title="Y — radial (mm)",
                zaxis_title="Z — radial (mm)",
                aspectmode="data",
            ),
            margin=dict(l=0, r=0, t=60, b=140),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        )
        # Model-status / physics-overlay text as a 2D annotation under the plot
        fig.add_annotation(
            text="<br>".join(status_lines),
            xref="paper", yref="paper", x=0.0, y=-0.25,
            showarrow=False, align="left",
            font=dict(size=12, family="monospace"),
        )
        return fig


def save_html(fig: go.Figure, path: str | Path) -> Path:
    """Save as a fully self-contained (offline-viewable) HTML file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(path), include_plotlyjs="inline", full_html=True)
    return path


if __name__ == "__main__":
    from src.physics.hall_thruster import HallThrusterModel, OperatingConditions

    geometry = ThrusterGeometry()
    liner = LinerState(theta_deg=45.0)
    model = HallThrusterModel()
    result = model.evaluate(OperatingConditions.from_yaml())

    viz = ThrusterVisualization3D(geometry, liner, result)
    fig = viz.build()
    out = save_html(fig, Path(__file__).resolve().parents[2] / "results" / "digital_twin_3d.html")
    print(f"Wrote {out}")
