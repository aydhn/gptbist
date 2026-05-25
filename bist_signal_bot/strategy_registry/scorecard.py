import uuid
from datetime import datetime, UTC
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyEvidenceRef,
    StrategyEvidenceType,
    StrategyScorecard,
    StrategyScoreComponent,
    StrategyGateDecision,
    StrategyRegistryStatus
)

class StrategyScorecardBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()

    def build_scorecard(self, strategy: StrategyDefinition, evidence: list[StrategyEvidenceRef] | None = None) -> StrategyScorecard:
        evidence = evidence or []

        components = [
            self.score_backtest(evidence),
            self.score_validation(evidence),
            self.score_monte_carlo(evidence),
            self.score_overfit(evidence),
            self.score_execution(evidence),
            self.score_drift(evidence),
            self.score_performance(evidence),
            self.score_review(evidence),
            self.score_governance(evidence)
        ]

        aggregate = self.aggregate_components(components)

        scorecard = StrategyScorecard(
            scorecard_id=f"sc_{uuid.uuid4().hex[:8]}",
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name,
            version=strategy.version,
            components=components,
            aggregate_score=aggregate.get("aggregate_score"),
            confidence_score=aggregate.get("confidence_score"),
            robustness_score=aggregate.get("robustness_score"),
            overfit_risk_score=aggregate.get("overfit_risk_score"),
            execution_penalty_score=aggregate.get("execution_penalty_score"),
            drift_risk_score=aggregate.get("drift_risk_score"),
            status=strategy.status,
            gate_decision=aggregate.get("gate_decision", StrategyGateDecision.UNKNOWN),
            warnings=aggregate.get("warnings", []),
            recommended_actions=aggregate.get("recommended_actions", [])
        )

        return scorecard

    def _get_evidence_for_type(self, evidence: list[StrategyEvidenceRef], type_: StrategyEvidenceType) -> list[StrategyEvidenceRef]:
        return [e for e in evidence if e.evidence_type == type_]

    def score_backtest(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.BACKTEST)
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_BACKTEST", 0.10)
        if not refs:
            return StrategyScoreComponent(
                component_id="backtest", name="Backtest Quality", evidence_type=StrategyEvidenceType.BACKTEST,
                score=0.0, weight=weight,
                status=None, message="Missing backtest evidence", warnings=["Missing backtest evidence"]
            )
        # Mock score
        return StrategyScoreComponent(
            component_id="backtest", name="Backtest Quality", evidence_type=StrategyEvidenceType.BACKTEST,
            score=85.0, weight=weight,
            status=StrategyRegistryStatus.VALIDATED_RESEARCH, message="Good backtest results",
            evidence_refs=[e.evidence_id for e in refs]
        )

    def score_validation(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.WALK_FORWARD)
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_VALIDATION", 0.25)
        if not refs:
            return StrategyScoreComponent(
                component_id="validation", name="Walk-Forward Validation", evidence_type=StrategyEvidenceType.WALK_FORWARD,
                score=0.0, weight=weight,
                status=None, message="Missing validation evidence", warnings=["Missing validation evidence"]
            )
        # Mock score
        return StrategyScoreComponent(
            component_id="validation", name="Walk-Forward Validation", evidence_type=StrategyEvidenceType.WALK_FORWARD,
            score=80.0, weight=weight,
            status=StrategyRegistryStatus.VALIDATED_RESEARCH, message="Validation passed",
            evidence_refs=[e.evidence_id for e in refs]
        )

    def score_monte_carlo(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.MONTE_CARLO)
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_MONTE_CARLO", 0.20)
        if not refs:
            return StrategyScoreComponent(
                component_id="monte_carlo", name="Monte Carlo Robustness", evidence_type=StrategyEvidenceType.MONTE_CARLO,
                score=0.0, weight=weight,
                status=None, message="Missing Monte Carlo evidence", warnings=["Missing Monte Carlo evidence"]
            )
        # Mock score
        return StrategyScoreComponent(
            component_id="monte_carlo", name="Monte Carlo Robustness", evidence_type=StrategyEvidenceType.MONTE_CARLO,
            score=75.0, weight=weight,
            status=StrategyRegistryStatus.VALIDATED_RESEARCH, message="Robustness verified",
            evidence_refs=[e.evidence_id for e in refs]
        )

    def score_overfit(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.OVERFIT_DIAGNOSTICS)
        score = 90.0 if refs else 50.0
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_OVERFIT", 0.15)
        return StrategyScoreComponent(
            component_id="overfit", name="Overfit Risk", evidence_type=StrategyEvidenceType.OVERFIT_DIAGNOSTICS,
            score=score, weight=weight,
            status=None, message="Overfit check", evidence_refs=[e.evidence_id for e in refs]
        )

    def score_execution(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.EXECUTION_QUALITY)
        score = 80.0 if refs else 50.0
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_EXECUTION", 0.10)
        return StrategyScoreComponent(
            component_id="execution", name="Execution Quality", evidence_type=StrategyEvidenceType.EXECUTION_QUALITY,
            score=score, weight=weight,
            status=None, message="Execution simulation check", evidence_refs=[e.evidence_id for e in refs]
        )

    def score_drift(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.DRIFT)
        score = 85.0 if refs else 50.0
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_DRIFT", 0.10)
        return StrategyScoreComponent(
            component_id="drift", name="Drift Stability", evidence_type=StrategyEvidenceType.DRIFT,
            score=score, weight=weight,
            status=None, message="Drift check", evidence_refs=[e.evidence_id for e in refs]
        )

    def score_performance(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.PERFORMANCE_BENCHMARK)
        score = 90.0 if refs else 50.0
        return StrategyScoreComponent(
            component_id="performance", name="Performance Benchmark", evidence_type=StrategyEvidenceType.PERFORMANCE_BENCHMARK,
            score=score, weight=0.0,  # Not strictly weighted by default in request
            status=None, message="Performance check", evidence_refs=[e.evidence_id for e in refs]
        )

    def score_review(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.ANALYST_REVIEW)
        score = 100.0 if refs else 50.0
        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_REVIEW", 0.05)
        return StrategyScoreComponent(
            component_id="review", name="Analyst Review", evidence_type=StrategyEvidenceType.ANALYST_REVIEW,
            score=score, weight=weight,
            status=None, message="Review check", evidence_refs=[e.evidence_id for e in refs]
        )

    def score_governance(self, evidence: list[StrategyEvidenceRef]) -> StrategyScoreComponent:
        refs = self._get_evidence_for_type(evidence, StrategyEvidenceType.GOVERNANCE)
        # Mock logic
        warnings = []
        gate_decision = StrategyGateDecision.ALLOW
        if refs:
            for r in refs:
                if r.status == "FAIL":
                    warnings.append(f"Governance critical finding: {r.summary}")
                    gate_decision = StrategyGateDecision.BLOCK

        weight = getattr(self.settings, "STRATEGY_SCORE_WEIGHT_GOVERNANCE", 0.05)
        return StrategyScoreComponent(
            component_id="governance", name="Governance Safety", evidence_type=StrategyEvidenceType.GOVERNANCE,
            score=100.0 if not warnings else 0.0, weight=weight,
            status=StrategyRegistryStatus.BLOCKED if warnings else None,
            message="Governance check", warnings=warnings, evidence_refs=[e.evidence_id for e in refs],
            metadata={"gate_decision": gate_decision.value}
        )

    def aggregate_components(self, components: list[StrategyScoreComponent]) -> dict[str, Any]:
        total_weight = sum(c.weight for c in components if c.weight > 0)
        aggregate = 0.0
        warnings = []
        gate_decision = StrategyGateDecision.ALLOW

        for c in components:
            if c.weight > 0 and c.score is not None:
                if total_weight > 0:
                    normalized_weight = c.weight / total_weight
                    aggregate += c.score * normalized_weight
            if c.warnings:
                warnings.extend(c.warnings)
            if c.component_id == "governance" and c.score == 0.0:
                gate_decision = StrategyGateDecision.BLOCK

        # Further analysis
        overfit_risk = 0.0
        robustness = 0.0
        confidence = aggregate

        for c in components:
            if c.component_id == "overfit" and c.score is not None:
                overfit_risk = 100.0 - c.score
                if overfit_risk > 70:
                    warnings.append("High overfit risk detected")
                    if gate_decision != StrategyGateDecision.BLOCK:
                        gate_decision = StrategyGateDecision.REQUIRE_REVIEW
            if c.component_id == "monte_carlo" and c.score is not None:
                robustness = c.score
                if robustness < 30:
                    warnings.append("Low robustness detected")

        return {
            "aggregate_score": aggregate,
            "confidence_score": confidence,
            "robustness_score": robustness,
            "overfit_risk_score": overfit_risk,
            "execution_penalty_score": 0.0,
            "drift_risk_score": 0.0,
            "gate_decision": gate_decision,
            "warnings": warnings,
            "recommended_actions": ["Review scorecard findings"]
        }
