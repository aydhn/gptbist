"""PaperTradingEngine.run adapter + orchestrator PAPER_RUN (offline). No real order sent."""
from types import SimpleNamespace

from bist_signal_bot.paper.engine import PaperTradingDependencies, PaperTradingEngine
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.strategies.engine import StrategyEngine


def build(settings_factory, tmp_path, **over):
    s = settings_factory(PAPER_DEFAULT_ACCOUNT_ID="acc_run", **over)
    return s, PaperTradingEngine(PaperTradingDependencies(
        ledger_store=PaperLedgerStore(s, base_dir=tmp_path), strategy_engine=StrategyEngine(s),
        data_service=MarketDataService(s), settings=s))


def test_run_creates_account_and_zero_signal_is_success(settings_factory, tmp_path):
    s, eng = build(settings_factory, tmp_path)
    out = eng.run("moving_average_trend", symbols=["ASELS"], source="local", timeframe="1d")
    for k in ("equity", "cash", "open_positions", "realized_pnl", "orders_count", "signals_count"):
        assert k in out
    assert out["status"] != "ERROR" and out["orders_count"] == 0
    assert out["no_real_order_sent"] is True
    assert "No real order sent." in out["message"]
    assert out["equity"] == 100000.0


def test_run_twice_does_not_duplicate_account(settings_factory, tmp_path):
    s, eng = build(settings_factory, tmp_path)
    eng.run("moving_average_trend", symbols=["ASELS"], source="local")
    eng.run("moving_average_trend", symbols=["ASELS"], source="local")
    state = eng.load_state("acc_run")
    assert state.account.account_id == "acc_run"
    assert sum(1 for e in state.events if e.event_type.value == "ACCOUNT_INITIALIZED") == 1


def test_orchestrator_paper_run_not_mock(settings_factory, tmp_path):
    from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
    from bist_signal_bot.runtime.models import RuntimePipelineResult  # noqa: F401
    s, eng = build(settings_factory, tmp_path)
    orch = RuntimeOrchestrator(paper_engine=eng, settings=s)
    cfg = orch.build_default_pipeline_config()
    cfg.use_paper = True
    cfg.symbols = ["ASELS"]
    res = SimpleNamespace(job_results=[], metadata={}, paper_result_summary=None)
    orch._execute_paper_run(cfg, res)
    assert res.job_results
    assert "mock_paper" not in res.paper_result_summary
    assert res.paper_result_summary.get("no_real_order_sent") is True
