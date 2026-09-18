import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.physics.units import (
    eV_to_joules,
    gauss_to_tesla,
    joules_to_eV,
    kg_per_s_to_mg_per_s,
    mg_per_s_to_kg_per_s,
    specific_impulse_s,
    tesla_to_gauss,
    watts_from_volts_amps,
)


def test_mg_to_kg_exact():
    assert mg_per_s_to_kg_per_s(5.0) == pytest.approx(5.0e-6)


def test_kg_to_mg_round_trip():
    original = 5.0
    assert kg_per_s_to_mg_per_s(mg_per_s_to_kg_per_s(original)) == pytest.approx(original)


def test_gauss_tesla_exact():
    assert gauss_to_tesla(1e4) == pytest.approx(1.0)


def test_tesla_gauss_round_trip():
    original = 0.015
    assert gauss_to_tesla(tesla_to_gauss(original)) == pytest.approx(original)


def test_eV_joules_round_trip():
    original = 300.0
    assert joules_to_eV(eV_to_joules(original)) == pytest.approx(original, rel=1e-9)


def test_watts_from_volts_amps():
    assert watts_from_volts_amps(300.0, 4.5) == pytest.approx(1350.0)


def test_specific_impulse_positive_for_positive_velocity():
    assert specific_impulse_s(20000.0) > 0
