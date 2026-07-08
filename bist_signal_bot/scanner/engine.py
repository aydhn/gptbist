
from bist_signal_bot.app.context_fusion_app import create_context_fusion_engine
import logging
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ScannerValidationError, ScannerExecutionError
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.models import Timeframe
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.ml.inference.models import MLInferenceConfig
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.security.preflight import SecurityPreflightRunner
from bist_signal_bot.storage.paths import get_data_dir

from bist_signal_bot.risk.engine import RiskEngine
from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine
from bist_signal_bot.paper.engine import PaperTradingEngine
from bist_signal_bot.scanner.models import (
    ScanRequest, ScanReport, SymbolScanResult, SymbolScanIssue, ScanUniverseMode,
    ScanStatus, ScanCandidateStatus, ScanRankingItem
)
from bist_signal_bot.scanner.ranking import ScanRanker
from bist_signal_bot.scanner.filters import ScanFilterEngine

from bist_signal_bot.strategies.models import StrategyRunMode


@dataclass
class SignalScannerDependencies:
    data_service: MarketDataService
    strategy_engine: StrategyEngine
    risk_engine: Optional[RiskEngine] = None
    portfolio_risk_engine: Optional[PortfolioRiskEngine] = None
    paper_engine: Optional[PaperTradingEngine] = None
    ranker: Optional[ScanRanker] = None
    filter_engine: Optional[ScanFilterEngine] = None
    settings: Optional[Settings] = None
    notifier: Optional[Any] = None
    logger: Optional[logging.Logger] = None
    ml_inference_engine: Optional[Any] = None

