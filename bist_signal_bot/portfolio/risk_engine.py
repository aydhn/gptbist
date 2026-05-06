import logging
import pandas as pd
from typing import Optional
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskContext
from bist_signal_bot.risk.engine import RiskEngine
from bist_signal_bot.portfolio.models import (
    PortfolioState, PortfolioRiskDecision, PortfolioDecisionStatus,
    PortfolioRejectReason, AllocationMethod, AllocationRequest, AllocationResultItem,
    AllocationResult
)
from bist_signal_bot.portfolio.correlation import CorrelationAnalyzer
from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.allocation import PortfolioAllocator
from bist_signal_bot.portfolio.holdings import build_portfolio_state

class PortfolioRiskEngine:
    def __init__(
        self,
        trade_risk_engine: Optional[RiskEngine] = None,
        allocator: Optional[PortfolioAllocator] = None,
        exposure_analyzer: Optional[ExposureAnalyzer] = None,
        correlation_analyzer: Optional[CorrelationAnalyzer] = None,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        from bist_signal_bot.config.settings import settings as default_settings
        self.settings = settings or default_settings
        self.logger = logger or logging.getLogger(__name__)

        self.trade_risk_engine = trade_risk_engine or RiskEngine(settings=self.settings, logger=self.logger)
        self.allocator = allocator or PortfolioAllocator(settings=self.settings, logger=self.logger)
        self.exposure_analyzer = exposure_analyzer or ExposureAnalyzer()
        self.correlation_analyzer = correlation_analyzer or CorrelationAnalyzer(settings=self.settings, logger=self.logger)

    def evaluate_portfolio_signals(
        self,
        signals: list[SignalCandidate],
        portfolio_state: PortfolioState,
        data_by_symbol: Optional[dict[str, pd.DataFrame]] = None
    ) -> PortfolioRiskDecision:

        warnings = []
        reject_reasons = []

        # 1. Trade-level evaluate
        trade_decisions = []
        for sig in signals:
            td = self.trade_risk_engine.evaluate_signal(sig, RiskContext(equity=portfolio_state.equity, available_cash=portfolio_state.cash))
            trade_decisions.append(td)

        active_decisions = [d for d in trade_decisions if d.status != RiskDecisionStatus.REJECTED]

        # 2. Correlation
        corr_result = None
        if data_by_symbol and getattr(self.settings, "PORTFOLIO_ENABLE_CORRELATION_CHECK", True):
            corr_result = self.correlation_analyzer.calculate_correlation_matrix(
                data_by_symbol,
                method=getattr(self.settings, "PORTFOLIO_CORRELATION_METHOD", "pearson"),
                lookback_rows=getattr(self.settings, "PORTFOLIO_CORRELATION_LOOKBACK_ROWS", 60)
            )

            existing_symbols = portfolio_state.holding_symbols()
            candidate_symbols = [d.signal.symbol for d in active_decisions]
            threshold = getattr(self.settings, "PORTFOLIO_MAX_PAIRWISE_CORRELATION", 0.80)

            corr_warnings = self.correlation_analyzer.correlation_warnings(
                candidate_symbols, existing_symbols, corr_result, threshold
            )
            warnings.extend(corr_warnings)

            # Action logic
            action = getattr(self.settings, "PORTFOLIO_CORRELATION_LIMIT_ACTION", "REDUCE")
            if corr_warnings and action == "REJECT":
                 # Mock reject
                 for d in active_decisions:
                     if any(d.signal.symbol in w for w in corr_warnings):
                         d.status = RiskDecisionStatus.REJECTED
                         reject_reasons.append(PortfolioRejectReason.MAX_CORRELATION_EXCEEDED)
                 active_decisions = [d for d in active_decisions if d.status != RiskDecisionStatus.REJECTED]

        # 3. Allocation
        alloc_method_str = getattr(self.settings, "PORTFOLIO_ALLOCATION_METHOD", "HYBRID")
        try:
            method = AllocationMethod(alloc_method_str)
        except ValueError:
            method = AllocationMethod.HYBRID

        req = AllocationRequest(
            signals=signals,
            risk_decisions=trade_decisions,
            portfolio_state=portfolio_state,
            method=method,
            total_allocation_pct=getattr(self.settings, "PORTFOLIO_TOTAL_ALLOCATION_PCT", 0.95),
            max_symbol_weight_pct=getattr(self.settings, "PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT", 0.20)
        )

        alloc_result = self.allocator.allocate(req)

        # 4. Exposure
        exp_before = self.exposure_analyzer.calculate_exposure(portfolio_state)
        exp_after = self.exposure_analyzer.simulate_post_allocation_exposure(portfolio_state, alloc_result)

        ok, exp_reasons, exp_issues = self.exposure_analyzer.check_exposure_limits(exp_after, self.settings)
        if not ok:
            warnings.extend(exp_issues)
            reject_reasons.extend(exp_reasons)
            # Simplistic approach: if exposure limits violated, reject everything in this round
            for item in alloc_result.items:
                item.approved = False
                item.allocated_notional = 0.0
                item.quantity = 0.0
                item.reasons.extend(exp_issues)
            alloc_result.rejected_symbols.extend([i.symbol for i in alloc_result.items])
            alloc_result.reduced_symbols.clear()
            alloc_result.total_allocated_notional = 0.0
            alloc_result.total_allocated_pct = 0.0

        status = PortfolioDecisionStatus.APPROVED
        if all(not i.approved for i in alloc_result.items):
            status = PortfolioDecisionStatus.REJECTED
        elif any(not i.approved for i in alloc_result.items):
            status = PortfolioDecisionStatus.PARTIALLY_APPROVED

        approved_cnt = sum(1 for i in alloc_result.items if i.approved)
        rejected_cnt = sum(1 for i in alloc_result.items if not i.approved)
        reduced_cnt = len(alloc_result.reduced_symbols)

        from bist_signal_bot.core.audit import AuditLogger, AuditEventType, AuditEvent
        from bist_signal_bot.config.secrets import sanitize_config_dict
        audit = AuditLogger(settings=self.settings)
        audit.log_event(AuditEvent(
            event_type=AuditEventType.PORTFOLIO_RISK_EVALUATED,
            level="INFO",
            message="Portfolio risk evaluated",
            metadata=sanitize_config_dict({
                "approved": approved_cnt,
                "rejected": rejected_cnt,
                "allocation": alloc_result.total_allocated_pct
            })
        ))

        return PortfolioRiskDecision(
            portfolio_state=portfolio_state,
            input_signals=signals,
            trade_risk_decisions=trade_decisions,
            allocation_result=alloc_result,
            exposure_report_before=exp_before,
            exposure_report_after=exp_after,
            correlation_result=corr_result,
            status=status,
            approved_count=approved_cnt,
            rejected_count=rejected_cnt,
            reduced_count=reduced_cnt,
            reject_reasons=reject_reasons,
            warnings=warnings,
            generated_at=datetime.utcnow(),
            metadata={}
        )

    def evaluate_single_signal_against_portfolio(
        self, signal: SignalCandidate, portfolio_state: PortfolioState, data_by_symbol: Optional[dict[str, pd.DataFrame]] = None
    ) -> PortfolioRiskDecision:
        return self.evaluate_portfolio_signals([signal], portfolio_state, data_by_symbol)

    def build_default_portfolio_state(self, equity: Optional[float] = None, cash: Optional[float] = None) -> PortfolioState:
        eq = equity or getattr(self.settings, "PORTFOLIO_DEFAULT_EQUITY", 100000.0)
        c = cash if cash is not None else getattr(self.settings, "PORTFOLIO_DEFAULT_CASH", eq)
        return build_portfolio_state(equity=eq, cash=c)

    @classmethod
    def from_settings(cls, settings: Settings) -> "PortfolioRiskEngine":
        return cls(settings=settings)
