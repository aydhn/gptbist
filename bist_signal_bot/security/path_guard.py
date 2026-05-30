from pathlib import Path
from bist_signal_bot.config.settings import Settings

class PathGuard:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    @staticmethod
    def ensure_safe_path(base_dir: Path, target_path: Path) -> bool:
        try:
            target_path.resolve().relative_to(base_dir.resolve())
            return True
        except ValueError:
            return False

    def validate_and_resolve(self, target_path: Path) -> Path:
        resolved = target_path.resolve()
        if self.base_dir:
            if not self.ensure_safe_path(self.base_dir, resolved):
                raise ValueError("Path traversal attempt blocked.")
        return resolved

    def redact_path(self, target_path: Path) -> Path:
        # A simple redaction mechanism
        resolved = target_path.resolve()
        if self.base_dir:
            try:
                rel = resolved.relative_to(self.base_dir.resolve())
                return Path("<BASE_DIR>") / rel
            except ValueError:
                pass

        home = Path.home()
        try:
            rel = resolved.relative_to(home.resolve())
            return Path("~") / rel
        except ValueError:
            pass

        return target_path
