import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation import survivorship as sv


class _Ctx:
    def __init__(self):
        idx = pd.bdate_range("2018-01-01", "2023-12-29")
        close = pd.DataFrame(1.0, index=idx, columns=["OLD", "NEW"])
        close.loc[idx < "2023-01-02", "NEW"] = np.nan  # NEW lists 2023
        self.close, self.index, self.symbols = close, idx, ["OLD", "NEW"]


def _events():
    t0 = pd.to_datetime(["2023-03-01", "2023-03-01", "2023-09-01", "2023-09-01"])
    return pd.DataFrame({"symbol": ["OLD", "NEW", "OLD", "NEW"], "t0": t0, "net_ret": [0.01, 0.05, 0.01, 0.05]})


def test_age_weighting_monotonic():
    ctx, ev = _Ctx(), _events()
    means = [sv.age_weight_sensitivity(ctx, ev, full_weight_days=n)["weighted"]["mean_net_excess_bps"]
             for n in (1, 300, 750, 3000)]
    assert means == sorted(means, reverse=True)  # larger N -> young (high-return) symbols weigh less
    assert means[0] > means[-1]
    assert sv.age_weight_sensitivity(ctx, ev)["retained_fraction"] < 1.0


def test_exclusion_removes_young():
    r = sv.exclude_recent_listings_sensitivity(_Ctx(), _events())
    assert r["excluded_symbols"] == ["NEW"] and r["n_excluded"] == 2
    assert abs(r["kept"]["mean_net_excess_bps"] - 100.0) < 1e-6


def test_statement_always_and_empty_ok():
    ctx = _Ctx()
    for ev in (None, pd.DataFrame(), _events()):
        b = sv.optimism_bound(ctx, ev)
        assert b["statement"] == sv.HONESTY_STATEMENT and b["measurable"] is False
        assert b["n_symbols_lt_2y_history"] == 1
    assert sv.optimism_bound(ctx, None)["retained_fraction_age_weighted"] is None
    assert "İYİMSERLİK SINIRI" in sv.header_line(None)
