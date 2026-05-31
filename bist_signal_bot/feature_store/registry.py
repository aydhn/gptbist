from datetime import datetime, timezone
from typing import Any
from bist_signal_bot.feature_store.models import FeatureDefinition, FeatureSet, FeatureStatus, FeatureKind
from bist_signal_bot.core.exceptions import FeatureRegistryError

class FeatureRegistry:
    def __init__(self):
        self._features: dict[str, FeatureDefinition] = {f.feature_name: f for f in self.default_feature_definitions()}
        self._sets: dict[str, FeatureSet] = {s.feature_set_id: s for s in self.default_feature_sets()}

    def register_feature(self, feature: FeatureDefinition, confirm: bool = False) -> FeatureDefinition:
        errors = self.validate_feature_definition(feature)
        if errors:
            raise FeatureRegistryError(f"Invalid feature definition: {', '.join(errors)}")
        self._features[feature.feature_name] = feature
        return feature

    def default_feature_definitions(self) -> list[FeatureDefinition]:
        return []

    def list_features(self, kind: FeatureKind | None = None, status: FeatureStatus | None = None) -> list[FeatureDefinition]:
        features = list(self._features.values())
        if kind:
            features = [f for f in features if f.feature_kind == kind]
        if status:
            features = [f for f in features if f.status == status]
        return features

    def get_feature(self, feature_name: str) -> FeatureDefinition | None:
        return self._features.get(feature_name)

    def register_feature_set(self, feature_set: FeatureSet, confirm: bool = False) -> FeatureSet:
        errors = self.validate_feature_set(feature_set)
        if errors:
            raise FeatureRegistryError(f"Invalid feature set: {', '.join(errors)}")
        self._sets[feature_set.feature_set_id] = feature_set
        return feature_set

    def default_feature_sets(self) -> list[FeatureSet]:
        now = datetime.now(timezone.utc)
        return [
            FeatureSet(feature_set_id="fs_scanner_core_v1", name="scanner_core_v1", version="1.0", created_at=now, purpose="Core features for scanning"),
            FeatureSet(feature_set_id="fs_ml_core_v1", name="ml_core_v1", version="1.0", created_at=now, purpose="Core features for ML"),
            FeatureSet(feature_set_id="fs_validation_core_v1", name="validation_core_v1", version="1.0", created_at=now, purpose="Core features for validation"),
            FeatureSet(feature_set_id="fs_context_light_v1", name="context_light_v1", version="1.0", created_at=now, purpose="Light context features"),
            FeatureSet(feature_set_id="fs_full_research_v1", name="full_research_v1", version="1.0", created_at=now, purpose="Full research features"),
            FeatureSet(feature_set_id="fs_qa_synthetic_v1", name="qa_synthetic_v1", version="1.0", created_at=now, purpose="Synthetic features for QA")
        ]

    def get_feature_set(self, name_or_id: str) -> FeatureSet | None:
        for fset in self._sets.values():
            if fset.feature_set_id == name_or_id or fset.name == name_or_id:
                return fset
        return None

    def validate_feature_definition(self, feature: FeatureDefinition) -> list[str]:
        errors = []
        if not feature.feature_name:
            errors.append("feature_name cannot be empty")
        for source in feature.source_datasets:
            if "secret" in source.lower():
                errors.append("source_datasets cannot contain secret paths")
        return errors

    def validate_feature_set(self, feature_set: FeatureSet) -> list[str]:
        errors = []
        if not feature_set.name:
            errors.append("feature_set name cannot be empty")
        return errors