class SignalScannerEngine:

    def __init__(self, deps: SignalScannerDependencies):
        self.settings = deps.settings or Settings()
        self.logger = deps.logger or logging.getLogger(__name__)
        self.data_service = deps.data_service
        self.strategy_engine = deps.strategy_engine
        self.kill_switch = KillSwitchManager(self.settings, get_data_dir(self.settings))
        self.security_preflight = SecurityPreflightRunner(self.settings, kill_switch=self.kill_switch)
        self.ml_inference_engine = deps.ml_inference_engine
        self.risk_engine = deps.risk_engine or RiskEngine(settings=self.settings)
        self.portfolio_risk_engine = deps.portfolio_risk_engine or PortfolioRiskEngine(settings=self.settings)
        self.paper_engine = deps.paper_engine
        self.ranker = deps.ranker or ScanRanker(self.settings)
        self.filter_engine = deps.filter_engine or ScanFilterEngine(self.settings)
        self.notifier = deps.notifier
        self.universe = SymbolUniverse()

    def resolve_symbols(self, request: ScanRequest) -> List[str]:
        symbols = []
        mode = request.universe_mode

        if mode == ScanUniverseMode.SYMBOLS or mode == ScanUniverseMode.CUSTOM:
            symbols = request.symbols
        elif mode == ScanUniverseMode.WATCHLIST:
            if not request.watchlist_name:
                raise ScannerValidationError("Watchlist name is required for WATCHLIST mode")
            wl = self.universe.get_watchlist(request.watchlist_name)
            if not wl:
                raise ScannerValidationError(f"Watchlist not found: {request.watchlist_name}")
            symbols = wl.symbols
        elif mode == ScanUniverseMode.GROUP:
            if not request.group_name:
                raise ScannerValidationError("Group name is required for GROUP mode")
            symbols = [s.symbol for s in self.universe.list_symbols(active_only=True) if s.group == request.group_name]
        elif mode == ScanUniverseMode.ALL:
            symbols = [s.symbol for s in self.universe.list_symbols(active_only=True)]

        # Remove duplicates, maintain order
        seen = set()
        unique_symbols = []
        for sym in symbols:
            if sym not in seen:
                seen.add(sym)
                unique_symbols.append(sym)

        if not unique_symbols:
            raise ScannerValidationError("Resolved symbol list is empty")

        # Limit max symbols
        max_syms = self.settings.SCANNER_MAX_SYMBOLS_PER_RUN
        if len(unique_symbols) > max_syms:
            self.logger.warning(f"Symbol list exceeds max ({max_syms}), truncating")
            unique_symbols = unique_symbols[:max_syms]

        return unique_symbols

    def scan_symbol(self, symbol: str, request: ScanRequest, pre_fetched_data: Optional[Any] = None) -> SymbolScanResult:
        start_time = time.time()
        issues = []

        try:
            # 1. Fetch data
            timeframe = Timeframe(request.timeframe)
            if pre_fetched_data is not None:
                market_data = pre_fetched_data
            else:
                if request.source in {"local", "local_file"}:
                    store = getattr(self.data_service, "store", None)
                    provider = getattr(self.data_service, "provider", None)
                    vendor = getattr(provider, "vendor", None)
                    if store is None or vendor is None or not store.exists(symbol, vendor, timeframe):
                        raise ScannerExecutionError(
                            f"No local data found for {symbol} ({timeframe.value}); network fallback is disabled."
                        )

                market_data = self.data_service.get_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    refresh=False,
                    save=False,
                    allow_provider_fallback=request.source not in {"local", "local_file"},
                )
            data = getattr(market_data, "data", market_data)
            if request.rows:
                data = data.tail(request.rows)
            if data is None or data.empty:
                issues.append(SymbolScanIssue(symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], stage="DATA", message="No data returned"))
                return SymbolScanResult(
                    symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], status=ScanCandidateStatus.ERROR, issues=issues,
                    elapsed_seconds=time.time() - start_time
                )

            # 2. Run strategy
            strat_result = self.strategy_engine.run_strategy_on_data(
                strategy_name=request.strategy_name,
                symbol=symbol,
                data=data,
                params=request.params,
                run_mode=StrategyRunMode.RESEARCH,
                timeframe=request.timeframe
            )

            if strat_result.status == "error":
                issues.append(SymbolScanIssue(symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], stage="STRATEGY", message=strat_result.issues[0].message if strat_result.issues else "Unknown strategy error"))
                return SymbolScanResult(
                    symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], status=ScanCandidateStatus.ERROR, issues=issues,
                    elapsed_seconds=time.time() - start_time
                )

            if not strat_result.candidate and not strat_result.signals:
                issues.append(SymbolScanIssue(symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], stage="STRATEGY", message="No signals returned", severity="INFO"))
                return SymbolScanResult(
                    symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], status=ScanCandidateStatus.FILTERED, issues=issues,
                    reasons=["No signals returned"],
                    elapsed_seconds=time.time() - start_time
                )

            signal = strat_result.candidate or (strat_result.signals[0] if strat_result.signals else None)

            # 3. Trade Risk
            risk_decision = None
            if request.use_trade_risk:
                risk_context = self.risk_engine.build_default_context()
                risk_decision = self.risk_engine.evaluate_signal(signal, risk_context, data)

            return SymbolScanResult(
                symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[],
                status=ScanCandidateStatus.PASSED, # Will be filtered later
                signal=signal,
                risk_decision=risk_decision,
                issues=issues,
                elapsed_seconds=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Error scanning symbol {symbol}: {e}")
            issues.append(SymbolScanIssue(symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], stage="EXECUTION", message=str(e)))
            return SymbolScanResult(
                symbol=symbol,
                data_provider=self.settings.DEFAULT_DATA_PROVIDER,
                data_lineage_source_id="UNKNOWN",
                data_freshness_age_hours=0.0,
                data_quality_warnings=[], status=ScanCandidateStatus.ERROR, issues=issues,
                elapsed_seconds=time.time() - start_time
            )

    def _apply_portfolio_decisions(self, results: List["SymbolScanResult"], portfolio_decision: Any) -> None:
        if not portfolio_decision or not hasattr(portfolio_decision, "allocations") or not portfolio_decision.allocations:
            return

        alloc_map = {alloc.signal: alloc for alloc in portfolio_decision.allocations}
        for res in results:
            if not res.signal:
                continue

            alloc = alloc_map.get(res.signal)
            if not alloc:
                continue

            res.portfolio_status = alloc.status.value
            if alloc.status.value in ["REJECTED", "REDUCED"] and res.status == ScanCandidateStatus.PASSED:
                # Keep PASSED but note portfolio status, or change status. Let's keep PASSED and add reason.
                res.reasons.append(f"Portfolio Engine: {alloc.status.value}")

    def scan(self, request: ScanRequest) -> ScanReport:
        if self.kill_switch.is_active(KillSwitchScope.SCANNER):
            self.logger.warning("SCANNER kill switch is active. Scan aborted.")
            return ScanReport(request=request, status=ScanStatus.FAILED, error="Kill Switch Active")
        started_at = datetime.utcnow()
        start_time = time.time()

        try:
            symbols = self.resolve_symbols(request)
        except ScannerValidationError as e:
            return ScanReport(request=request, status=ScanStatus.FAILED, issues=[SymbolScanIssue(stage="RESOLVE", message=str(e))])

        results, issues = self._scan_all_symbols(symbols, request)
        results = self.filter_engine.filter_results(results, request)
        portfolio_decision = self._simulate_portfolio_risk(results, request, issues)
        rankings = self._rank_results(results, request)
        passed, filtered, rejected, error, watch, status = self._count_statuses(results)
        paper_summary = self._simulate_paper_execution(request, issues)

        report = ScanReport(
            request=request,
            status=status,
            total_symbols=len(symbols),
            processed_symbols=len(results),
            passed_count=passed,
            filtered_count=filtered,
            rejected_count=rejected,
            error_count=error,
            watch_only_count=watch,
            results=results,
            rankings=rankings,
            portfolio_decision=portfolio_decision,
            paper_result_summary=paper_summary,
            issues=issues,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            elapsed_seconds=time.time() - start_time
        )

        self._save_and_send_report(request, report)
        self._log_research_events(report)

        return report

    def _scan_all_symbols(self, symbols: List[str], request: ScanRequest) -> tuple[List[SymbolScanResult], List[SymbolScanIssue]]:
        results = []
        issues = []
        timeframe = Timeframe(request.timeframe)
        allow_network = request.source not in {"local", "local_file"}
        batch_data = {}
        try:
            batch_data = self.data_service.get_many_ohlcv(
                symbols=symbols,
                timeframe=timeframe,
                refresh=False,
                save=False,
                allow_provider_fallback=allow_network
            )
        except Exception as e:
            self.logger.warning(f"Batch fetch failed, falling back to sequential: {e}")

        for sym in symbols:
            pre_fetched = None
            if isinstance(batch_data, dict) and batch_data:
                pre_fetched = batch_data.get(sym)
                if pre_fetched is None:
                    from bist_signal_bot.data.models import MarketDataFrame, DataVendor
                    import datetime as dt_mod
                    source_val = request.source.upper() if request.source.upper() in [v.value for v in DataVendor] else DataVendor.UNKNOWN
                    pre_fetched = MarketDataFrame(symbol=sym, timeframe=timeframe, source=source_val, data=None, fetched_at=dt_mod.datetime.utcnow())
            elif isinstance(batch_data, dict) and len(batch_data) == 0:
                from bist_signal_bot.data.models import MarketDataFrame, DataVendor
                import datetime as dt_mod
                source_val = request.source.upper() if request.source.upper() in [v.value for v in DataVendor] else DataVendor.UNKNOWN
                pre_fetched = MarketDataFrame(symbol=sym, timeframe=timeframe, source=source_val, data=None, fetched_at=dt_mod.datetime.utcnow())

            res = self.scan_symbol(sym, request, pre_fetched_data=pre_fetched)
            results.append(res)
            issues.extend(res.issues)

            if res.status == ScanCandidateStatus.ERROR and not request.continue_on_error:
                raise ScannerExecutionError(f"Failed to scan {sym}: {res.issues[0].message if res.issues else 'Unknown error'}")

        return results, issues

    def _simulate_portfolio_risk(self, results: List[SymbolScanResult], request: ScanRequest, issues: List[SymbolScanIssue]) -> Optional[Any]:
        if not request.use_portfolio_risk or not self.portfolio_risk_engine:
            return None
        from bist_signal_bot.portfolio.models import PortfolioState
        valid_signals = [r.signal for r in results if r.status in [ScanCandidateStatus.PASSED, ScanCandidateStatus.WATCH_ONLY] and r.signal]
        if valid_signals:
            p_state = PortfolioState(equity=100000, cash=100000, account_id="test", status="ACTIVE")
            try:
                portfolio_decision = self.portfolio_risk_engine.evaluate_portfolio_signals(valid_signals, p_state)
                self._apply_portfolio_decisions(results, portfolio_decision)
                return portfolio_decision
            except Exception as e:
                self.logger.error(f"Portfolio risk failed: {e}")
                issues.append(SymbolScanIssue(stage="PORTFOLIO", message=str(e)))
        return None

    def _rank_results(self, results: List[SymbolScanResult], request: ScanRequest) -> List[ScanRankingItem]:
        rankings = self.ranker.rank(results, sort_key=request.sort_key, descending=request.descending, top_n=request.top_n)
        if request.top_n and request.top_n > 0:
            rankings = rankings[:request.top_n]
        return rankings

    def _count_statuses(self, results: List[SymbolScanResult]) -> tuple[int, int, int, int, int, ScanStatus]:
        passed = filtered = rejected = error = watch = 0
        for r in results:
            if r.status == ScanCandidateStatus.PASSED:
                passed += 1
            elif r.status == ScanCandidateStatus.FILTERED:
                filtered += 1
            elif r.status == ScanCandidateStatus.REJECTED:
                rejected += 1
            elif r.status == ScanCandidateStatus.ERROR:
                error += 1
            elif r.status == ScanCandidateStatus.WATCH_ONLY:
                watch += 1

        status = ScanStatus.SUCCESS
        if error > 0:
            status = ScanStatus.PARTIAL_SUCCESS if passed > 0 else ScanStatus.FAILED
        if passed == 0 and watch == 0 and error == 0:
            status = ScanStatus.EMPTY

        return passed, filtered, rejected, error, watch, status

    def _simulate_paper_execution(self, request: ScanRequest, issues: List[SymbolScanIssue]) -> Optional[dict[str, Any]]:
        if not request.use_paper:
            return None
        if not self.settings.SCANNER_ALLOW_PAPER_EXECUTION:
            issues.append(SymbolScanIssue(stage="PAPER", message="paper execution disabled by scanner config", severity="WARNING"))
            return None
        if self.paper_engine:
             return {"status": "simulated", "message": "Paper run simulation placeholder"}
        return None

    def _save_and_send_report(self, request: ScanRequest, report: ScanReport) -> None:
        if request.save_report:
            from bist_signal_bot.scanner.storage import ScanReportStore
            store = ScanReportStore(self.settings)
            formats = [f.strip() for f in self.settings.SCANNER_REPORT_FORMATS.split(",")]
            output_files = store.save_report(report, formats=formats)
            report.output_files = {k: str(v) for k, v in output_files.items()}

        if request.send_telegram and self.notifier:
            try:
                from bist_signal_bot.notifications.formatter import format_scan_report
                msg = format_scan_report(report)
                self.notifier.send_message(msg)
            except Exception as e:
                self.logger.error(f"Telegram failed: {e}")

    def _log_research_events(self, report: ScanReport) -> None:
        if self.settings.ENABLE_RESEARCH_LEDGER and self.settings.RESEARCH_AUTO_LOG_SCAN:
            try:
                from ..app.research_app import create_research_event_builder, create_research_ledger, create_signal_journal
                ledger = create_research_ledger(self.settings)
                builder = create_research_event_builder(self.settings)
                run_obj = builder.from_scan_report(report)
                ledger.append_run(run_obj)

                if self.settings.RESEARCH_SIGNAL_JOURNAL_ENABLED:
                    journal = create_signal_journal(self.settings)
                    journal.from_scan_report(report)
            except Exception as e:
                self.logger.warning(f"Failed to log scan to research ledger/journal: {e}")


    def build_default_request(self, strategy_name: str, **kwargs) -> ScanRequest:
        req = ScanRequest(
            strategy_name=strategy_name,
            universe_mode=ScanUniverseMode.SYMBOLS,
            source=kwargs.get("source", self.settings.SCANNER_DEFAULT_SOURCE),
            timeframe=kwargs.get("timeframe", self.settings.SCANNER_DEFAULT_TIMEFRAME),
            top_n=kwargs.get("top_n", self.settings.SCANNER_DEFAULT_TOP_N),
            use_trade_risk=kwargs.get("use_trade_risk", self.settings.SCANNER_USE_TRADE_RISK),
            use_portfolio_risk=kwargs.get("use_portfolio_risk", self.settings.SCANNER_USE_PORTFOLIO_RISK),
            continue_on_error=kwargs.get("continue_on_error", self.settings.SCANNER_CONTINUE_ON_ERROR),
            save_report=kwargs.get("save_report", self.settings.SCANNER_SAVE_REPORT),
            send_telegram=kwargs.get("send_telegram", self.settings.SCANNER_SEND_TELEGRAM),
            sort_key=kwargs.get("sort_key", ScanSortKey[self.settings.SCANNER_SORT_KEY]),
            min_signal_score=kwargs.get("min_signal_score", self.settings.SCANNER_MIN_SIGNAL_SCORE),
            min_confidence=kwargs.get("min_confidence", self.settings.SCANNER_MIN_CONFIDENCE),
            min_final_score=kwargs.get("min_final_score", self.settings.SCANNER_MIN_FINAL_SCORE)
        )
        if "symbols" in kwargs: req.symbols = kwargs["symbols"]
        if "watchlist_name" in kwargs:
            req.watchlist_name = kwargs["watchlist_name"]
            req.universe_mode = ScanUniverseMode.WATCHLIST
        if "group_name" in kwargs:
            req.group_name = kwargs["group_name"]
            req.universe_mode = ScanUniverseMode.GROUP
        if "all" in kwargs and kwargs["all"]:
            req.universe_mode = ScanUniverseMode.ALL
        if "params" in kwargs: req.params = kwargs["params"]
        return req

    def scan_symbols(self, symbols: List[str], strategy_name: str, **kwargs) -> ScanReport:
        req = self.build_default_request(strategy_name, symbols=symbols, **kwargs)
        req.universe_mode = ScanUniverseMode.SYMBOLS
        return self.scan(req)

    def scan_watchlist(self, watchlist_name: str, strategy_name: str, **kwargs) -> ScanReport:
        req = self.build_default_request(strategy_name, watchlist_name=watchlist_name, **kwargs)
        return self.scan(req)

    def scan_group(self, group_name: str, strategy_name: str, **kwargs) -> ScanReport:
        req = self.build_default_request(strategy_name, group_name=group_name, **kwargs)
        return self.scan(req)

    def scan_all(self, strategy_name: str, **kwargs) -> ScanReport:
        req = self.build_default_request(strategy_name, all=True, **kwargs)
        return self.scan(req)

    def add_valuation_context(self, result: SymbolScanResult) -> None:
        if not getattr(self.settings, "SCANNER_INCLUDE_VALUATION_CONTEXT", True):
            return

        try:
            from bist_signal_bot.app.valuation_app import create_valuation_store
            store = create_valuation_store()
            risk = store.load_latest_risk(result.symbol)
            if risk:
                setattr(result, "valuation_score", risk.valuation_score)
                setattr(result, "valuation_risk_level", risk.valuation_risk_level.value)
                setattr(result, "valuation_status", "FAIR") # Mock
        except Exception:
            pass
