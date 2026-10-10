import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.daily import macro
from bist_signal_bot.edge_validation.cash_benchmark import daily_cash_returns
from bist_signal_bot.edge_validation.real_returns import (build_real_report, price_level, real_cagr,
                                                          report_for_nav)


class Ctx:
    def __init__(self, idx, bench=None, usd=None, rate=0.37):
        self.benchmark, self.usdtry, self.cash_rate = bench, usd, rate
        self.cash_ret = daily_cash_returns(idx, rate, 0.0)


def _cpi(months=60, monthly=0.03, start="2018-01-01"):
    idx = pd.date_range(start, periods=months, freq="MS")
    return pd.Series(100 * (1 + monthly) ** np.arange(months), index=idx)


def test_real_cagr_known_inflation():
    cpi = _cpi()
    idx = pd.bdate_range("2019-01-01", "2021-12-31")
    r = pd.Series(1.8 ** (1 / 252) - 1, index=idx)
    d = real_cagr(r, cpi)
    infl = 1.03 ** 12 - 1
    assert d["inflation_cagr"] == pytest.approx(infl, rel=0.02)
    assert d["real_cagr"] == pytest.approx((1 + d["nominal_cagr"]) / (1 + d["inflation_cagr"]) - 1, rel=0.03)


def test_truncates_to_coverage_and_never_extrapolates():
    cpi = _cpi(months=24)  # ends 2019-12-01
    idx = pd.bdate_range("2018-06-01", "2021-12-31")
    r = pd.Series(0.001, index=idx)
    d = real_cagr(r, cpi)
    assert d["end"] <= pd.Timestamp("2019-12-01")
    rep = build_real_report(r, Ctx(idx), cpi)
    assert any("covers only" in w for w in rep["warnings"])
    assert rep["window"][1] <= "2019-12-01"


def test_causal_mode_lag():
    cpi = _cpi(months=12)
    idx = pd.bdate_range("2018-01-01", "2019-06-30")
    p0 = price_level(cpi, idx, "causal", lag_months=0)
    p1 = price_level(cpi, idx, "causal", lag_months=1)
    d = pd.Timestamp("2018-03-15")
    assert p0[d] == pytest.approx(cpi.iloc[1])  # Feb index known from March 1
    assert p1[d] == pytest.approx(cpi.iloc[0])  # one more month of lag
    assert np.isnan(p1.iloc[0])


def test_missing_cpi_warns_not_assumes():
    idx = pd.bdate_range("2019-01-01", "2020-12-31")
    rep = build_real_report(pd.Series(0.0005, index=idx), Ctx(idx), None)
    assert rep["real_cagr"] is None and any("CPI MISSING" in w for w in rep["warnings"])
    assert "CANNOT BE EVALUATED" in rep["target_statement"]


def test_report_comparators_and_distribution():
    idx = pd.bdate_range("2018-02-01", "2022-12-30")
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0.0012, 0.01, len(idx)), index=idx)
    bench = pd.Series(100 * np.cumprod(1 + rng.normal(0.0005, 0.012, len(idx))), index=idx)
    usd = pd.Series(10 * np.cumprod(1 + np.full(len(idx), 0.0004)), index=idx)
    rep = build_real_report(r, Ctx(idx, bench, usd), _cpi())
    c = rep["comparators"]
    assert set(c) == {"xu100", "cash_gross", "deposit_net_stopaj", "usdtry"}
    assert c["deposit_net_stopaj"]["cagr"] < c["cash_gross"]["cagr"]  # stopaj reduces deposit return
    assert rep["rolling_12m"]["n"] > 100 and 0 <= rep["pct_12m_real_ge_target"] <= 1
    assert rep["usd_cagr"] < rep["nominal_cagr"]
    assert "NOT REACHED" in rep["target_statement"] or rep["target_reached"]


def test_report_for_nav_with_overlay():
    idx = pd.bdate_range("2018-02-01", "2022-12-30")
    rng = np.random.default_rng(2)
    r = rng.normal(0.001, 0.01, len(idx))
    r[400:450] = -0.015
    nav = pd.DataFrame({"ret": r}, index=idx)
    out = report_for_nav(nav, Ctx(idx), cpi=_cpi())
    assert out["overlay"]["max_drawdown"] > out["base"]["max_drawdown"]
    assert out["overlay_summary"]["n_halts"] >= 1


def test_load_cpi_local_file_and_fail_loudly(tmp_path):
    with pytest.raises(macro.CPIUnavailable):
        macro.load_cpi(None, allow_fetch=False, directory=tmp_path)
    s = _cpi(30)
    pd.DataFrame({"date": s.index, "index": s.to_numpy()}).to_csv(tmp_path / "cpi_tr.csv", index=False)
    got, src = macro.load_cpi(None, allow_fetch=False, directory=tmp_path)
    assert src.startswith("local:") and len(got) == 30


def test_fetch_fred_injected_and_html_rejected(tmp_path):
    s = _cpi(30)
    text = "observation_date,TURCPIALLMINMEI\n" + "\n".join(f"{d.date()},{v}" for d, v in s.items()) + "\n2030-01-01,.\n"
    got, src = macro.load_cpi(None, directory=tmp_path, http_get=lambda u, t: text)
    assert src.startswith("fred:") and len(got) == 30 and (tmp_path / "cpi_tr_fred.csv").exists()
    got2, src2 = macro.load_cpi(None, directory=tmp_path, http_get=lambda u, t: "<html></html>")
    assert src2.startswith("cache:")
    with pytest.raises(macro.CPIUnavailable):
        macro.fetch_fred_cpi(http_get=lambda u, t: "<html></html>")
