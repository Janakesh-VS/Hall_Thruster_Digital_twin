import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.geometry.geometry import ThrusterGeometry
from src.geometry.liner_geometry import LinerState
from src.geometry.visualization import ThrusterVisualization3D
from src.physics.hall_thruster import HallThrusterModel, OperatingConditions

GEOM_PATH = Path(__file__).resolve().parents[1] / "config" / "geometry.yaml"
OPS_PATH = Path(__file__).resolve().parents[1] / "config" / "operating_conditions.yaml"


def test_figure_builds_without_physics_result():
    geom = ThrusterGeometry(GEOM_PATH)
    viz = ThrusterVisualization3D(geometry=geom)
    fig = viz.build()
    assert len(fig.data) > 0


def test_figure_builds_with_physics_result():
    geom = ThrusterGeometry(GEOM_PATH)
    model = HallThrusterModel()
    result = model.evaluate(OperatingConditions.from_yaml(OPS_PATH))
    viz = ThrusterVisualization3D(geometry=geom, physics_result=result)
    fig = viz.build()
    # physics overlay annotation should mention the discharge voltage
    text = fig.layout.annotations[0].text
    assert f"{result.discharge_voltage_V:.0f} V" in text


def test_liner_angle_changes_the_reference_mark_trace_name():
    geom = ThrusterGeometry(GEOM_PATH)

    viz_a = ThrusterVisualization3D(geometry=geom, liner_state=LinerState(theta_deg=0.0))
    fig_a = viz_a.build()
    names_a = [t.name for t in fig_a.data if t.name and "reference mark" in t.name]

    viz_b = ThrusterVisualization3D(geometry=geom, liner_state=LinerState(theta_deg=90.0))
    fig_b = viz_b.build()
    names_b = [t.name for t in fig_b.data if t.name and "reference mark" in t.name]

    assert names_a != names_b  # theta is embedded in the trace name/state


def test_geometry_change_propagates_to_visualization():
    geom = ThrusterGeometry(GEOM_PATH)
    original_length = geom.params["channel_length"].value
    geom.override("channel_length", original_length + 5.0)

    viz = ThrusterVisualization3D(geometry=geom)
    fig = viz.build()

    # the exit-plane ring trace's x-coordinates should reflect the new
    # exit_plane_position default is independent, so instead check the
    # channel wall surface's axial extent directly from geometry
    wall_traces = [t for t in fig.data if t.name == "Inner dielectric wall"]
    assert wall_traces, "expected an inner dielectric wall trace"
    max_x = max(max(row) for row in wall_traces[0].x)
    assert max_x == original_length + 5.0
