import uuid
from datetime import datetime, timezone
from typing import Any
from bist_signal_bot.explainability.models import (
    ExplanationCohort,
    ExplanationObjectType,
    ExplanationStatus
)

class ExplanationCohortBuilder:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def build_cohort(self, name: str, object_type: ExplanationObjectType, object_ids: list[str], symbols: list[str], feature_names: list[str]) -> ExplanationCohort:
        cohort = ExplanationCohort(
            cohort_id=str(uuid.uuid4()),
            name=name,
            object_type=object_type,
            object_ids=object_ids,
            symbols=symbols,
            feature_names=feature_names,
            sample_count=len(object_ids) if object_ids else len(symbols),
            created_at=datetime.now(timezone.utc),
            status=ExplanationStatus.PASS
        )
        warnings = self.validate_cohort(cohort)
        if warnings:
            cohort.status = ExplanationStatus.WATCH
            cohort.warnings = warnings
        return cohort

    def cohort_from_feature_frame(self, frame: Any, name: str = "feature_frame_cohort") -> ExplanationCohort:
        # Mocking frame as a dict with 'columns' and 'index'
        feature_names = []
        symbols = []
        if hasattr(frame, "columns"):
            feature_names = list(frame.columns)
        if hasattr(frame, "index"):
            # Assume index holds symbols or we just make up one
            symbols = ["UNKNOWN"] * len(frame.index)

        return self.build_cohort(
            name=name,
            object_type=ExplanationObjectType.FEATURE_SET,
            object_ids=[],
            symbols=symbols,
            feature_names=feature_names
        )

    def cohort_from_model_registry(self, model_ids: list[str]) -> ExplanationCohort:
        return self.build_cohort(
            name="model_registry_cohort",
            object_type=ExplanationObjectType.MODEL,
            object_ids=model_ids,
            symbols=[],
            feature_names=[]
        )

    def validate_cohort(self, cohort: ExplanationCohort) -> list[str]:
        warnings = []
        if cohort.sample_count == 0:
            warnings.append("Cohort is empty.")
        if not cohort.feature_names and cohort.object_type == ExplanationObjectType.FEATURE_SET:
            warnings.append("Feature set cohort lacks feature names.")
        return warnings
