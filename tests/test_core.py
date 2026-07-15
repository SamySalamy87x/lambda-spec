import numpy as np
import pytest
from lambda_spec import coupling, phi, dlambda_dt, synthetic


def test_isolated_is_fragile():
    """Control negativo: sin acoplamiento -> Phi alto."""
    x, env = synthetic.isolated_system(n=500)
    r = coupling(x, env)
    assert r.phi > 0.8
    assert r.fragile


def test_coupled_is_robust():
    """Acoplamiento fuerte -> Phi bajo."""
    x, env = synthetic.bistable_switch(n=500)
    r = coupling(x, env)
    assert r.phi < 0.3
    assert not r.fragile


def test_phi_bounds():
    for gen in [
        synthetic.bistable_switch,
        synthetic.neural_coupling,
        synthetic.telemetry_subsystems,
        synthetic.isolated_system,
    ]:
        x, env = gen()
        p = phi(x, env)
        assert 0.0 <= p <= 1.0


def test_lambda_phi_complementary():
    x, env = synthetic.telemetry_subsystems()
    r = coupling(x, env)
    assert abs(r.lam + r.phi - 1.0) < 1e-9


def test_methods_agree_on_direction():
    x, env = synthetic.bistable_switch(n=400)
    for m in ["spearman", "pearson", "residual"]:
        assert coupling(x, env, method=m).phi < 0.5


def test_dlambda_dt_sign():
    assert dlambda_dt(np.array([0.1, 0.3, 0.5])) > 0
    assert dlambda_dt(np.array([0.5, 0.3, 0.1])) < 0


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        coupling(np.zeros(10), np.zeros(5))


def test_min_samples():
    with pytest.raises(ValueError):
        coupling(np.zeros(2), np.zeros(2))
