import math

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation import stats as S


def test_sharpe_edge_cases():
    assert math.isnan(S.sharpe([0.01, 0.02]))
    assert math.isnan(S.sharpe([0.01] * 10))
    r = np.random.default_rng(0).normal(0.001, 0.01, 500)
    assert S.sharpe(r, 252) == pytest.approx(S.sharpe(r) * math.sqrt(252))


def test_psr_known_values():
    assert S.probabilistic_sharpe_ratio(0.1, 0.1, 100) == pytest.approx(0.5)
    se = math.sqrt((1 + 0.5 * 0.01) / 100)
    assert S.probabilistic_sharpe_ratio(0.1, 0.0, 101) == pytest.approx(S.norm_cdf(0.1 / se))
    assert math.isnan(S.probabilistic_sharpe_ratio(0.1, 0.0, 2))


def test_expected_max_sharpe_values():
    assert S.expected_max_sharpe(1, 1.0) == 0.0
    assert S.expected_max_sharpe(100, 1.0) == pytest.approx(2.5, abs=0.05)
    assert S.expected_max_sharpe(10, 1.0) < S.expected_max_sharpe(1000, 1.0)


def test_dsr_decreases_with_trials():
    sr, n = 0.08, 1000
    vals = [S.deflated_sharpe_ratio(sr, k, 0.001, n_obs=n) for k in (1, 10, 100, 1000)]
    assert all(a > b for a, b in zip(vals, vals[1:]))
    assert vals[0] == pytest.approx(S.probabilistic_sharpe_ratio(sr, 0.0, n))
    r = np.random.default_rng(1).normal(0.002, 0.01, 800)
    assert S.deflated_sharpe_ratio(r, 50, 0.0005) < S.deflated_sharpe_ratio(r, 2, 0.0005)
    with pytest.raises(ValueError):
        S.deflated_sharpe_ratio(0.1, 5, 0.01)


def test_min_track_record_length():
    assert S.min_track_record_length(0.1, 0.0) == pytest.approx(1 + 1.005 * (1.6448536 / 0.1) ** 2, rel=1e-4)
    assert math.isinf(S.min_track_record_length(0.0))


def test_sharpe_pvalue():
    rng = np.random.default_rng(2)
    assert S.sharpe_pvalue(rng.normal(0.01, 0.01, 200)) < 0.001
    assert S.sharpe_pvalue(rng.normal(-0.01, 0.01, 200)) > 0.99
    assert math.isnan(S.sharpe_pvalue([1.0]))


def test_pbo_noise_and_dominant():
    rng = np.random.default_rng(3)
    noise = pd.DataFrame(rng.normal(0, 0.01, (640, 20)))
    res = S.probability_of_backtest_overfitting(noise, n_blocks=12)
    # a single noise realisation has a large PBO spread; the average over seeds is ~0.5
    pbos = [S.probability_of_backtest_overfitting(
        np.random.default_rng(100 + s).normal(0, 0.01, (640, 20)), n_blocks=12)["pbo"] for s in range(10)]
    assert abs(float(np.mean(pbos)) - 0.5) < 0.15
    assert res["n_combinations"] == 924
    dom = noise.copy()
    dom[0] = dom[0] + 0.01
    res2 = S.probability_of_backtest_overfitting(dom, n_blocks=12)
    assert res2["pbo"] < 0.05
    assert res2["prob_loss"] == 0.0
    assert math.isnan(S.probability_of_backtest_overfitting(noise.iloc[:, :1])["pbo"])
    assert math.isnan(S.probability_of_backtest_overfitting(noise.iloc[:10])["pbo"])


def test_bh_holm_bonferroni_hand_computed():
    p = [0.01, 0.04, 0.03, 0.005]
    bon, rb = S.bonferroni(p)
    assert bon == pytest.approx([0.04, 0.16, 0.12, 0.02])
    assert list(rb) == [True, False, False, True]
    h, rh = S.holm(p)
    # sorted .005,.01,.03,.04 -> *4,*3,*2,*1 = .02,.03,.06,.04 -> cummax .02,.03,.06,.06
    assert h == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert list(rh) == [True, False, False, True]
    b, rbh = S.benjamini_hochberg(p)
    # .005*4/1=.02, .01*4/2=.02, .03*4/3=.04, .04*4/4=.04
    assert b == pytest.approx([0.02, 0.04, 0.04, 0.02])
    assert list(rbh) == [True, True, True, True]


def test_bootstrap_ci_coverage_and_edges():
    assert math.isnan(S.block_bootstrap_ci([1.0, 2.0])[0])
    rng = np.random.default_rng(4)
    hits = 0
    trials = 40
    for i in range(trials):
        x = rng.normal(0.5, 1.0, 100)
        lo, hi = S.block_bootstrap_ci(x, block_len=3, n=300, seed=i)
        hits += lo <= 0.5 <= hi
    assert hits / trials >= 0.85
    x = rng.normal(0, 1, 100)
    assert S.block_bootstrap_ci(x, seed=7) == S.block_bootstrap_ci(x, seed=7)
    lo, hi = S.block_bootstrap_ci(x, block_len=4, n=200, method="circular")
    assert lo < hi


def test_effective_sample_size():
    rng = np.random.default_rng(5)
    iid = rng.normal(size=1000)
    assert S.effective_sample_size(iid) > 700
    ar = np.zeros(1000)
    e = rng.normal(size=1000)
    for t in range(1, 1000):
        ar[t] = 0.8 * ar[t - 1] + e[t]
    assert S.effective_sample_size(ar) < 300
    assert math.isnan(S.effective_sample_size([]))


def test_reality_check_planted_vs_noise():
    rng = np.random.default_rng(6)
    noise = rng.normal(0, 0.01, (500, 30))
    assert S.white_reality_check(noise, n_boot=300, seed=1) > 0.1
    planted = noise.copy()
    planted[:, 7] += 0.003
    assert S.white_reality_check(planted, n_boot=300, seed=1) < 0.05
    bench = rng.normal(0, 0.01, 500)
    assert S.white_reality_check(planted + bench[:, None], benchmark=bench, n_boot=300, seed=1) < 0.05
    assert math.isnan(S.white_reality_check(noise[:2]))
    with pytest.raises(ValueError):
        S.white_reality_check(noise, benchmark=bench[:10])
