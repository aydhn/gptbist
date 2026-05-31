import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelRegistryError
from bist_signal_bot.model_registry.models import ModelRecord, ModelRegistryStatus, ModelKind


class LocalModelRegistry:
    def __init__(self, settings: Settings | None = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.store = store

    def validate_model_record(self, model: ModelRecord) -> list[str]:
        issues = []
        if not model.model_name:
            issues.append("model_name cannot be empty")
        if not model.version:
            issues.append("version cannot be empty")
        if model.status == ModelRegistryStatus.ACTIVE_RESEARCH:
            if self.settings.MODEL_REGISTRY_REQUIRE_VALIDATION and not model.validation_result_id:
                issues.append("ACTIVE_RESEARCH model requires validation metadata")
            if self.settings.MODEL_REGISTRY_REQUIRE_CALIBRATION and not model.calibration_result_id:
                issues.append("ACTIVE_RESEARCH model requires calibration metadata")
            if self.settings.MODEL_REGISTRY_REQUIRE_FEATURE_SET_VERSION and not model.feature_set_version:
                issues.append("ACTIVE_RESEARCH model requires feature_set_version")
        return issues

    def register_model(self, model: ModelRecord, confirm: bool = False) -> ModelRecord:
        issues = self.validate_model_record(model)
        if issues:
            self.logger.warning(f"Validation issues for model {model.model_id}: {issues}")

        if not confirm:
            self.logger.info(f"[DRY-RUN] Would register model {model.model_id}")
            return model

        if not self.store:
            raise ModelRegistryError("Model store not configured")

        self.store.append_model(model)
        self.logger.info(f"Registered model {model.model_id} in local registry")

        # We need audit logger, but we will leave it for integration later, or mock it.
        return model

    def list_models(self, status: ModelRegistryStatus | None = None, kind: ModelKind | None = None) -> list[ModelRecord]:
        if not self.store:
            return []
        models = self.store.load_models(status=status)
        if kind:
            models = [m for m in models if m.model_kind == kind]
        return models

    def get_model(self, model_id_or_name: str) -> ModelRecord | None:
        if not self.store:
            return None
        return self.store.get_model(model_id_or_name)

    def update_model_status(self, model_id: str, status: ModelRegistryStatus, warning: str | None = None, confirm: bool = False) -> ModelRecord:
        model = self.get_model(model_id)
        if not model:
            raise ModelRegistryError(f"Model not found: {model_id}")

        model.status = status
        model.updated_at = datetime.now(timezone.utc)
        if warning:
            model.warnings.append(warning)

        return self.register_model(model, confirm=confirm)

    def archive_model(self, model_id: str, confirm: bool = False) -> ModelRecord:
        return self.update_model_status(model_id, ModelRegistryStatus.ARCHIVED, confirm=confirm)

    def safe_model_summary(self, model: ModelRecord) -> dict[str, Any]:
        return {
            "model_id": model.model_id,
            "model_name": model.model_name,
            "version": model.version,
            "status": model.status.value,
            "kind": model.model_kind.value,
            "feature_set_version": model.feature_set_version,
            "created_at": model.created_at.isoformat(),
            "disclaimer": model.disclaimer
        }
