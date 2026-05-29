
import json
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.ops.models import StoreIntegrityResult, OpsStatus

class StoreIntegrityChecker:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_data_dir()
        self.path_guard = PathGuard(allowed_base_dirs=[self.base_dir])

    def expected_store_files(self) -> list[Path]:
        return [self.base_dir / "ops" / "health" / "ops_health_snapshots.jsonl"]

    def check_jsonl_file(self, path: Path) -> list[dict[str, Any]]:
        invalid_lines = []
        if not path.exists(): return invalid_lines
        max_lines = getattr(self.settings, "OPS_JSONL_CHECK_MAX_LINES", 100000) if self.settings else 100000
        try:
            with open(path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx >= max_lines: break
                    line = line.strip()
                    if not line: continue
                    try: json.loads(line)
                    except json.JSONDecodeError as e: invalid_lines.append({"path": str(path), "line_num": idx + 1, "error": str(e)})
        except Exception as e: invalid_lines.append({"path": str(path), "line_num": -1, "error": f"File read error: {e}"})
        return invalid_lines

    def find_orphan_files(self, root: Path) -> list[str]: return []

    def find_missing_expected_files(self, root: Path) -> list[str]:
        missing = []
        if getattr(self.settings, "OPS_STORE_CHECK_EXPECTED_FILES", True):
            for expected in self.expected_store_files():
                if not expected.exists(): missing.append(str(expected))
        return missing

    def classify_integrity(self, result: StoreIntegrityResult) -> OpsStatus:
        if result.invalid_files or result.invalid_lines: return OpsStatus.FAIL
        if result.missing_expected_files: return OpsStatus.WATCH
        return OpsStatus.PASS

    def check_store_integrity(self, root: Path | None = None) -> StoreIntegrityResult:
        now = datetime.now()
        target_root = root or self.base_dir
        self.path_guard.resolve_safe_path(target_root)

        files_checked = jsonl_files_checked = 0
        invalid_lines_all, invalid_files = [], []

        if target_root.exists() and target_root.is_dir():
            for p in target_root.rglob("*.jsonl"):
                files_checked += 1
                jsonl_files_checked += 1
                inv_lines = self.check_jsonl_file(p)
                if inv_lines:
                    invalid_lines_all.extend(inv_lines)
                    invalid_files.append(str(p))

        missing_expected = self.find_missing_expected_files(target_root)
        orphans = self.find_orphan_files(target_root)

        res = StoreIntegrityResult(
            result_id=f"integ_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, root_path=str(target_root),
            files_checked=files_checked, jsonl_files_checked=jsonl_files_checked,
            invalid_files=invalid_files, invalid_lines=invalid_lines_all,
            orphan_files=orphans, missing_expected_files=missing_expected, status=OpsStatus.UNKNOWN
        )
        res.status = self.classify_integrity(res)
        return res
