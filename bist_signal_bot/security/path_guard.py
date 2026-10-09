from pathlib import Path
from typing import Any, Optional

from bist_signal_bot.core.exceptions import PathSecurityError


class PathGuard:
    """Guards filesystem paths against traversal / unsafe locations.

    Usage styles supported across the codebase:
    - Static: ``PathGuard.ensure_safe_path(path, base_dir)`` raises on unsafe paths.
    - Instance: ``PathGuard([allowed...])`` (or ``allowed_base_dirs=[...]``) restricts
      resolved paths to the allowed directories. With no allowed directories
      configured only path traversal (``..``) is rejected.
    """

    def __init__(self, allowed_paths=None, allowed_base_dirs=None, settings: Any = None, base_dir: Any = None):
        # A Settings object may be passed positionally by legacy callers.
        if allowed_paths is not None and not isinstance(allowed_paths, (list, tuple, set)):
            settings, allowed_paths = allowed_paths, None
        dirs = list(allowed_paths or []) + list(allowed_base_dirs or [])
        if base_dir is not None:
            dirs.append(base_dir)
        self.allowed_paths = [Path(p).resolve() for p in dirs]
        self.allowed_base_dirs = self.allowed_paths
        self.settings = settings

    @staticmethod
    def ensure_safe_path(path: Path, base_dir: Path | None = None) -> None:
        path = Path(path)
        if ".." in path.parts:
            raise PathSecurityError("Path traversal attempt")
        if base_dir:
            try:
                path.resolve().relative_to(Path(base_dir).resolve())
            except ValueError:
                raise PathSecurityError("Path outside base_dir")
        elif path.is_absolute():
            # reject absolute paths as potentially unsafe when no base_dir is given
            raise PathSecurityError("Absolute paths not allowed without base_dir")

    def redact_path(self, path) -> str:
        """Return a display-safe path: the user's home directory is masked as ``~``."""
        text = str(path)
        try:
            home = str(Path.home())
        except Exception:
            return text
        if home and text.startswith(home):
            return "~" + text[len(home):]
        return text

    def assert_no_path_traversal(self, path) -> None:
        """Reject any path containing a ``..`` component."""
        if ".." in Path(path).parts:
            raise PathSecurityError(f"Path traversal sequences ('..') are not allowed: {path}")

    def _is_allowed(self, resolved: Path) -> bool:
        for allowed in self.allowed_paths:
            try:
                resolved.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def resolve_safe_path(self, path, must_be_under: Optional[Path] = None) -> Path:
        """Validate a path against traversal / allowed dirs and return its resolved form."""
        p = Path(path)
        self.assert_no_path_traversal(p)
        try:
            resolved = p.resolve()
        except Exception as e:
            raise PathSecurityError(f"Could not resolve path {path}: {e}")
        if must_be_under is not None:
            try:
                resolved.relative_to(Path(must_be_under).resolve())
            except ValueError:
                raise PathSecurityError(f"Path traversal blocked: {path} is not under {must_be_under}")
        elif self.allowed_paths and not self._is_allowed(resolved):
            raise PathSecurityError(f"Path traversal blocked: {path} is not under any allowed directory.")
        return resolved

    def assert_under_allowed_dirs(self, path) -> None:
        self.resolve_safe_path(path)

    def safe_join(self, base, *parts: str) -> Path:
        """Join paths, preventing escape from ``base``."""
        for part in parts:
            if ".." in Path(part).parts:
                raise PathSecurityError("Path traversal sequence '..' detected in join part.")
        base = Path(base)
        joined = base.joinpath(*parts)
        self.resolve_safe_path(joined, must_be_under=base)
        return joined

    def validate_model_path(self, path, allow_external: bool = False) -> None:
        """Validate a model (joblib/pickle) path; must live under an allowed dir unless allow_external."""
        self.assert_no_path_traversal(path)
        if not allow_external:
            self.resolve_safe_path(path)
