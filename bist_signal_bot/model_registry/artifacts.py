import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelArtifactError
from bist_signal_bot.model_registry.models import ModelArtifact, ModelArtifactFormat
from bist_signal_bot.security.path_guard import PathGuard


class ModelArtifactManager:
    def __init__(self, settings: Settings | None = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.store = store
        self.path_guard = PathGuard(self.settings)


    def _is_safe(self, p):
        try:
            self.path_guard.ensure_safe_path(p)
            return True
        except:
            return False

    def checksum(self, path: Path) -> str | None:
        if not path.exists() or not path.is_file():
            return None
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate checksum for {path}: {e}")
            return None

    def infer_format(self, path: Path) -> ModelArtifactFormat:
        if path.is_dir():
            return ModelArtifactFormat.DIRECTORY

        ext = path.suffix.lower()
        if ext in [".pkl", ".pickle"]:
            return ModelArtifactFormat.PICKLE
        elif ext == ".joblib":
            return ModelArtifactFormat.JOBLIB
        elif ext == ".json":
            return ModelArtifactFormat.JSON
        elif ext == ".onnx":
            return ModelArtifactFormat.ONNX
        elif ext in [".pt", ".pth"]:
            return ModelArtifactFormat.TORCH
        elif ext == ".txt":
            return ModelArtifactFormat.TEXT

        # Try to infer from content or name if needed, but return UNKNOWN for now
        return ModelArtifactFormat.UNKNOWN

    def validate_artifact(self, artifact: ModelArtifact) -> list[str]:
        issues = []
        path_obj = Path(artifact.path)

        if not self._is_safe(path_obj):
            issues.append("Artifact path failed path guard validation")

        if self.settings.MODEL_ARTIFACT_CHECKSUM_REQUIRED and not artifact.checksum and artifact.artifact_format != ModelArtifactFormat.DIRECTORY:
            issues.append("Checksum is required but missing")

        allowed_formats = getattr(self.settings, "MODEL_ARTIFACT_ALLOWED_FORMATS", "JSON,JOBLIB,PICKLE,SKLEARN,TEXT,DIRECTORY").split(",")
        if artifact.artifact_format.value not in allowed_formats and artifact.artifact_format != ModelArtifactFormat.UNKNOWN:
            issues.append(f"Format {artifact.artifact_format.value} is not in allowed formats")

        return issues

    def check_loadable(self, artifact: ModelArtifact) -> bool | None:
        path_obj = Path(artifact.path)
        if not path_obj.exists():
            return False

        if artifact.artifact_format in [ModelArtifactFormat.PICKLE, ModelArtifactFormat.JOBLIB]:
            if getattr(self.settings, "MODEL_ARTIFACT_PICKLE_LOAD_BLOCKED", True):
                self.logger.warning(f"Pickle load check blocked by security policy for {artifact.path}")
                return None

        # In a real system, we might actually attempt to load the model here.
        # For now, we just check if the file exists and is accessible.
        try:
            if path_obj.is_file():
                with open(path_obj, "rb") as f:
                    f.read(1)
            return True
        except Exception:
            return False

    def register_artifact(self, path: Path, model_id: str | None = None, artifact_format: ModelArtifactFormat | None = None, confirm: bool = False) -> ModelArtifact:
        if not path.exists():
            raise ModelArtifactError(f"Artifact path does not exist: {path}")

        if not self._is_safe(path):
            raise ModelArtifactError(f"Artifact path is not safe: {path}")

        fmt = artifact_format or self.infer_format(path)

        # Calculate size
        size_bytes = sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) if path.is_dir() else path.stat().st_size

        artifact = ModelArtifact(
            artifact_id=f"art_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            path=str(path),
            artifact_format=fmt,
            created_at=datetime.now(timezone.utc),
            size_bytes=size_bytes,
            checksum=self.checksum(path) if fmt != ModelArtifactFormat.DIRECTORY else None
        )

        if getattr(self.settings, "MODEL_ARTIFACT_LOAD_CHECK_ENABLED", False):
            artifact.loadable = self.check_loadable(artifact)

        issues = self.validate_artifact(artifact)
        if issues:
            self.logger.warning(f"Validation issues for artifact {artifact.artifact_id}: {issues}")
            artifact.warnings.extend(issues)

        if not confirm:
            self.logger.info(f"[DRY-RUN] Would register artifact {artifact.artifact_id} for {path}")
            return artifact

        if not self.store:
            raise ModelArtifactError("Model store not configured")

        self.store.append_artifact(artifact)
        return artifact

    def artifact_for_model(self, model_id: str) -> ModelArtifact | None:
        if not self.store:
            return None
        artifacts = self.store.load_artifacts(model_id=model_id)
        if not artifacts:
            return None
        # Return the most recent one
        return sorted(artifacts, key=lambda a: a.created_at, reverse=True)[0]
