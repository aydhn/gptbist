import math
import sqlite3

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.ledger import TrialLedger, default_ledger_path


def _ret(seed, start="2024-01-02 10:00", n=50):
    idx = pd.date_range(start, periods=n, freq="30min", tz="Europe/Istanbul")
    return pd.Series(np.random.default_rng(seed).normal(0.001, 0.01, n), index=idx)


def test_idempotent_and_counts(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    assert led.record_trial("t1", "ma", {"w": 5}, "30m", "bist30", _ret(1), strategy_family="ma")
    assert not led.record_trial("t1", "ma", {"w": 5}, "30m", "bist30", _ret(2), strategy_family="ma")
    led.record_trial("t2", "ma", {"w": 10}, "30m", "bist30", _ret(3), strategy_family="ma")
    led.record_trial("t3", "rsi", {}, "30m", "bist30", None, strategy_family="rsi", status="failed")
    assert led.n_trials() == 3 and led.n_trials("ma") == 2 and led.n_trials("rsi") == 1
    assert TrialLedger(tmp_path / "t.sqlite").n_trials() == 3


def test_variance(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    assert math.isnan(led.trial_sharpe_variance())
    rs = [_ret(i) for i in range(5)]
    for i, r in enumerate(rs):
        led.record_trial(f"t{i}", "ma", returns=r)
    srs = [r.mean() / r.std(ddof=1) for r in rs]
    assert led.trial_sharpe_variance() == pytest.approx(np.var(srs, ddof=1))


def test_returns_matrix_alignment_and_mask(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    a, b = _ret(1, n=20), _ret(2, start="2024-01-02 14:00", n=20)
    led.record_trial("a", "ma", returns=a)
    led.record_trial("b", "ma", returns=b)
    m, mask = led.returns_matrix("ma", with_mask=True)
    assert set(m.columns) == {"a", "b"}
    assert len(m) == len(a.index.union(b.index))
    assert m.notna().all().all()
    assert mask["a"].sum() == 20 and mask["b"].sum() == 20 and (~mask).any().any()
    np.testing.assert_allclose(m["a"][mask["a"]].to_numpy(), a.to_numpy())
    assert led.returns_matrix("none").empty


def test_append_only(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    led.record_trial("a", "ma", returns=_ret(1))
    c = sqlite3.connect(str(tmp_path / "t.sqlite"))
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("DELETE FROM trials")
    c.close()


def test_default_path_helper(tmp_path, monkeypatch):
    from bist_signal_bot.storage import paths
    monkeypatch.setattr(paths, "PROJECT_ROOT", tmp_path)
    p = default_ledger_path()
    assert p.name == "trials.sqlite" and p.parent.name == "edge_validation"
    assert tmp_path in p.parents
