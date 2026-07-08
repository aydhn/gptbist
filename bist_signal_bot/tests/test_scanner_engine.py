import pytest
import pandas as pd
from types import SimpleNamespace
from bist_signal_bot.scanner.engine import SignalScannerEngine, SignalScannerDependencies
from bist_signal_bot.scanner.models import ScanRequest, ScanUniverseMode, ScanCandidateStatus, ScanStatus, ScanSortKey
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategies.models import StrategyExecutionResult, StrategyExecutionIssue
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus
from bist_signal_bot.risk.engine import RiskEngine
from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine

class MockDataService:
    provider = SimpleNamespace(vendor="MOCK")
    store = SimpleNamespace(exists=lambda *args, **kwargs: True)

    def get_ohlcv(self, symbol, **kwargs):
        if symbol == "BADDATA":
            return SimpleNamespace(data=pd.DataFrame())
        return SimpleNamespace(data=pd.DataFrame({'close': [100, 101, 102]}))

    def get_many_ohlcv(self, symbols, **kwargs):
        if "BATCHERROR" in symbols:
            raise Exception("Simulated batch fetch error")
        results = {}
        for symbol in symbols:

            if symbol == "BADDATA":
                results[symbol] = SimpleNamespace(data=pd.DataFrame())
            else:
                results[symbol] = SimpleNamespace(data=pd.DataFrame({'close': [100, 101, 102]}))
        return results

class MockStrategyEngine:
    def run_strategy_on_data(self, strategy_name, symbol, data, **kwargs):
        if symbol == "ERRORSTRAT":
            return StrategyExecutionResult(request={"strategy_name": strategy_name, "symbol": symbol, "run_mode": "RESEARCH", "timeframe": "1d", "params": {}}, status="error", issues=[StrategyExecutionIssue(strategy_name=strategy_name, symbol=symbol, message="error")])
        sig = SignalCandidate(strategy_name=strategy_name, symbol=symbol, direction=SignalDirection.LONG, score=80.0, strength=SignalStrength.STRONG, confidence=80.0)
        return StrategyExecutionResult(request={"strategy_name": strategy_name, "symbol": symbol, "run_mode": "RESEARCH", "timeframe": "1d", "params": {}}, status="success", candidate=sig, )

class MockRiskEngine:
    def build_default_context(self):
        return None
    def evaluate_signal(self, signal, context, data):
        from bist_signal_bot.risk.models import RiskFilterResult
        return RiskDecision(signal=signal, side=signal.direction, approved=True, filter_result=RiskFilterResult(status=RiskDecisionStatus.APPROVED, passed=True, active_rules=[], triggered_rules=[]), symbol=signal.symbol, status=RiskDecisionStatus.APPROVED, final_score=90.0)

class MockPortfolioRiskEngine:
    def evaluate_portfolio_signals(self, signals, state):
        from bist_signal_bot.portfolio.models import PortfolioRiskDecision, PortfolioDecisionStatus
        return PortfolioRiskDecision(portfolio_state=state, input_signals=signals, trade_risk_decisions=[], approved_count=1, rejected_count=0, reduced_count=0, reject_reasons=[], warnings=[], status=PortfolioDecisionStatus.APPROVED, allocations=[])

def test_resolve_symbols():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine()))
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A", "B", "A"])
    symbols = engine.resolve_symbols(req)
    assert symbols == ["A", "B"]

def test_default_risk_engines_receive_settings_by_keyword():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine()))

    assert isinstance(engine.risk_engine, RiskEngine)
    assert isinstance(engine.portfolio_risk_engine, PortfolioRiskEngine)
    assert not isinstance(engine.risk_engine.position_sizer, Settings)

def test_scan_symbol_success():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine(), risk_engine=MockRiskEngine(), portfolio_risk_engine=MockPortfolioRiskEngine()))
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    res = engine.scan_symbol("A", req)
    assert res.status == ScanCandidateStatus.PASSED

def test_scan_continue_on_error():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine(), risk_engine=MockRiskEngine(), portfolio_risk_engine=MockPortfolioRiskEngine()))
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["BADDATA", "A"], continue_on_error=True)
    report = engine.scan(req)
    assert report.status == ScanStatus.PARTIAL_SUCCESS
    assert report.passed_count == 1
    assert report.error_count == 1

def test_local_scan_does_not_fall_back_to_network():
    data_service = MockDataService()
    data_service.store = SimpleNamespace(exists=lambda *args, **kwargs: False)
    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=data_service,
        strategy_engine=MockStrategyEngine(),
        risk_engine=MockRiskEngine(),
        portfolio_risk_engine=MockPortfolioRiskEngine(),
    ))
    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"],
        source="local_file",
    )

    res = engine.scan_symbol("A", req)

    assert res.status == ScanCandidateStatus.ERROR
    assert "network fallback is disabled" in res.issues[0].message


def test_scan_batch_fetch_fallback():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=MockDataService(),
        strategy_engine=MockStrategyEngine(),
        risk_engine=MockRiskEngine(),
        portfolio_risk_engine=MockPortfolioRiskEngine(),
    ))
    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["BATCHERROR", "A"],
        continue_on_error=True
    )
    report = engine.scan(req)
    # The batch error falls back to sequential. The sequential fetch returns valid dataframe for both "BATCHERROR" and "A",
    # but the symbol might be processed further leading to an error or pass.
    # We just need to check the batch fallback was hit and we continued.
    assert len(report.results) == 2

def test_telegram_notification_failure_does_not_crash():
    class MockNotifier:
        def send_message(self, msg):
            raise Exception("Telegram failure")

    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=MockDataService(),
        strategy_engine=MockStrategyEngine(),
        notifier=MockNotifier()
    ))
    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"],
        send_telegram=True
    )
    report = engine.scan(req)
    assert report.status == ScanStatus.SUCCESS
    assert report.passed_count == 1

def test_log_research_events_failure_does_not_crash(monkeypatch):
    from bist_signal_bot.scanner.engine import SignalScannerEngine, SignalScannerDependencies
    from bist_signal_bot.scanner.models import ScanRequest, ScanUniverseMode

    def mock_create_research_ledger(*args, **kwargs):
        class MockLedger:
            def append_run(self, *args, **kwargs):
                raise Exception("Simulated ledger failure")
        return MockLedger()

    def mock_create_research_event_builder(*args, **kwargs):
        class MockBuilder:
            def from_scan_report(self, report):
                return "mock_run_obj"
        return MockBuilder()

    monkeypatch.setattr("bist_signal_bot.app.research_app.create_research_ledger", mock_create_research_ledger)
    monkeypatch.setattr("bist_signal_bot.app.research_app.create_research_event_builder", mock_create_research_event_builder)

    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=MockDataService(),
        strategy_engine=MockStrategyEngine(),
        risk_engine=MockRiskEngine(),
        portfolio_risk_engine=MockPortfolioRiskEngine()
    ))

    engine.settings.ENABLE_RESEARCH_LEDGER = True
    engine.settings.RESEARCH_AUTO_LOG_SCAN = True

    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"]
    )

    report = engine.scan(req)
    assert report is not None
