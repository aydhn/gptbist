from bist_signal_bot.monte_carlo.randomness import MonteCarloRandomState

def test_monte_carlo_randomness_deterministic():
    rs = MonteCarloRandomState()
    u1 = rs.uniform(0.0, 1.0, 5, 42)
    u2 = rs.uniform(0.0, 1.0, 5, 42)
    assert u1 == u2
    n1 = rs.normal(0.0, 1.0, 5, 42)
    n2 = rs.normal(0.0, 1.0, 5, 42)
    assert n1 == n2
    i1 = rs.sample_indices(100, 10, 42)
    i2 = rs.sample_indices(100, 10, 42)
    assert i1 == i2

def test_monte_carlo_shuffle():
    rs = MonteCarloRandomState()
    seq = [1, 2, 3, 4, 5]
    s1 = rs.shuffle_sequence(seq, 42)
    s2 = rs.shuffle_sequence(seq, 42)
    assert s1 == s2
    assert sorted(s1) == seq
    assert len(s1) == 5
