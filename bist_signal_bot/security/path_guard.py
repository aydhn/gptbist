from pathlib import Path

class PathGuard:
    @staticmethod
    def ensure_safe_path(base_dir: Path, target_path: Path) -> bool:
        try:
            target_path.resolve().relative_to(base_dir.resolve())
            return True
        except ValueError:
            return False
