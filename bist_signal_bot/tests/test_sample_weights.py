import numpy as np
import pytest

from bist_signal_bot.edge_validation.sample_weights import (
    average_uniqueness,
    return_attribution_weights,
    sequential_bootstrap,
    time_decay_weights,
)


def test_uniqueness_hand_example():
    # grid {0,1,2,3}; A=[0,2], B=[1,3], C=[3,3]
    # concurrency: t0=1, t1=2, t2=2, t3=2 (B and C)
    u = average_uniqueness([0, 1, 3], [2, 3, 3])
    assert u[0] == pytest.approx((1 + 0.5 + 0.5) / 3)
    assert u[1] == pytest.approx(0.5)
    assert u[2] == pytest.approx(0.5)


def test_uniqueness_bounds_and_disjoint():
    assert np.allclose(average_uniqueness([0, 10, 20], [5, 15, 25]), 1.0)
    rng = np.random.default_rng(0)
    t0 = np.sort(rng.integers(0, 100, 40))
    t1 = t0 + rng.integers(0, 15, 40)
    u = average_uniqueness(t0, t1, grid=np.arange(0, 120))
    assert ((u > 0) & (u <= 1 + 1e-12)).all()
    assert average_uniqueness([], []).size == 0
    with pytest.raises(ValueError):
        average_uniqueness([5], [1])


def test_time_decay():
    u = np.ones(10)
    w = time_decay_weights(u, 0.5)
    assert w[-1] == pytest.approx(1.0)
    assert w[0] == pytest.approx(0.5 + 0.5 / 10)  # oldest ~ last_weight
    assert np.all(np.diff(w) > 0) and w[0] > 0
    assert np.allclose(time_decay_weights(u, 1.0), 1.0)
    z = time_decay_weights(u, -0.5)
    assert (z >= 0).all() and z[0] == 0 and z[-1] == pytest.approx(1.0)
    assert time_decay_weights([], 0.5).size == 0


def test_return_attribution():
    w = return_attribution_weights([0, 1, 5], [3, 4, 8], [0.05, -0.02, 0.10])
    assert len(w) == 3 and (w >= 0).all()
    assert w.sum() == pytest.approx(3.0)
    w2 = return_attribution_weights([0, 10], [3, 13], [0.1, 0.2])
    assert w2[1] / w2[0] == pytest.approx(np.log(1.2) / np.log(1.1))
    assert return_attribution_weights([], [], []).size == 0


def test_sequential_bootstrap():
    t0 = np.array([0, 0, 0, 10, 20])
    t1 = np.array([5, 5, 5, 12, 22])
    a = sequential_bootstrap(t0, t1, 5, np.random.default_rng(1))
    b = sequential_bootstrap(t0, t1, 5, np.random.default_rng(1))
    assert (a == b).all() and len(a) == 5 and a.min() >= 0 and a.max() < 5
    draws = sequential_bootstrap(t0, t1, 2000, np.random.default_rng(2))
    counts = np.bincount(draws, minlength=5)
    assert counts[3] > counts[0] and counts[4] > counts[1]
    assert sequential_bootstrap([], [], 3).size == 0
