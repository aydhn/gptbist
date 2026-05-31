import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelPromotionError
from bist_signal_bot.model_registry.models import (
    ModelPromotionRequest, ModelPromotionStage, ModelRecord, ModelRegistryStatus, ModelGovernanceStatus
)


class ModelPromotionManager:
    def __init__(self, settings: Settings | None = None, registry: Any = None, governance_engine: Any = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.registry = registry
        self.governance_engine = governance_engine
        self.store = store

    def evaluate_promotion(self, model: ModelRecord, requested_stage: ModelPromotionStage) -> tuple[ModelGovernanceStatus, list[str]]:
        if not self.governance_engine:
            # Fallback if no engine provided
            return ModelGovernanceStatus.UNKNOWN, ["Governance engine not configured"]

        assessment = self.governance_engine.assess_model(model.model_id)
        reasons = []

        if requested_stage == ModelPromotionStage.ACTIVE_RESEARCH:
            if getattr(self.settings, "MODEL_PROMOTION_BLOCK_ON_MISSING_CARD", True) and assessment.model_card_status != ModelGovernanceStatus.PASS:
                reasons.append("Model card missing or incomplete")

            if getattr(self.settings, "MODEL_PROMOTION_BLOCK_ON_MISSING_ARTIFACT", True) and assessment.artifact_status != ModelGovernanceStatus.PASS:
                reasons.append("Model artifact missing or load check failed")

            if getattr(self.settings, "MODEL_PROMOTION_BLOCK_ON_LEAKAGE", True) and assessment.leakage_status == ModelGovernanceStatus.BLOCKED:
                reasons.append("Model blocked due to feature leakage")

            if getattr(self.settings, "MODEL_PROMOTION_ACTIVE_RESEARCH_REQUIRES_PASS", True) and assessment.status not in [ModelGovernanceStatus.PASS, ModelGovernanceStatus.WATCH]:
                reasons.append(f"Model governance status {assessment.status.value} does not meet requirements")

            if reasons:
                return ModelGovernanceStatus.BLOCKED, reasons

            if assessment.status == ModelGovernanceStatus.WATCH:
                return ModelGovernanceStatus.WATCH, ["Model meets minimum requirements but has warnings"]

            return ModelGovernanceStatus.PASS, []

        return ModelGovernanceStatus.PASS, []

    def request_promotion(self, model_id: str, requested_stage: ModelPromotionStage, reason: str, requested_by: str | None = None) -> ModelPromotionRequest:
        if not self.registry:
            raise ModelPromotionError("Model registry not configured")

        model = self.registry.get_model(model_id)
        if not model:
            raise ModelPromotionError(f"Model not found: {model_id}")

        current_stage = ModelPromotionStage.UNKNOWN
        try:
            current_stage = ModelPromotionStage(model.status.value)
        except ValueError:
            # E.g. WATCH -> UNKNOWN stage mapping
            pass

        gov_status, warnings = self.evaluate_promotion(model, requested_stage)

        # Determine approval automatically based on governance (could be manual in a real system)
        approved = gov_status in [ModelGovernanceStatus.PASS, ModelGovernanceStatus.WATCH]

        req = ModelPromotionRequest(
            promotion_id=f"promo_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            requested_stage=requested_stage,
            current_stage=current_stage,
            requested_at=datetime.now(timezone.utc),
            requested_by=requested_by,
            reason=reason,
            governance_decision=gov_status,
            approved=approved,
            warnings=warnings
        )

        # We also need validation/calibration status in the request for record-keeping
        if self.governance_engine:
            assessment = self.governance_engine.assess_model(model_id)
            req.validation_status = assessment.validation_status
            req.calibration_status = assessment.calibration_status
            req.leakage_status = assessment.leakage_status

        if self.store:
            self.store.append_promotion_request(req)

        return req

    def approve_research_promotion(self, promotion_id: str, confirm: bool = False) -> ModelPromotionRequest:
        if not self.store or not self.registry:
            raise ModelPromotionError("Store or registry not configured")

        reqs = self.store.load_promotion_requests()
        req = next((r for r in reqs if r.promotion_id == promotion_id), None)
        if not req:
            raise ModelPromotionError(f"Promotion request not found: {promotion_id}")

        if req.governance_decision == ModelGovernanceStatus.BLOCKED:
            raise ModelPromotionError(f"Cannot approve BLOCKED promotion request: {promotion_id}")

        if getattr(self.settings, "MODEL_PROMOTION_REQUIRES_CONFIRM", True) and not confirm:
            self.logger.info(f"[DRY-RUN] Would approve promotion {promotion_id}")
            return req

        req.approved = True

        # Map stage to registry status
        try:
            new_status = ModelRegistryStatus(req.requested_stage.value)
            self.registry.update_model_status(req.model_id, new_status, confirm=confirm)
        except ValueError:
            self.logger.warning(f"Could not map stage {req.requested_stage.value} to registry status")

        if confirm:
            self.store.append_promotion_request(req)

        return req

    def reject_promotion(self, promotion_id: str, reason: str, confirm: bool = False) -> ModelPromotionRequest:
        if not self.store:
            raise ModelPromotionError("Store not configured")

        reqs = self.store.load_promotion_requests()
        req = next((r for r in reqs if r.promotion_id == promotion_id), None)
        if not req:
            raise ModelPromotionError(f"Promotion request not found: {promotion_id}")

        req.approved = False
        req.warnings.append(f"Rejected: {reason}")

        if confirm:
            self.store.append_promotion_request(req)

        return req

    def promotion_history(self, model_id: str) -> list[ModelPromotionRequest]:
        if not self.store:
            return []
        return self.store.load_promotion_requests(model_id=model_id)
