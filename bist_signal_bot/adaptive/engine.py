import logging
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveRecommendation,
    AdaptiveDecisionStatus,
    AdaptiveParameterSet,
    AdaptiveMode
)
from bist_signal_bot.adaptive.policy import AdaptivePolicyManager
from bist_signal_bot.adaptive.evidence import AdaptiveEvidenceCollector
from bist_signal_bot.adaptive.parameter_store import AdaptiveParameterStore
from bist_signal_bot.adaptive.scoring import AdaptiveScorer
from bist_signal_bot.adaptive.strategy_selector import AdaptiveStrategySelector
from bist_signal_bot.adaptive.refresh_planner import AdaptiveRefreshPlanner
from bist_signal_bot.adaptive.model_refresh import ModelRefreshPlanner
from bist_signal_bot.adaptive.storage import AdaptiveStore
from bist_signal_bot.core.exceptions import AdaptiveParameterStoreError, AdaptiveError

class AdaptiveEngine:
    def __init__(
        self,
        policy_manager: AdaptivePolicyManager | None = None,
        evidence_collector: AdaptiveEvidenceCollector | None = None,
        parameter_store: AdaptiveParameterStore | None = None,
        selector: AdaptiveStrategySelector | None = None,
        refresh_planner: AdaptiveRefreshPlanner | None = None,
        model_refresh_planner: ModelRefreshPlanner | None = None,
        storage: AdaptiveStore | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None
    ):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

        self.policy_manager = policy_manager or AdaptivePolicyManager(self.settings, self.logger)
        self.evidence_collector = evidence_collector or AdaptiveEvidenceCollector(self.settings, self.logger)
        self.storage = storage or AdaptiveStore(self.settings, logger=self.logger)
        self.parameter_store = parameter_store or AdaptiveParameterStore(self.storage.get_adaptive_dir(), self.settings, self.logger)
        self.selector = selector or AdaptiveStrategySelector(AdaptiveScorer(), self.settings)
        self.refresh_planner = refresh_planner or AdaptiveRefreshPlanner()
        self.model_refresh_planner = model_refresh_planner or ModelRefreshPlanner(self.settings)

    @classmethod
    def from_settings(cls, settings: Settings) -> 'AdaptiveEngine':
        return cls(settings=settings)

    def recommend(
        self,
        symbols: list[str],
        strategies: list[str],
        top_n: int | None = None,
        policy: AdaptivePolicy | None = None,
        save_report: bool = False
    ) -> AdaptiveRecommendation:
        start_time = time.time()
        now = datetime.now(timezone.utc)
        rec_id = f"ar_{uuid.uuid4().hex[:12]}"

        try:
            active_policy = policy or self.policy_manager.load_policy()
            top_n = top_n or self.settings.ADAPTIVE_DEFAULT_TOP_N

            if active_policy.mode == AdaptiveMode.DISABLED:
                return AdaptiveRecommendation(
                    recommendation_id=rec_id,
                    mode=AdaptiveMode.DISABLED,
                    policy=active_policy,
                    status=AdaptiveDecisionStatus.SKIPPED,
                    generated_at=now,
                    disclaimer="Adaptive engine is disabled."
                )

            active_params = self.parameter_store.load_active_parameters()
            evidence_items = self.evidence_collector.collect_all(symbols, strategies)
            candidates = self.selector.build_candidates(symbols, strategies, evidence_items, active_params)
            selected = self.selector.select_top_candidates(candidates, top_n, active_policy)
            refresh_plan = self.refresh_planner.build_refresh_plan(candidates, evidence_items, active_policy)
            model_refresh = self.model_refresh_planner.recommend_model_refresh([], evidence_items, active_policy)

            result = AdaptiveRecommendation(
                recommendation_id=rec_id,
                mode=active_policy.mode,
                candidates=candidates,
                selected_candidates=selected,
                refresh_plan=refresh_plan,
                model_refresh_recommendations=model_refresh,
                policy=active_policy,
                status=AdaptiveDecisionStatus.APPROVED_RESEARCH if selected else AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE,
                generated_at=now,
                elapsed_seconds=time.time() - start_time
            )

            from bist_signal_bot.security.redaction import SecretRedactor
            result.metadata["redacted"] = True
            result.metadata = SecretRedactor.redact_dict(result.metadata)

            if save_report or self.settings.ADAPTIVE_SAVE_REPORTS:
                saved = self.storage.save_recommendation(result)
                result.output_files = {k: str(v) for k, v in saved.items()}

            return result
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return AdaptiveRecommendation(
                recommendation_id=rec_id,
                mode=AdaptiveMode.DISABLED,
                policy=policy or self.policy_manager.build_default_policy(),
                status=AdaptiveDecisionStatus.ERROR,
                generated_at=now,
                elapsed_seconds=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def recommend_for_symbol(self, symbol: str, strategies: list[str], policy: AdaptivePolicy | None = None) -> AdaptiveRecommendation:
        return self.recommend([symbol], strategies, top_n=1, policy=policy, save_report=False)

    def build_runtime_strategy_config(self, symbols: list[str], strategies: list[str], policy: AdaptivePolicy | None = None) -> dict[str, Any]:
        rec = self.recommend(symbols, strategies, policy=policy, save_report=False)
        config_map = {}
        if rec.status == AdaptiveDecisionStatus.APPROVED_RESEARCH:
            for c in rec.selected_candidates:
                config_map[c.symbol] = {
                    "strategy": c.strategy_name,
                    "params": c.params,
                    "adaptive_score": c.composite_score,
                    "adaptive_confidence": c.confidence.value
                }
        return {
            "recommendation_id": rec.recommendation_id,
            "mode": rec.mode.value,
            "status": rec.status.value,
            "configs": config_map
        }

    def apply_parameter_update(self, parameter_sets: list[AdaptiveParameterSet], confirm: bool = False) -> list[AdaptiveParameterSet]:
        if not confirm:
            raise AdaptiveParameterStoreError("Explicit confirmation required for apply_parameter_update")
        try:
            from bist_signal_bot.security.preflight import SecurityPreflightRunner
            preflight = SecurityPreflightRunner(self.settings)
            preflight.run_preflight()

            results = []
            for p in parameter_sets:
                updated = self.parameter_store.upsert_parameter_set(p, confirm=True)
                results.append(updated)

            from bist_signal_bot.core.audit import audit_log
            audit_log(
                "ADAPTIVE_PARAMS_APPLIED",
                metadata={"count": len(results), "no_real_order_sent": True}
            )
            return results
        except Exception as e:
            self.logger.error(f"Failed to apply parameter update: {e}")
            raise AdaptiveError(f"Failed to apply parameters: {e}")
