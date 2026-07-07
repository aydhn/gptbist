import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.stress.models import StressTestResult
from bist_signal_bot.storage.paths import get_stress_dir
from bist_signal_bot.core.exceptions import StressStorageError

class StressStore:
    def __init__(self, base_dir: Path | None = None):
        self.logger = logging.getLogger("bist_signal_bot.stress.storage")
        # Assume get_stress_dir returns base_dir/stress or similar
        try:
            self.base_path = get_stress_dir() if base_dir is None else base_dir / "stress"
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.base_path = Path("data/stress")
            self.base_path.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: StressTestResult) -> dict[str, Path]:
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            result_dir = self.base_path / "results" / date_str / result.stress_id
            result_dir.mkdir(parents=True, exist_ok=True)

            result_file = result_dir / "stress_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)

            return {"result_json": result_file}
        except Exception as e:
            self.logger.error(f"Failed to save stress result {result.stress_id}: {str(e)}")
            raise StressStorageError(f"Save failed: {str(e)}")

    def load_result(self, stress_id: str) -> StressTestResult | None:
        results_dir = self.base_path / "results"
        if not results_dir.exists():
            return None

        for date_dir in results_dir.iterdir():
            if not date_dir.is_dir():
                continue
            target_dir = date_dir / stress_id
            if target_dir.exists():
                json_file = target_dir / "stress_result.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        return StressTestResult(**data)
                    except Exception as e:
                        self.logger.error(f"Failed to load stress result {stress_id}: {str(e)}")
                        return None
        return None

    def load_latest_result(self) -> StressTestResult | None:
        results_dir = self.base_path / "results"
        if not results_dir.exists():
            return None

        date_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)
        if not date_dirs:
            return None

        latest_date_dir = date_dirs[0]
        result_dirs = sorted([d for d in latest_date_dir.iterdir() if d.is_dir()],
                             key=lambda x: x.stat().st_mtime, reverse=True)

        if not result_dirs:
            return None

        json_file = result_dirs[0] / "stress_result.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return StressTestResult(**data)
            except Exception as e:
                self.logger.error(f"Failed to load latest stress result: {str(e)}")
        return None

    def list_recent_results(self, limit: int = 20) -> list[dict[str, Any]]:
        results_dir = self.base_path / "results"
        if not results_dir.exists():
            return []

        all_results = []
        for date_dir in sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True):
            for result_dir in sorted([d for d in date_dir.iterdir() if d.is_dir()],
                                     key=lambda x: x.stat().st_mtime, reverse=True):
                json_file = result_dir / "stress_result.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            all_results.append({
                                "stress_id": data.get("stress_id"),
                                "rating": data.get("stress_rating"),
                                "status": data.get("status"),
                                "timestamp": result_dir.stat().st_mtime
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to parse or load recent stress result from {json_file}: {str(e)}")

                if len(all_results) >= limit:
                    return all_results

        return all_results
