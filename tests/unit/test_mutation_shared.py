import random

from auditcurve.models.mutation import Severity
from auditcurve.mutate.shared import perturb_numeric


def test_blatant_perturbation_is_20_to_40_percent():
    rng = random.Random(0)
    for _ in range(50):
        value = perturb_numeric(100.0, Severity.BLATANT, rng)
        pct = abs(value - 100.0) / 100.0
        assert 0.20 <= pct <= 0.40


def test_subtle_perturbation_is_3_to_8_percent():
    rng = random.Random(0)
    for _ in range(50):
        value = perturb_numeric(100.0, Severity.SUBTLE, rng)
        pct = abs(value - 100.0) / 100.0
        assert 0.03 <= pct <= 0.08


def test_blatant_is_always_a_bigger_deviation_than_subtle_ceiling():
    rng = random.Random(0)
    blatant = perturb_numeric(100.0, Severity.BLATANT, rng)
    assert abs(blatant - 100.0) > 8.0
