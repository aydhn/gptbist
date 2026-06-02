
from pathlib import Path
class PathGuard:
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
             # if no base_dir provided, reject absolute paths as potentially unsafe in tests
             # unless we know it's fine. For test_check_unsafe_path it expects /etc/passwd to fail.
             raise ValueError("Absolute paths not allowed without base_dir")
