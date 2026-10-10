import itertools

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.xsection import DailyContext, check_score_causality
from bist_signal_bot.tests.test_xsection_daily import make_panel

NAMES = ["xs_lowvol_x_momentum", "xs_multi_horizon_ensemble", "xs_regime_momentum", "xs_sector_rs_liquid",
         "xs_turnover_damped_momentum"]
PARAMS = {"xs_lowvol_x_momentum": {"vol_window": 60, "mom_lookback": 126},
          "xs_multi_horizon_ensemble": {"variant": "B"},
          "xs_regime_momentum": {"ma_window": 100, "vol_thr": 0.8},
          "xs_sector_rs_liquid": {"lookback": 20, "adv_q": 0.5, "n_clusters": 5, "corr_window": 120},
          "xs_turnover_damped_momentum": {"halflife": 3, "lookback": 60}}


@pytest.fixture(scope="module")
def ctx():
    p = make_panel(3, n_sym=30, days=800)
    idx = next(iter(p.values())).index
    rng = np.random.default_rng(5)
    bm = pd.Series(1000 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, len(idx)))), index=idx)
    return DailyContext.from_panel(p, bm, min_adv=5e6)


def _combos(f):
    return [dict(zip(f.default_grid, v)) for v in itertools.product(*f.default_grid.values())]


@pytest.mark.parametrize("name", NAMES)
def test_registered_tiny_valid_grid(name):
    f = DAILY_FAMILIES[name]
    combos = _combos(f)
    assert 1 <= len(combos) <= 4
    assert all(f.valid(c) for c in combos)


@pytest.mark.parametrize("name", NAMES)
def test_shape_causal_masked(ctx, name):
    f, p = DAILY_FAMILIES[name], PARAMS[name]
    check_score_causality(f, ctx, p)
    s = f.score(ctx, p)
    assert list(s.index) == list(ctx.index) and list(s.columns) == ctx.symbols
    assert np.isfinite(s.to_numpy(float)).any()
    assert not np.isinf(s.to_numpy(float)).any()
    assert s.where(~ctx.universe_mask).notna().sum().sum() == 0  # NaN for ineligible cells


def test_turnover_damping_reduces_rank_churn(ctx):
    f = DAILY_FAMILIES["xs_turnover_damped_momentum"]
    a = f.score(ctx, {"halflife": 1, "lookback": 60}).diff().abs().mean().mean()
    b = f.score(ctx, {"halflife": 5, "lookback": 60}).diff().abs().mean().mean()
    assert b < a


def test_regime_needs_benchmark(ctx):
    nb = DailyContext(ctx.open, ctx.close, ctx.volume, None)
    with pytest.raises(ValueError):
        DAILY_FAMILIES["xs_regime_momentum"].score(nb, PARAMS["xs_regime_momentum"])


def test_sector_liquid_subset_of_sector(ctx):
    p = PARAMS["xs_sector_rs_liquid"]
    liq = DAILY_FAMILIES["xs_sector_rs_liquid"].score(ctx, p)
    full = DAILY_FAMILIES["xs_rel_strength_sector"].score(ctx, {k: p[k] for k in ("lookback", "n_clusters", "corr_window")})
    assert liq.notna().sum().sum() < full.where(ctx.universe_mask).notna().sum().sum()
