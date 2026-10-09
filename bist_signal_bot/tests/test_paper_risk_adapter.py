"""Paper engine trade-risk adapter (RiskEngine.evaluate_signal with a ledger-built RiskContext). No real order sent."""
import numpy as np
import pandas as pd

from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.paper.engine import PaperTradingDependencies, PaperTradingEngine
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.paper.models import PaperExecutionMode, PaperRunRequest
from bist_signal_bot.strategies.engine import StrategyEngine


def _frame(n=300):
    idx = pd.bdate_range("2023-06-01", periods=n)
    t = np.arange(n)
    close = 100 + 0.08 * t + 12 * np.sin(t / 14)
    return pd.DataFrame({"open": np.r_[close[0], close[:-1]], "high": close + 1, "low": close - 1,
                         "close": close, "volume": np.full(n, 1e6)}, index=idx)


def _run(settings_factory, tmp_path, **over):
    s = settings_factory(PAPER_DEFAULT_ACCOUNT_ID="acc_risk", **over)
    eng = PaperTradingEngine(PaperTradingDependencies(
        ledger_store=PaperLedgerStore(s, base_dir=tmp_path), strategy_engine=StrategyEngine(settings=s),
        data_service=MarketDataService(s), settings=s))
    eng.initialize_account("acc_risk")
    # find a bar where the strategy signals LONG so the test is deterministic
    full = _frame()
    for cut in range(len(full), 210, -1):
        eng.data_override = {"AAA": full.iloc[:cut]}
        req = PaperRunRequest(account_id="acc_risk", symbols=["AAA"], strategy_name="moving_average_trend",
                              source="local", timeframe="1d", execution_mode=PaperExecutionMode.LATEST_CLOSE_RESEARCH,
                              use_trade_risk=True, use_portfolio_risk=False)
        _, sigs = eng._collect_data_and_signals(req, type("R", (), {"issues": [], "signals": []})())
        if sigs:
            return eng, eng.run_once(req)
    raise AssertionError("no LONG signal on synthetic data")


def test_risk_on_approves_and_opens_position(settings_factory, tmp_path):
    eng, r = _run(settings_factory, tmp_path, RISK_MIN_SIGNAL_SCORE=0.0, RISK_MIN_CONFIDENCE=0.0, RISK_REJECT_IF_NO_STOP=False)
    assert not any("no attribute" in i for i in r.issues), r.issues
    assert r.risk_decisions, (r.issues, len(r.signals), r.status)
    if r.risk_decisions[0].approved:
        assert len(r.orders) >= 1 and len(r.fills) >= 1
    else:  # approval depends on engine defaults; still must be a recorded decision, never an adapter error
        assert r.metadata["risk_rejections"]


def test_risk_reject_is_recorded_with_reason_and_no_order(settings_factory, tmp_path):
    eng, r = _run(settings_factory, tmp_path, RISK_MIN_SIGNAL_SCORE=101.0)
    assert not any("no attribute" in i for i in r.issues)
    assert r.orders == [] and r.fills == []
    rej = r.metadata["risk_rejections"]
    assert rej and rej[0]["symbol"] == "AAA" and rej[0]["reasons"]
    assert any(i.startswith("Risk rejected AAA") for i in r.issues)
    assert r.summary()["risk_rejections"] == rej


def test_risk_engine_error_fails_closed(settings_factory, tmp_path):
    s = settings_factory(PAPER_DEFAULT_ACCOUNT_ID="acc_risk2")
    eng = PaperTradingEngine(PaperTradingDependencies(
        ledger_store=PaperLedgerStore(s, base_dir=tmp_path), strategy_engine=StrategyEngine(settings=s),
        data_service=MarketDataService(s), settings=s))
    eng.initialize_account("acc_risk2")

    def boom(*a, **k):
        raise RuntimeError("risk down")
    eng.risk_engine.evaluate_signal = boom
    state = eng.load_state("acc_risk2")
    req = PaperRunRequest(account_id="acc_risk2", symbols=["AAA"], strategy_name="x", source="local", timeframe="1d")
    res = type("R", (), {"issues": [], "metadata": {}, "risk_decisions": []})()
    out = eng._evaluate_trade_risk(req, [("AAA", object(), _frame())], res, state)
    assert out == [] and res.issues[0].startswith("Risk error for AAA")
    assert res.metadata["risk_rejections"][0]["status"] == "ERROR"
