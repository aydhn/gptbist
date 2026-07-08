import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
import joblib

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_ml_models_dir
from bist_signal_bot.ml.training.models import MLModelArtifact, MLModelType, MLTaskType, MLFeatureImportance, MLTrainResult
from bist_signal_bot.security.path_guard import PathGuard

from bist_signal_bot.core.exceptions import MLModelRegistryError

logger = logging.getLogger(__name__)

class MLModelRegistry:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_ml_models_dir(settings)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path_guard = PathGuard()

    def get_models_dir(self) -> Path:
        return self.base_dir

    def create_model_id(self, strategy_or_dataset_name: str | None, model_type: MLModelType, timestamp: datetime | None = None) -> str:
        ts = timestamp or datetime.now()
        dt_str = ts.strftime("%Y%m%d_%H%M%S")
        prefix = strategy_or_dataset_name or "model"
        return f"{prefix}_{model_type.value}_{dt_str}".lower().replace(" ", "_")

    def save_model(self, estimator: Any, preprocessor: Any, artifact: MLModelArtifact, train_result: MLTrainResult | None = None) -> MLModelArtifact:
        model_dir = self.base_dir / artifact.model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / "model.joblib"
        prep_path = model_dir / "preprocessor.joblib"
        metadata_path = model_dir / "metadata.json"

        try:
            joblib.dump(estimator, model_path)
            joblib.dump(preprocessor, prep_path)

            artifact.model_path = str(model_path)
            artifact.metadata_path = str(metadata_path)

            if train_result and train_result.feature_importance:
                self.save_feature_importance(train_result.feature_importance, model_dir)
                artifact.feature_importance_top = [f.model_dump() for f in train_result.feature_importance[:20]]

            self.save_metadata(artifact)
            return artifact
        except Exception as e:
            raise MLModelRegistryError(f"Failed to save model {artifact.model_id}: {e}")

    def load_model(self, model_id: str) -> tuple[Any, Any, MLModelArtifact]:
        model_dir = self.base_dir / model_id
        self.path_guard.validate_model_path(model_dir, allow_external=getattr(self.settings, "SECURITY_ALLOW_EXTERNAL_MODEL_PATH", False))
        model_dir = self.base_dir / model_id
        if not model_dir.exists():
            raise MLModelRegistryError(f"Model directory not found: {model_dir}")

        model_path = model_dir / "model.joblib"
        prep_path = model_dir / "preprocessor.joblib"
        metadata_path = model_dir / "metadata.json"

        if not model_path.exists() or not metadata_path.exists():
            raise MLModelRegistryError(f"Model files missing for {model_id}")

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)
            artifact = MLModelArtifact(**metadata_dict)
            # WARNING: joblib.load is unsafe and vulnerable to insecure deserialization.
            # Untrusted models should not be loaded using this function as it can lead to
            # Arbitrary Code Execution (ACE). In the future, migrate to a safe format
            # like ONNX or implement cryptographic model signing and verification.
            logger.warning("Loading model with joblib.load. Ensure the model source is trusted to prevent insecure deserialization.")
            estimator = joblib.load(model_path)
            preprocessor = joblib.load(prep_path) if prep_path.exists() else None

            return estimator, preprocessor, artifact
        except Exception as e:
            raise MLModelRegistryError(f"Failed to load model {model_id}: {e}")

    def load_model_by_path(self, model_path: Path) -> tuple[Any, Any, dict[str, Any]]:
        # This is essentially identical to load_model, implemented for direct path usage
        model_dir = model_path
        if not model_dir.is_dir():
            # perhaps the user gave the exact joblib path
            if model_dir.name.endswith(".joblib"):
                model_dir = model_dir.parent

        if not model_dir.exists():
            raise MLModelRegistryError(f"Model directory not found: {model_dir}")

        m_path = model_dir / "model.joblib"
        p_path = model_dir / "preprocessor.joblib"
        md_path = model_dir / "metadata.json"

        try:
            with open(md_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)
            # WARNING: joblib.load is unsafe and vulnerable to insecure deserialization.
            # Untrusted models should not be loaded using this function as it can lead to
            # Arbitrary Code Execution (ACE). In the future, migrate to a safe format
            # like ONNX or implement cryptographic model signing and verification.
            logger.warning("Loading model with joblib.load. Ensure the model source is trusted to prevent insecure deserialization.")
            estimator = joblib.load(m_path)
            preprocessor = joblib.load(p_path) if p_path.exists() else None

            return estimator, preprocessor, metadata_dict
        except Exception as e:
            raise MLModelRegistryError(f"Failed to load model by path {model_path}: {e}")

    def save_metadata(self, artifact: MLModelArtifact) -> Path:
        md_path = Path(artifact.metadata_path)
        with open(md_path, "w", encoding="utf-8") as f:
            # We serialize created_at and complex structures
            json.dump(json.loads(artifact.model_dump_json()), f, indent=2)
        return md_path

    def save_feature_importance(self, feature_importance: list[MLFeatureImportance], model_dir: Path) -> Path:
        fi_path = model_dir / "feature_importance.csv"
        import pandas as pd
        df = pd.DataFrame([fi.model_dump() for fi in feature_importance])
        df.to_csv(fi_path, index=False)
        return fi_path

    def list_models(self, limit: int = 20) -> list[dict[str, Any]]:
        models = []
        for model_dir in self.base_dir.iterdir():
            if model_dir.is_dir():
                md_path = model_dir / "metadata.json"
                if md_path.exists():
                    try:
                        with open(md_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            models.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read metadata for {model_dir.name}: {e}")

        # Sort by created_at desc
        models.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return models[:limit]

    def delete_model(self, model_id: str) -> bool:
        model_dir = self.base_dir / model_id
        if not model_dir.exists():
            return False

        try:
            import shutil
            shutil.rmtree(model_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            return False
