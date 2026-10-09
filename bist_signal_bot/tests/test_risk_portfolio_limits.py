import pandas as pd

from bist_signal_bot.risk.portfolio_limits import PortfolioLimits

EQ = 1_000_000.0
PL = PortfolioLimits()


def _chk(order, positions=(), settings=None, **kw):
    return PL.check(order, list(positions), EQ, settings=settings or {}, **kw)


def test_ok():
    r = _chk({"symbol": "A", "notional": 50_000.0})
    assert r.allowed and r.reasons == [] and "No real order sent" in r.note


def test_duplicate_symbol():
    r = _chk({"symbol": "A", "notional": 10_000.0}, [{"symbol": "A", "notional": 10_000.0}])
    assert "duplicate_symbol" in r.reasons and not r.allowed


def test_max_open_positions():
    pos = [{"symbol": f"S{i}", "notional": 1000.0} for i in range(3)]
    r = _chk({"symbol": "A", "notional": 1000.0}, pos, {"RISK_MAX_OPEN_POSITIONS": 3})
    assert r.reasons == ["max_open_positions"]
    assert _chk({"symbol": "A", "notional": 1000.0}, pos, {"RISK_MAX_OPEN_POSITIONS": 4}).allowed


def test_gross_exposure():
    pos = [{"symbol": f"S{i}", "notional": 90_000.0} for i in range(10)]  # 900k
    r = _chk({"symbol": "A", "notional": 100_001.0}, pos, {"RISK_MAX_OPEN_POSITIONS": 20})
    assert "max_gross_exposure" in r.reasons
    assert _chk({"symbol": "A", "notional": 100_000.0}, pos, {"RISK_MAX_OPEN_POSITIONS": 20}).allowed


def test_single_name_qty_price_form():
    r = _chk({"symbol": "A", "qty": 1001, "price": 100.0})
    assert r.reasons == ["max_single_name"]
    assert _chk({"symbol": "A", "qty": 1000, "price": 100.0}).allowed


def test_sector():
    smap = {"A": "BANK", "B": "BANK", "C": "BANK", "D": "OIL"}
    pos = [{"symbol": "B", "notional": 100_000.0}, {"symbol": "C", "notional": 100_000.0},
           {"symbol": "D", "notional": 100_000.0}]
    r = _chk({"symbol": "A", "notional": 100_001.0}, pos, {"RISK_MAX_POSITION_PCT": 0.5}, sector_map=smap)
    assert r.reasons == ["max_sector"]
    assert _chk({"symbol": "A", "notional": 100_000.0}, pos, {"RISK_MAX_POSITION_PCT": 0.5}, sector_map=smap).allowed


def test_cluster_exposure():
    cm = pd.DataFrame([[1, 0.9, 0.1], [0.9, 1, 0.1], [0.1, 0.1, 1]], index=list("ABC"), columns=list("ABC"))
    pos = [{"symbol": "B", "notional": 100_000.0}, {"symbol": "C", "notional": 100_000.0}]
    r = _chk({"symbol": "A", "notional": 100_000.0}, pos, {"RISK_MAX_CLUSTER_PCT": 0.15}, corr_matrix=cm)
    assert r.reasons == ["max_cluster_exposure"]
    # uncorrelated C does not join the cluster
    pos2 = [{"symbol": "C", "notional": 100_000.0}]
    assert _chk({"symbol": "A", "notional": 100_000.0}, pos2, {"RISK_MAX_CLUSTER_PCT": 0.15}, corr_matrix=cm).allowed
    # dict-of-dict matrix also works
    d = {"A": {"B": -0.95}, "B": {"A": -0.95}}
    r = _chk({"symbol": "A", "notional": 100_000.0}, [pos[0]], {"RISK_MAX_CLUSTER_PCT": 0.15}, corr_matrix=d)
    assert "max_cluster_exposure" in r.reasons


def test_daily_turnover():
    r = _chk({"symbol": "A", "notional": 50_000.0}, traded_today_value=1_960_000.0)
    assert r.reasons == ["max_daily_turnover"]
    assert _chk({"symbol": "A", "notional": 40_000.0}, traded_today_value=1_960_000.0).allowed
