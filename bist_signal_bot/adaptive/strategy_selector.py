from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveStrategyCandidate,
    AdaptiveEvidence,
    AdaptiveParameterSet,
    AdaptiveDecisionStatus,
    AdaptiveConfidenceLevel
)
from bist_signal_bot.adaptive.scoring import AdaptiveScorer

class AdaptiveStrategySelector:
    def __init__(self, scorer: AdaptiveScorer | None = None, settings: Settings | None = None):
        self.scorer = scorer or AdaptiveScorer()
        self.settings = settings

    def build_candidates(self, symbols: list[str], strategies: list[str], evidence_items: list[AdaptiveEvidence], parameter_sets: list[AdaptiveParameterSet] | None = None) -> list[AdaptiveStrategyCandidate]:
        candidates = []
        param_lookup = {}
        if parameter_sets:
            for p in parameter_sets:
                key = f"{p.strategy_name}:{p.symbol or 'ALL'}"
                param_lookup[key] = p.params

        for symbol in symbols:
            for strategy in strategies:
                pair_evidence = [
                    e for e in evidence_items
                    if (e.symbol == symbol or e.symbol is None) and
                       (e.strategy_name == strategy or e.strategy_name is None)
                ]

                params = {}
                key_specific = f"{strategy}:{symbol}"
                key_general = f"{strategy}:ALL"

                if key_specific in param_lookup:
                    params = param_lookup[key_specific]
                elif key_general in param_lookup:
                    params = param_lookup[key_general]
                else:
                    opt_ev = [e for e in pair_evidence if e.evidence_type.value == "OPTIMIZATION"]
                    if opt_ev and opt_ev[0].params:
                        params = opt_ev[0].params

                candidate = AdaptiveStrategyCandidate(
                    symbol=symbol,
                    strategy_name=strategy,
                    params=params,
                    evidence_items=pair_evidence
                )
                candidates.append(candidate)
        return candidates

    def select_top_candidates(self, candidates: list[AdaptiveStrategyCandidate], top_n: int, policy: AdaptivePolicy) -> list[AdaptiveStrategyCandidate]:
        scored = [self.scorer.score_candidate(c, policy) for c in candidates]

        def sort_key(c: AdaptiveStrategyCandidate):
            status_order = {
                AdaptiveDecisionStatus.APPROVED_RESEARCH: 0,
                AdaptiveDecisionStatus.NEEDS_REFRESH: 1,
                AdaptiveDecisionStatus.WATCH_ONLY: 2,
                AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE: 3,
                AdaptiveDecisionStatus.REJECTED: 4,
                AdaptiveDecisionStatus.SKIPPED: 5,
                AdaptiveDecisionStatus.ERROR: 6,
                AdaptiveDecisionStatus.NEEDS_RETRAIN: 7
            }
            s_val = status_order.get(c.status, 99)

            conf_order = {
                AdaptiveConfidenceLevel.HIGH: 0,
                AdaptiveConfidenceLevel.MEDIUM: 1,
                AdaptiveConfidenceLevel.LOW: 2,
                AdaptiveConfidenceLevel.UNKNOWN: 3
            }
            c_val = conf_order.get(c.confidence, 99)
            score_val = -c.composite_score
            return (s_val, c_val, score_val, c.symbol, c.strategy_name)

        scored.sort(key=sort_key)

        approved = [c for c in scored if c.status == AdaptiveDecisionStatus.APPROVED_RESEARCH]
        if len(approved) >= top_n:
            return approved[:top_n]
        return scored[:top_n]

    def recommend_strategy_for_symbol(self, symbol: str, strategies: list[str], evidence_items: list[AdaptiveEvidence], policy: AdaptivePolicy) -> AdaptiveStrategyCandidate | None:
        candidates = self.build_candidates([symbol], strategies, evidence_items)
        scored = [self.scorer.score_candidate(c, policy) for c in candidates]

        approved = [c for c in scored if c.status == AdaptiveDecisionStatus.APPROVED_RESEARCH]
        if approved:
            return max(approved, key=lambda c: c.composite_score)
        if scored:
            return max(scored, key=lambda c: c.composite_score)
        return None

    def strategy_regime_match(self, strategy_name: str, regime_tags: list[str]) -> float:
        if not regime_tags:
            return 50.0
        strategy_lower = strategy_name.lower()
        if "trend" in strategy_lower and any("bull" in t.lower() for t in regime_tags):
            return 90.0
        if "mean_reversion" in strategy_lower and any("chop" in t.lower() or "range" in t.lower() for t in regime_tags):
            return 90.0
        if "breakout" in strategy_lower and any("volatile" in t.lower() for t in regime_tags):
            return 80.0
        return 50.0
