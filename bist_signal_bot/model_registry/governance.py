import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import (
    ModelGovernanceAssessment, ModelGovernanceStatus, ModelRecord
)


class ModelGovernanceEngine:
    def __init__(self, settings: Settings | None = None, registry: Any = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.registry = registry
        self.store = store

    def artifact_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        artifacts = self.store.load_artifacts(model_id=model.model_id)
        if not artifacts:
            return ModelGovernanceStatus.FAIL

        latest = sorted(artifacts, key=lambda a: a.created_at, reverse=True)[0]

        # In a real system, loadable might be None if blocked, False if failed
        if latest.loadable is False:
            return ModelGovernanceStatus.FAIL

        return ModelGovernanceStatus.PASS

    def model_card_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        cards = self.store.load_model_cards(model_id=model.model_id)
        if not cards:
            return ModelGovernanceStatus.WATCH if not getattr(self.settings, "MODEL_REGISTRY_REQUIRE_MODEL_CARD", True) else ModelGovernanceStatus.FAIL

        latest = sorted(cards, key=lambda c: c.created_at, reverse=True)[0]
        return latest.governance_status

    def validation_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        if not model.validation_result_id:
            return ModelGovernanceStatus.INSUFFICIENT_DATA

        vals = self.store.load_validation_summaries(model_id=model.model_id)
        val = next((v for v in vals if v.validation_id == model.validation_result_id), None)
        if not val:
            # Maybe the latest
            if vals:
                val = sorted(vals, key=lambda v: v.created_at, reverse=True)[0]
            else:
                return ModelGovernanceStatus.UNKNOWN

        return val.status

    def calibration_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        if not model.calibration_result_id:
            return ModelGovernanceStatus.INSUFFICIENT_DATA

        cals = self.store.load_calibration_summaries(model_id=model.model_id)
        cal = next((c for c in cals if c.calibration_id == model.calibration_result_id), None)
        if not cal:
            if cals:
                cal = sorted(cals, key=lambda c: c.created_at, reverse=True)[0]
            else:
                return ModelGovernanceStatus.UNKNOWN

        return cal.status

    def feature_quality_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        # We can extract this from validation summary if available
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        vals = self.store.load_validation_summaries(model_id=model.model_id)
        if not vals:
            return ModelGovernanceStatus.UNKNOWN

        latest = sorted(vals, key=lambda v: v.created_at, reverse=True)[0]
        if latest.feature_quality_score is None:
            return ModelGovernanceStatus.UNKNOWN

        min_score = getattr(self.settings, "MODEL_VALIDATION_FEATURE_QUALITY_MIN_SCORE", 70.0)
        if latest.feature_quality_score < min_score:
            return ModelGovernanceStatus.FAIL
        elif latest.feature_quality_score < min_score + 10.0:
            return ModelGovernanceStatus.WATCH
        return ModelGovernanceStatus.PASS

    def leakage_status(self, model: ModelRecord) -> ModelGovernanceStatus:
        # Also extracted from validation summary
        if not self.store:
            return ModelGovernanceStatus.UNKNOWN

        vals = self.store.load_validation_summaries(model_id=model.model_id)
        if not vals:
            return ModelGovernanceStatus.UNKNOWN

        latest = sorted(vals, key=lambda v: v.created_at, reverse=True)[0]
        return latest.leakage_status

    def blocking_reasons(self, statuses: dict[str, ModelGovernanceStatus]) -> list[str]:
        reasons = []
        if statuses.get("leakage") == ModelGovernanceStatus.BLOCKED:
            reasons.append("Critical feature leakage detected")

        if statuses.get("artifact") == ModelGovernanceStatus.FAIL:
            reasons.append("Model artifact is missing or corrupted")

        if statuses.get("card") == ModelGovernanceStatus.FAIL:
            reasons.append("Required model card is missing")

        if statuses.get("validation") == ModelGovernanceStatus.FAIL:
            reasons.append("Model failed validation checks")

        return reasons

    def final_status(self, parts: dict[str, ModelGovernanceStatus | None]) -> ModelGovernanceStatus:
        # Leakage BLOCKED is absolute
        if parts.get("leakage") == ModelGovernanceStatus.BLOCKED:
            return ModelGovernanceStatus.BLOCKED

        # Any FAIL leads to FAIL
        for k, v in parts.items():
            if v == ModelGovernanceStatus.FAIL:
                return ModelGovernanceStatus.FAIL

        # Any INSUFFICIENT_DATA leads to WATCH or INSUFFICIENT_DATA
        if ModelGovernanceStatus.INSUFFICIENT_DATA in parts.values():
            return ModelGovernanceStatus.INSUFFICIENT_DATA

        # Any WATCH leads to WATCH
        if ModelGovernanceStatus.WATCH in parts.values():
            return ModelGovernanceStatus.WATCH

        return ModelGovernanceStatus.PASS

    def assess_model(self, model_id: str) -> ModelGovernanceAssessment:
        if not self.registry:
            # Return empty/unknown assessment
            return ModelGovernanceAssessment(
                assessment_id=f"gov_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
                model_id=model_id,
                created_at=datetime.now(timezone.utc),
                status=ModelGovernanceStatus.UNKNOWN,
                warnings=["Registry not configured"]
            )

        model = self.registry.get_model(model_id)
        if not model:
            # Model missing
            return ModelGovernanceAssessment(
                assessment_id=f"gov_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
                model_id=model_id,
                created_at=datetime.now(timezone.utc),
                status=ModelGovernanceStatus.UNKNOWN,
                warnings=["Model not found"]
            )

        parts = {
            "artifact": self.artifact_status(model),
            "card": self.model_card_status(model),
            "validation": self.validation_status(model),
            "calibration": self.calibration_status(model),
            "feature_quality": self.feature_quality_status(model),
            "leakage": self.leakage_status(model)
        }

        reasons = self.blocking_reasons(parts)
        status = self.final_status(parts)

        assessment = ModelGovernanceAssessment(
            assessment_id=f"gov_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            created_at=datetime.now(timezone.utc),
            status=status,
            validation_status=parts["validation"],
            calibration_status=parts["calibration"],
            feature_quality_status=parts["feature_quality"],
            leakage_status=parts["leakage"],
            artifact_status=parts["artifact"],
            model_card_status=parts["card"],
            blocking_reasons=reasons
        )

        if self.store:
            self.store.append_governance_assessment(assessment)

        return assessment
