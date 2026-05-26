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
                 candidate_builder: PortfolioCandidateBuilder,
                 correlation_analyzer: CorrelationAnalyzer,
                 risk_budget_calculator: RiskBudgetCalculator,
                 constraint_engine: PortfolioConstraintEngine,
                 weighting_engine: PortfolioWeightingEngine,
                 rebalance_simulator: RebalanceSimulator,
                 diversification_scorer: DiversificationScorer,
                 portfolio_scorer: PortfolioConstructionScorer,
                 store: PortfolioConstructionStore,
                 settings: Settings):
        self.candidate_builder = candidate_builder
        self.correlation_analyzer = correlation_analyzer
        self.risk_budget_calculator = risk_budget_calculator
        self.constraint_engine = constraint_engine
        self.weighting_engine = weighting_engine
        self.rebalance_simulator = rebalance_simulator
        self.diversification_scorer = diversification_scorer
        self.portfolio_scorer = portfolio_scorer
        self.store = store
        self.settings = settings
        self.logger = logger

    def construct(self, request: PortfolioConstructionRequest, returns_df: Optional[pd.DataFrame] = None) -> PortfolioConstructionResult:
        if returns_df is None:
            returns_df = pd.DataFrame()

        self.logger.info(f"Starting portfolio construction for request {request.request_id}")

        candidates = self.candidate_builder.build_candidates(request)
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
            estimated_total_cost_bps=sim.estimated_cost_bps
        )

        portfolio_score = self.portfolio_scorer.score_portfolio(result)
        result.portfolio_score = portfolio_score
        result.status = self.portfolio_scorer.derive_status(portfolio_score, violations, [])
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
