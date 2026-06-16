from pathlib import Path


class PathGuard:
    """Guards filesystem paths against traversal / unsafe locations.

    Two usage styles are supported across the codebase:
    - Static: ``PathGuard.ensure_safe_path(path, base_dir)`` raises on unsafe paths.
    - Instance: ``PathGuard([allowed...]).resolve_safe_path(path)`` validates and
      returns the resolved path (used by the adaptive / storage layers).
    """

    def __init__(self, allowed_paths=None):
        self.allowed_paths = [Path(p) for p in (allowed_paths or [])]

    @staticmethod
    def ensure_safe_path(path: Path, base_dir: Path | None = None) -> None:
        p_str = str(path)
        if ".." in p_str:
            raise ValueError("Path traversal attempt")
        if base_dir:
            try:
                # if path is absolute but not inside base_dir, this raises ValueError
                path.resolve().relative_to(base_dir.resolve())
            except ValueError:
                raise ValueError("Path outside base_dir")
        elif path.is_absolute():
            # reject absolute paths as potentially unsafe when no base_dir is given
            raise ValueError("Absolute paths not allowed without base_dir")

    def resolve_safe_path(self, path) -> Path:
        """Validate a path against traversal and return its resolved form.

        Absolute paths are permitted here (the adaptive/storage layers write to
        absolute data dirs); only path traversal is rejected.
        """
        p = Path(path)
        if ".." in str(p):
            raise ValueError("Path traversal attempt")
        return p.resolve()
