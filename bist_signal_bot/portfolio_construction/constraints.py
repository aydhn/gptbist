from typing import List, Optional, Dict, Any
import uuid

from bist_signal_bot.portfolio_construction.models import (
    PortfolioConstraint, PortfolioPositionResearch, CorrelationCluster,
    RiskBudgetItem, PortfolioConstraintViolation, ConstraintType, ConstraintSeverity
)
from bist_signal_bot.config.settings import Settings

class PortfolioConstraintEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def default_constraints(self) -> List[PortfolioConstraint]:
        return [
            PortfolioConstraint(
                constraint_id=f"c_{uuid.uuid4().hex[:8]}",
                constraint_type=ConstraintType.MAX_SYMBOL_WEIGHT,
                name="Max Symbol Weight",
                limit_value=self.settings.PORTFOLIO_MAX_SYMBOL_WEIGHT,
                severity=ConstraintSeverity.HIGH
            ),
            PortfolioConstraint(
                constraint_id=f"c_{uuid.uuid4().hex[:8]}",
                constraint_type=ConstraintType.MAX_SECTOR_WEIGHT,
                name="Max Sector Weight",
                limit_value=self.settings.PORTFOLIO_MAX_SECTOR_WEIGHT,
                severity=ConstraintSeverity.MEDIUM
            ),
            PortfolioConstraint(
                constraint_id=f"c_{uuid.uuid4().hex[:8]}",
                constraint_type=ConstraintType.MAX_CORRELATION_CLUSTER_WEIGHT,
                name="Max Correlation Cluster Weight",
                limit_value=self.settings.PORTFOLIO_MAX_CORRELATION_CLUSTER_WEIGHT,
                severity=ConstraintSeverity.MEDIUM
            )
        ]

    def evaluate_constraints(self, positions: List[PortfolioPositionResearch],
                           clusters: Optional[List[CorrelationCluster]] = None,
                           risk_budget: Optional[List[RiskBudgetItem]] = None) -> List[PortfolioConstraintViolation]:
        violations = []
        constraints = self.default_constraints()

        for c in constraints:
            if not c.enabled:
                continue

            if c.constraint_type == ConstraintType.MAX_SYMBOL_WEIGHT:
                violations.extend(self.check_max_symbol_weight(positions, c))
            elif c.constraint_type == ConstraintType.MAX_SECTOR_WEIGHT:
                violations.extend(self.check_max_sector_weight(positions, c))
            elif c.constraint_type == ConstraintType.MAX_CORRELATION_CLUSTER_WEIGHT and clusters:
                violations.extend(self.check_correlation_cluster_weight(clusters, c))

        return violations

    def check_max_symbol_weight(self, positions: List[PortfolioPositionResearch], constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        v = []
        limit = float(constraint.limit_value) if constraint.limit_value else 1.0
        for p in positions:
            if p.target_weight > limit:
                v.append(PortfolioConstraintViolation(
                    violation_id=f"v_{uuid.uuid4().hex[:8]}",
                    constraint_type=constraint.constraint_type,
                    symbol=p.symbol,
                    observed_value=p.target_weight,
                    limit_value=limit,
                    severity=constraint.severity,
                    message=f"Symbol {p.symbol} weight {p.target_weight:.2%} exceeds max limit {limit:.2%}",
                    recommended_action="REDUCE_CONCENTRATION"
                ))
        return v

    def check_max_sector_weight(self, positions: List[PortfolioPositionResearch], constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        v = []
        limit = float(constraint.limit_value) if constraint.limit_value else 1.0
        sectors = {}
        for p in positions:
            if p.sector:
                sectors[p.sector] = sectors.get(p.sector, 0.0) + p.target_weight

        for sector, weight in sectors.items():
            if weight > limit:
                v.append(PortfolioConstraintViolation(
                    violation_id=f"v_{uuid.uuid4().hex[:8]}",
                    constraint_type=constraint.constraint_type,
                    sector=sector,
                    observed_value=weight,
                    limit_value=limit,
                    severity=constraint.severity,
                    message=f"Sector {sector} weight {weight:.2%} exceeds max limit {limit:.2%}",
                    recommended_action="REDUCE_CONCENTRATION"
                ))
        return v

    def check_max_strategy_weight(self, positions: List[PortfolioPositionResearch], constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        return []

    def check_correlation_cluster_weight(self, clusters: List[CorrelationCluster], constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        v = []
        limit = float(constraint.limit_value) if constraint.limit_value else 1.0
        for cluster in clusters:
            if cluster.cluster_weight and cluster.cluster_weight > limit:
                v.append(PortfolioConstraintViolation(
                    violation_id=f"v_{uuid.uuid4().hex[:8]}",
                    constraint_type=constraint.constraint_type,
                    observed_value=cluster.cluster_weight,
                    limit_value=limit,
                    severity=constraint.severity,
                    message=f"Correlation cluster weight {cluster.cluster_weight:.2%} exceeds max limit {limit:.2%}",
                    recommended_action="REDUCE_CONCENTRATION"
                ))
        return v

    def check_liquidity_constraints(self, positions: List[PortfolioPositionResearch], constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        return []

    def check_turnover_constraint(self, turnover: float, constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        return []

    def check_cost_drag_constraint(self, cost_bps: float, constraint: PortfolioConstraint) -> List[PortfolioConstraintViolation]:
        return []

    def severity_from_violation(self, violation: PortfolioConstraintViolation) -> ConstraintSeverity:
        return violation.severity
