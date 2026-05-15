from pathlib import Path
from typing import Optional

from bist_signal_bot.core.exceptions import PathSecurityError

class PathGuard:
    """Protects against path traversal attacks and restricts access to allowed directories."""

    def __init__(self, allowed_base_dirs: list[Path]):
        # Ensure all allowed dirs are fully resolved absolute paths
        self.allowed_base_dirs = [p.resolve() for p in allowed_base_dirs]

    def resolve_safe_path(self, path: Path, must_be_under: Optional[Path] = None) -> Path:
        """Resolves a path and ensures it falls under an allowed base directory (or specific dir)."""
        try:
            resolved = path.resolve()
        except Exception as e:
            raise PathSecurityError(f"Could not resolve path {path}: {e}")

        # Check for specific directory requirement
        if must_be_under:
            must_be_under_resolved = must_be_under.resolve()
            try:
                resolved.relative_to(must_be_under_resolved)
            except ValueError:
                raise PathSecurityError(f"Path traversal blocked: {path} is not under {must_be_under}")
            return resolved

        # Check against general allowed base dirs
        for allowed in self.allowed_base_dirs:
            try:
                resolved.relative_to(allowed)
                return resolved
            except ValueError:
                continue

        raise PathSecurityError(f"Path traversal blocked: {path} is not under any allowed base directories.")

    def assert_under_allowed_dirs(self, path: Path) -> None:
        """Raises PathSecurityError if the path is not under any allowed directory."""
        self.resolve_safe_path(path)

    def assert_no_path_traversal(self, path: Path) -> None:
        """Basic check: if path contains '..' raise an error immediately."""
        if ".." in str(path) or path.name.startswith(".."):
            raise PathSecurityError(f"Path traversal sequences ('..') are not allowed: {path}")

    def safe_join(self, base: Path, *parts: str) -> Path:
        """Safely joins paths, preventing escape from the base directory."""
        for part in parts:
            if ".." in part:
                 raise PathSecurityError("Path traversal sequence '..' detected in join part.")

        joined = base.joinpath(*parts)
        # Verify it stays under base
        self.resolve_safe_path(joined, must_be_under=base)
        return joined

    def validate_model_path(self, path: Path, allow_external: bool = False) -> None:
        """Special validation for loading ML models (joblib/pickle) to ensure they come from trusted dirs."""
        if not allow_external:
            # We assume one of the allowed_base_dirs is the local model registry.
            # Usually, you'd check specifically against the configured ML_MODELS_DIR,
            # but for now we enforce it is under *some* allowed base (typically PROJECT_ROOT).
            self.resolve_safe_path(path)
