import pandas as pd
from types import SimpleNamespace
from bist_signal_bot.scanner.engine import SignalScannerEngine, SignalScannerDependencies
from bist_signal_bot.scanner.models import ScanRequest, ScanUniverseMode, ScanCandidateStatus, ScanStatus
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

def test_scan_symbol_exception():
    class ExceptionStrategyEngine:
        def run_strategy_on_data(self, *args, **kwargs):
            raise Exception("Simulated execution exception")

    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=MockDataService(),
        strategy_engine=ExceptionStrategyEngine(),
        risk_engine=MockRiskEngine(),
        portfolio_risk_engine=MockPortfolioRiskEngine(),
    ))
    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"]
    )
    res = engine.scan_symbol("A", req)

    assert res.status == ScanCandidateStatus.ERROR
    assert len(res.issues) == 1

    issue = res.issues[0]
    assert issue.stage == "EXECUTION"
    assert issue.symbol == "A"
    assert "Simulated execution exception" in issue.message

    assert issue.data_provider == engine.settings.DEFAULT_DATA_PROVIDER
    assert issue.data_lineage_source_id == "UNKNOWN"
    assert issue.data_freshness_age_hours == 0.0
    assert issue.data_quality_warnings == []

    assert res.data_provider == engine.settings.DEFAULT_DATA_PROVIDER
    assert res.data_lineage_source_id == "UNKNOWN"
    assert res.data_freshness_age_hours == 0.0
    assert res.data_quality_warnings == []
    assert res.elapsed_seconds >= 0.0

def test_scan_resolve_symbols_validation_error():
    from bist_signal_bot.core.exceptions import ScannerValidationError
    from unittest.mock import MagicMock

    engine = SignalScannerEngine(deps=SignalScannerDependencies(
        data_service=MockDataService(),
        strategy_engine=MockStrategyEngine()
    ))

    # Mock resolve_symbols to raise ScannerValidationError
    engine.resolve_symbols = MagicMock(side_effect=ScannerValidationError("Test validation error"))

    req = ScanRequest(
        strategy_name="t",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"]
    )

    report = engine.scan(req)

    # Verify the fallback mechanism
    assert report.status == ScanStatus.FAILED
    assert len(report.issues) == 1
    assert report.issues[0].stage == "RESOLVE"
    assert "Test validation error" in report.issues[0].message

def test_build_default_request():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine()))
    req = engine.build_default_request(strategy_name="test_strat")
    assert isinstance(req, ScanRequest)
    assert req.strategy_name == "test_strat"
    assert req.source == engine.settings.SCANNER_DEFAULT_SOURCE
    assert req.timeframe == engine.settings.SCANNER_DEFAULT_TIMEFRAME
    assert req.top_n == engine.settings.SCANNER_DEFAULT_TOP_N
    assert req.use_trade_risk == engine.settings.SCANNER_USE_TRADE_RISK
    assert req.use_portfolio_risk == engine.settings.SCANNER_USE_PORTFOLIO_RISK
    assert req.continue_on_error == engine.settings.SCANNER_CONTINUE_ON_ERROR
    assert req.save_report == engine.settings.SCANNER_SAVE_REPORT
    assert req.send_telegram == engine.settings.SCANNER_SEND_TELEGRAM
    assert req.min_signal_score == engine.settings.SCANNER_MIN_SIGNAL_SCORE
    assert req.min_confidence == engine.settings.SCANNER_MIN_CONFIDENCE
    assert req.min_final_score == engine.settings.SCANNER_MIN_FINAL_SCORE
    assert req.universe_mode == ScanUniverseMode.SYMBOLS
    assert req.symbols == []
    assert req.watchlist_name is None
    assert req.group_name is None

def test_build_default_request_with_kwargs():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=MockDataService(), strategy_engine=MockStrategyEngine()))
    req = engine.build_default_request(
        strategy_name="test_strat_2",
        source="custom_source",
        timeframe="1h",
        symbols=["AAPL", "MSFT"],
        watchlist_name="my_watch",
        group_name="my_group",
        all=True,
        params={"p1": "v1"}
    )

    assert req.strategy_name == "test_strat_2"
    assert req.source == "custom_source"
    assert req.timeframe == "1h"
    assert req.symbols == ["AAPL", "MSFT"]
    assert req.watchlist_name == "my_watch"
    assert req.group_name == "my_group"
    assert req.universe_mode == ScanUniverseMode.ALL
    assert req.params == {"p1": "v1"}
