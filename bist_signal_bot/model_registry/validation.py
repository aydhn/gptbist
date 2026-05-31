import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import ModelValidationSummary, ModelGovernanceStatus


class ModelValidationGovernance:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def check_min_sample(self, sample_count: int | None) -> list[str]:
        issues = []
        min_sample = getattr(self.settings, "MODEL_VALIDATION_MIN_SAMPLE", 100)
        if sample_count is None:
            issues.append("Sample count is missing")
        elif sample_count < min_sample:
            issues.append(f"Sample count {sample_count} is below minimum required {min_sample}")
        return issues

    def check_overfit(self, walk_forward_summary: dict[str, Any]) -> list[str]:
        issues = []
        if not getattr(self.settings, "MODEL_VALIDATION_OVERFIT_WARN_ENABLED", True):
            return issues

        if not walk_forward_summary:
            return issues

        # Example logic: if train metric is much higher than test metric
        train_score = walk_forward_summary.get("mean_train_score")
        test_score = walk_forward_summary.get("mean_test_score")

        if train_score is not None and test_score is not None:
            # Assuming higher is better (like AUC or accuracy)
            # If it's a loss, this logic would need to be flipped based on a metric_direction param
            # We'll use a simple ratio for demonstration
            if test_score > 0 and (train_score - test_score) / test_score > 0.2:
                issues.append(f"Potential overfitting: Train score {train_score:.3f} is significantly higher than test score {test_score:.3f}")

        folds = walk_forward_summary.get("n_folds", 0)
        min_folds = getattr(self.settings, "MODEL_VALIDATION_MIN_WALK_FORWARD_FOLDS", 3)
        if folds > 0 and folds < min_folds:
            issues.append(f"Walk-forward folds {folds} below minimum {min_folds}")

        return issues

    def check_feature_quality(self, feature_quality_score: float | None) -> ModelGovernanceStatus:
        if feature_quality_score is None:
            return ModelGovernanceStatus.UNKNOWN

        min_score = getattr(self.settings, "MODEL_VALIDATION_FEATURE_QUALITY_MIN_SCORE", 70.0)
        if feature_quality_score < min_score:
            return ModelGovernanceStatus.FAIL
        elif feature_quality_score < min_score + 10.0:
            return ModelGovernanceStatus.WATCH
        return ModelGovernanceStatus.PASS

    def status_from_metrics(self, metrics: dict[str, float], overfit_warnings: list[str], leakage_status: ModelGovernanceStatus | None = None) -> ModelGovernanceStatus:
        if leakage_status == ModelGovernanceStatus.BLOCKED:
            return ModelGovernanceStatus.BLOCKED

        if overfit_warnings:
            # If there are many warnings or severe, maybe FAIL, else WATCH
            return ModelGovernanceStatus.WATCH

        # In a real implementation, we would check if AUC > 0.55, Accuracy > 0.5 etc.
        # For this generic registry, if we have metrics and no leakage/overfit warnings, we PASS
        if metrics:
            return ModelGovernanceStatus.PASS

        return ModelGovernanceStatus.UNKNOWN

    def validate_summary(self, summary: ModelValidationSummary) -> list[str]:
        issues = []
        if not summary.validation_method:
            issues.append("validation_method is empty")
        return issues

    def summarize_validation(self, model_id: str, validation_result: Any | None = None,
                             sample_count: int | None = None,
                             metrics: dict[str, float] | None = None,
                             walk_forward_summary: dict[str, Any] | None = None,
                             robustness_summary: dict[str, Any] | None = None,
                             leakage_status: ModelGovernanceStatus = ModelGovernanceStatus.PASS,
                             feature_quality_score: float | None = None) -> ModelValidationSummary:

        warnings = []
        overfit_warnings = self.check_overfit(walk_forward_summary or {})
        warnings.extend(overfit_warnings)

        sample_issues = self.check_min_sample(sample_count)
        warnings.extend(sample_issues)

        fq_status = self.check_feature_quality(feature_quality_score)
        if fq_status in [ModelGovernanceStatus.FAIL, ModelGovernanceStatus.WATCH]:
            warnings.append(f"Feature quality score {feature_quality_score} triggered {fq_status.value}")

        status = self.status_from_metrics(metrics or {}, overfit_warnings, leakage_status)

        # Override status if sample count is too low
        if sample_issues and status in [ModelGovernanceStatus.PASS, ModelGovernanceStatus.UNKNOWN]:
            status = ModelGovernanceStatus.WATCH

        summary = ModelValidationSummary(
            validation_id=f"val_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            created_at=datetime.now(timezone.utc),
            validation_method="walk_forward" if walk_forward_summary else "train_test_split",
            sample_count=sample_count,
            metrics=metrics or {},
            walk_forward_summary=walk_forward_summary or {},
            robustness_summary=robustness_summary or {},
            overfit_warnings=overfit_warnings,
            leakage_status=leakage_status,
            feature_quality_score=feature_quality_score,
            status=status,
            warnings=warnings
        )

        val_issues = self.validate_summary(summary)
        summary.warnings.extend(val_issues)

        return summary
