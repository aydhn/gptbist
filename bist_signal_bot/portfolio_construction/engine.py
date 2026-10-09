import logging
import uuid
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.models import (
    PortfolioConstructionRequest, PortfolioConstructionResult, PortfolioConstructionStatus,
    PortfolioWeightingMethod, PortfolioPositionResearch, PortfolioCandidate
)
from bist_signal_bot.portfolio_construction.candidates import PortfolioCandidateBuilder
from bist_signal_bot.portfolio_construction.correlation import CorrelationAnalyzer
from bist_signal_bot.portfolio_construction.risk_budget import RiskBudgetCalculator
from bist_signal_bot.portfolio_construction.constraints import PortfolioConstraintEngine
from bist_signal_bot.portfolio_construction.weighting import PortfolioWeightingEngine
from bist_signal_bot.portfolio_construction.rebalance import RebalanceSimulator
from bist_signal_bot.portfolio_construction.diversification import DiversificationScorer
from bist_signal_bot.portfolio_construction.scoring import PortfolioConstructionScorer
from bist_signal_bot.portfolio_construction.storage import PortfolioConstructionStore

logger = logging.getLogger(__name__)

class PortfolioConstructionEngine:
    def __init__(self,
                 candidate_builder: Optional[PortfolioCandidateBuilder] = None,
                 correlation_analyzer: Optional[CorrelationAnalyzer] = None,
                 risk_budget_calculator: Optional[RiskBudgetCalculator] = None,
                 constraint_engine: Optional[PortfolioConstraintEngine] = None,
                 weighting_engine: Optional[PortfolioWeightingEngine] = None,
                 rebalance_simulator: Optional[RebalanceSimulator] = None,
                 diversification_scorer: Optional[DiversificationScorer] = None,
                 portfolio_scorer: Optional[PortfolioConstructionScorer] = None,
                 store: Optional[PortfolioConstructionStore] = None,
                 settings: Optional[Settings] = None):
        # All collaborators are optional; defaults are built from settings (research-only, no orders).
        self.settings = settings or Settings()
        s = self.settings
        self.candidate_builder = candidate_builder or PortfolioCandidateBuilder(settings=s)
        self.correlation_analyzer = correlation_analyzer or CorrelationAnalyzer()
        self.risk_budget_calculator = risk_budget_calculator or RiskBudgetCalculator()
        self.constraint_engine = constraint_engine or PortfolioConstraintEngine(settings=s)
        self.weighting_engine = weighting_engine or PortfolioWeightingEngine(settings=s)
        self.rebalance_simulator = rebalance_simulator or RebalanceSimulator(settings=s)
        self.diversification_scorer = diversification_scorer or DiversificationScorer(settings=s)
        self.portfolio_scorer = portfolio_scorer or PortfolioConstructionScorer(settings=s)
        self.store = store or PortfolioConstructionStore(settings=s)
        self.logger = logger

    def construct(self, request: PortfolioConstructionRequest, returns_df: Optional[pd.DataFrame] = None) -> PortfolioConstructionResult:
        if returns_df is None:
            returns_df = pd.DataFrame()

        self.logger.info(f"Starting portfolio construction for request {request.request_id}")

        candidates = self.candidate_builder.build_candidates(request)
        candidates = self.apply_valuation_filter(candidates)
        event_warnings = self.apply_event_risk(candidates)
        weights = self.weighting_engine.build_weights(candidates, request, returns_df)
        positions = self.build_positions(weights, candidates, request.portfolio_notional)

        corr = self.correlation_analyzer.correlation_matrix(returns_df)
        clusters = self.correlation_analyzer.build_clusters(corr, weights, self.settings.PORTFOLIO_HIGH_CORRELATION_THRESHOLD)

        risk_budget = []
        if self.settings.PORTFOLIO_RISK_BUDGET_ENABLED:
            risk_budget = self.risk_budget_calculator.calculate_risk_budget(weights, returns_df)

        violations = []
        if request.apply_constraints:
            violations = self.constraint_engine.evaluate_constraints(positions, clusters, risk_budget)

        div_score = self.diversification_scorer.score_diversification(positions, clusters)

        sim = self.rebalance_simulator.simulate(request.current_weights, weights, request.portfolio_notional, positions)

        result = PortfolioConstructionResult(
            result_id=f"pcr_{uuid.uuid4().hex[:8]}",
            request=request,
            status=PortfolioConstructionStatus.UNKNOWN,
            weighting_method=request.weighting_method,
            candidates=candidates,
            positions=positions,
            constraints=self.constraint_engine.default_constraints(),
            violations=violations,
            correlation_clusters=clusters,
            risk_budget=risk_budget,
            diversification_score=div_score,
            estimated_turnover_pct=sim.estimated_turnover_pct,
            estimated_total_cost_bps=sim.estimated_cost_bps,
            warnings=list(event_warnings)
        )

        portfolio_score = self.portfolio_scorer.score_portfolio(result)
        result.portfolio_score = portfolio_score
        result.status = self.portfolio_scorer.derive_status(portfolio_score, violations, event_warnings)
        result.recommended_actions = self.recommended_actions(result)

        if request.save_output:
            result.output_files = self.store.save_result(result)
            self.store.append_rebalance(sim)

        try:
            from bist_signal_bot.core.audit import AuditEvent, EventType, AuditLogger
            AuditLogger.log(AuditEvent(
                event_type=EventType.PORTFOLIO_CONSTRUCTION_COMPLETED,
                timestamp=datetime.utcnow(),
                metadata={
                    "result_id": result.result_id,
                    "weighting_method": result.weighting_method.value,
                    "candidate_count": len(candidates),
                    "position_count": len(positions),
                    "violation_count": len(violations),
                    "diversification_score": div_score,
                    "portfolio_score": portfolio_score,
                    "no_real_order_sent": True
                }
            ))
        except Exception:
            pass

        return result

    def apply_event_risk(self, candidates: List[PortfolioCandidate]) -> List[str]:
        warnings: List[str] = []
        issues: List[str] = []
        if getattr(self.settings, "ENABLE_EVENT_CALENDAR", False) and getattr(self.settings, "PORTFOLIO_EVENT_RISK_PENALTY_ENABLED", True):
            try:
                from bist_signal_bot.app.events_app import create_event_risk_engine
                engine = create_event_risk_engine(self.settings)
                symbols = [c.symbol for c in candidates]
                assessments = engine.assess_portfolio(symbols)

                event_counts = {}
                for c in candidates:
                    ass = assessments.get(c.symbol)
                    if ass and ass.matching_windows:
                        # Dummy attribute assignment since we don't have the real object
                        if hasattr(c, 'score') and c.score is not None:
                            c.score += getattr(self.settings, "EVENT_CONFIDENCE_ADJUSTMENT_WARN", -5.0)
                        if hasattr(c, 'warnings'):
                            c.warnings.append(f"Event Risk: {ass.decision.value}")

                        for ev in ass.matching_events:
                            event_counts[ev.event_type.value] = event_counts.get(ev.event_type.value, 0) + 1

                for k, v in event_counts.items():
                    if v >= getattr(self.settings, "PORTFOLIO_EVENT_CONCENTRATION_WARN_COUNT", 3):
                        warnings.append(f"Event Concentration Warning: {v} symbols exposed to {k}")
            except Exception as e:
                issues.append(str(e))
        for i in issues:
            self.logger.warning(f"Event risk integration failed: {i}")
        return warnings

    def compare_methods(self, request: PortfolioConstructionRequest, methods: List[PortfolioWeightingMethod], returns_df: Optional[pd.DataFrame] = None) -> List[PortfolioConstructionResult]:
        results = []
        for method in methods:
            req = request.model_copy()
            req.weighting_method = method
            req.request_id = f"req_{uuid.uuid4().hex[:8]}"
            results.append(self.construct(req, returns_df))
        return results

    def build_positions(self, weights: Dict[str, float], candidates: List[PortfolioCandidate], portfolio_notional: float) -> List[PortfolioPositionResearch]:
        cand_map = {c.symbol: c for c in candidates}
        positions = []
        for sym, w in weights.items():
            if w > 0:
                c = cand_map.get(sym)
                positions.append(PortfolioPositionResearch(
                    position_id=f"pos_{uuid.uuid4().hex[:8]}",
                    symbol=sym,
                    sector=c.sector if c else None,
                    current_weight=0.0,
                    target_weight=w,
                    weight_delta=w,
                    estimated_notional=w * portfolio_notional,
                    candidate_score=c.final_candidate_score if c else None
                ))
        return positions

    def recommended_actions(self, result: PortfolioConstructionResult) -> List[str]:
        actions = []
        if result.violations:
            actions.append("REVIEW_CONSTRAINTS")
        if (result.diversification_score or 0) < self.settings.PORTFOLIO_MIN_DIVERSIFICATION_SCORE:
            actions.append("REDUCE_CONCENTRATION")
        if (result.estimated_turnover_pct or 0) > self.settings.PORTFOLIO_MAX_TURNOVER_PCT:
            actions.append("LOWER_TURNOVER")
        if not actions:
            actions.append("NO_ACTION")
        return actions

    def apply_valuation_filter(self, candidates: List[PortfolioCandidate]) -> List[PortfolioCandidate]:
        if not getattr(self.settings, "PORTFOLIO_USE_VALUATION_SCORE", True):
            return candidates

        try:
            from bist_signal_bot.app.valuation_app import create_valuation_store
            store = create_valuation_store(self.settings)

            for c in candidates:
                risk = store.load_latest_risk(c.symbol)
                if risk:
                    if risk.valuation_risk_level.value == "EXTREME":
                        c.final_candidate_score = c.final_candidate_score * 0.5 # Penalty
                    elif risk.valuation_risk_level.value == "HIGH" and risk.valuation_score is not None and risk.valuation_score <= 25.0:
                        if not hasattr(c, "warnings"):
                            c.warnings = []
                        c.warnings.append("Value Trap Warning")
        except Exception as e:
            logger.warning(f"Failed to apply valuation filter: {e}")

        return candidates
