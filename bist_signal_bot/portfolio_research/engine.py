import uuid
from datetime import datetime
from typing import Any
import pandas as pd
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioSnapshot,
    ResearchPortfolioItem,
    PortfolioResearchRequest,
    RebalancePlan,
    BasketSimulationResult,
    PortfolioResearchMode
)
from bist_signal_bot.portfolio_research.constraints import PortfolioConstraintEngine
from bist_signal_bot.portfolio_research.allocation import ResearchAllocationEngine
from bist_signal_bot.portfolio_research.exposure import PortfolioExposureAnalyzer
from bist_signal_bot.portfolio_research.correlation import PortfolioCorrelationAnalyzer
from bist_signal_bot.portfolio_research.rebalance import RebalancePlanner
from bist_signal_bot.portfolio_research.simulation import BasketSimulator
from bist_signal_bot.portfolio_research.storage import PortfolioResearchStore
from bist_signal_bot.core.audit import AuditLogger, AuditEventType
import logging

class PortfolioResearchEngine:
    def __init__(self,
                 store: PortfolioResearchStore,
                 allocation_engine: ResearchAllocationEngine,
                 constraint_engine: PortfolioConstraintEngine,
                 exposure_analyzer: PortfolioExposureAnalyzer,
                 correlation_analyzer: PortfolioCorrelationAnalyzer,
                 rebalance_planner: RebalancePlanner,
                 basket_simulator: BasketSimulator,
                 data_service: Any = None,
                 signal_store: Any = None,
                 ensemble_store: Any = None,
                 fundamental_engine: Any = None,
                 breadth_engine: Any = None,
                 paper_ledger: Any = None,
                 audit_logger: AuditLogger | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):

        self.store = store
        self.allocation_engine = allocation_engine
        self.constraint_engine = constraint_engine
        self.exposure_analyzer = exposure_analyzer
        self.correlation_analyzer = correlation_analyzer
        self.rebalance_planner = rebalance_planner
        self.basket_simulator = basket_simulator
        self.data_service = data_service
        self.signal_store = signal_store
        self.ensemble_store = ensemble_store
        self.fundamental_engine = fundamental_engine
        self.breadth_engine = breadth_engine
        self.paper_ledger = paper_ledger
        self.audit_logger = audit_logger
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def from_settings(cls, settings: Settings) -> 'PortfolioResearchEngine':
        from bist_signal_bot.storage.paths import get_portfolio_research_dir
        store = PortfolioResearchStore(get_portfolio_research_dir(settings))
        return cls(
            store=store,
            allocation_engine=ResearchAllocationEngine(),
            constraint_engine=PortfolioConstraintEngine(),
            exposure_analyzer=PortfolioExposureAnalyzer(),
            correlation_analyzer=PortfolioCorrelationAnalyzer(),
            rebalance_planner=RebalancePlanner(),
            basket_simulator=BasketSimulator(),
            settings=settings
        )

    def build_snapshot(self, request: PortfolioResearchRequest) -> ResearchPortfolioSnapshot:
        if self.audit_logger:
            self.audit_logger.log(AuditEventType.PORTFOLIO_RESEARCH_BUILD_STARTED, "Started building research portfolio snapshot")

        candidates = []
        if request.symbols:
            for s in request.symbols:
                candidates.append(ResearchPortfolioItem(
                    item_id=str(uuid.uuid4()),
                    symbol=s,
                    proposed_weight=0.0,
                    capped_weight=0.0,
                    final_weight=0.0,
                    state="ACTIVE"
                ))
        else:
            if request.include_active_signals:
                candidates.extend(self.build_candidates_from_signals(request))
            if request.include_watchlist:
                candidates.extend(self.build_candidates_from_watchlist(request))
            if request.include_ensemble:
                candidates.extend(self.build_candidates_from_ensemble(request))

        # Deduplicate
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c.symbol not in seen:
                seen.add(c.symbol)
                unique_candidates.append(c)

        # Limit max items if taking from general scan
        if not request.symbols and len(unique_candidates) > request.max_items:
            # Sort by score if available, else just take first N
            unique_candidates.sort(key=lambda x: (x.score or 0.0), reverse=True)
            unique_candidates = unique_candidates[:request.max_items]

        # Fetch data for volatility/correlation
        data_by_symbol = {}
        volatility_by_symbol = {}
        if self.data_service:
            syms = [c.symbol for c in unique_candidates]
            for sym in syms:
                try:
                    df = self.data_service.fetch_data(sym, request.timeframe, source=request.source)
                    if df is not None and not df.empty:
                        data_by_symbol[sym] = df
                        # simple vol proxy
                        ret = df['close'].pct_change().dropna()
                        volatility_by_symbol[sym] = float(ret.std() * (252**0.5) * 100) if len(ret) > 10 else 0.0
                except Exception as e:
                    self.logger.warning(f"Failed to fetch data for {sym}: {e}")

        # Apply constraints phase 1
        constraints = self.constraint_engine.validate_items(unique_candidates, request)

        # Allocate
        if request.allocation_method == request.allocation_method.VOLATILITY_ADJUSTED:
            self.allocation_engine.volatility_adjusted(unique_candidates, volatility_by_symbol, request.target_gross_exposure)
        else:
            self.allocation_engine.allocate(unique_candidates, request)

        # Apply caps
        self.constraint_engine.apply_weight_caps(unique_candidates, request)

        # Normalize final weights
        self.constraint_engine.normalize_final_weights(unique_candidates, request.target_gross_exposure)

        # Calculate exposures
        exposures = self.exposure_analyzer.calculate_exposures(unique_candidates)
        exposure_warnings = self.exposure_analyzer.exposure_warnings(exposures, request)

        # Calculate correlations
        correlations = self.correlation_analyzer.calculate_correlations(data_by_symbol)
        correlation_warnings = self.correlation_analyzer.high_correlation_warnings(correlations, request.high_correlation_threshold if hasattr(request, 'high_correlation_threshold') else 0.8)

        total_weight = sum(c.final_weight for c in unique_candidates)

        warnings = exposure_warnings + correlation_warnings
        for c in unique_candidates:
            if c.warnings:
                warnings.extend([f"[{c.symbol}] {w}" for w in c.warnings])

        snapshot = ResearchPortfolioSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            mode=request.mode,
            allocation_method=request.allocation_method,
            items=unique_candidates,
            constraints=constraints,
            exposures=exposures,
            correlations=correlations,
            total_weight=total_weight,
            item_count=len(unique_candidates),
            valid_item_count=sum(1 for c in unique_candidates if c.final_weight > 0),
            blocked_item_count=sum(1 for c in unique_candidates if "BLOCKED" in (c.state or "")),
            warnings=warnings
        )

        if request.save_snapshot:
            self.store.save_snapshot(snapshot)
            if self.audit_logger:
                self.audit_logger.log(AuditEventType.PORTFOLIO_RESEARCH_SNAPSHOT_SAVED, f"Saved snapshot {snapshot.snapshot_id}")

        if self.audit_logger:
            self.audit_logger.log(AuditEventType.PORTFOLIO_RESEARCH_BUILD_COMPLETED, "Completed building research portfolio snapshot", metadata={"snapshot_id": snapshot.snapshot_id})

        return snapshot

    def build_candidates_from_signals(self, request: PortfolioResearchRequest) -> list[ResearchPortfolioItem]:
        # Mock logic, integrate real signal_store later
        return []

    def build_candidates_from_watchlist(self, request: PortfolioResearchRequest) -> list[ResearchPortfolioItem]:
        # Mock logic
        return []

    def build_candidates_from_ensemble(self, request: PortfolioResearchRequest) -> list[ResearchPortfolioItem]:
        # Mock logic
        return []

    def rebalance(self, current_snapshot_id: str | None, target_request: PortfolioResearchRequest) -> RebalancePlan:
        current = None
        if current_snapshot_id:
            current = self.store.load_snapshot(current_snapshot_id)

        target = self.build_snapshot(target_request)
        plan = self.rebalance_planner.build_plan(current, target)

        self.store.save_rebalance_plan(plan)
        if self.audit_logger:
            self.audit_logger.log(AuditEventType.PORTFOLIO_RESEARCH_REBALANCE_CREATED, f"Created rebalance plan {plan.plan_id}")

        return plan

    def simulate(self, snapshot_id: str, start_date: datetime, end_date: datetime, initial_value: float = 100000.0) -> BasketSimulationResult:
        snapshot = self.store.load_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        data_by_symbol = {}
        if self.data_service:
            for item in snapshot.items:
                if item.final_weight > 0:
                    try:
                        df = self.data_service.fetch_data(item.symbol, "1D", source="local") # force local for sim
                        if df is not None and not df.empty:
                            data_by_symbol[item.symbol] = df
                    except Exception as e:
                        self.logger.warning(f"Simulation missing data for {item.symbol}: {e}")

        result = self.basket_simulator.simulate(snapshot, data_by_symbol, start_date, end_date, initial_value)
        self.store.save_simulation(result)

        if self.audit_logger:
            self.audit_logger.log(AuditEventType.PORTFOLIO_RESEARCH_SIMULATION_COMPLETED, f"Completed simulation {result.simulation_id}")

        return result

    def latest_snapshot(self) -> ResearchPortfolioSnapshot | None:
        return self.store.load_latest_snapshot()

    def get_telegram_summary(self) -> dict:
        return {"total_snapshots": 0, "latest_status": "OK"}
