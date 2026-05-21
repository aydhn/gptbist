import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
import pandas as pd

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_drift_dir
from bist_signal_bot.drift.models import (
    DriftAnalysisResult, FeatureDriftResult, CalibrationReport
)
from bist_signal_bot.core.exceptions import DriftStorageError

logger = logging.getLogger(__name__)

class DriftStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_drift_dir(self.settings)

    def save_result(self, result: DriftAnalysisResult) -> dict[str, Path]:
        try:
            date_str = result.generated_at.strftime("%Y%m%d")
            out_dir = self.base_dir / "results" / date_str / result.drift_id
            out_dir.mkdir(parents=True, exist_ok=True)

            paths = {}

            json_path = out_dir / "drift_result.json"
            with open(json_path, "w") as f:
                json.dump(result.model_dump(mode='json'), f, indent=2)
            paths["json"] = json_path

            if result.feature_results:
                csv_path = self.save_feature_results(result.feature_results, out_dir)
                paths["feature_csv"] = csv_path

            if result.calibration_reports:
                cal_path = self.save_calibration_reports(result.calibration_reports, out_dir)
                paths["calibration_json"] = cal_path

            return paths
        except Exception as e:
            logger.error(f"Failed to save drift result {result.drift_id}: {e}")
            raise DriftStorageError(f"Failed to save drift result: {e}")

    def load_result(self, drift_id: str) -> DriftAnalysisResult | None:
        try:
            results_dir = self.base_dir / "results"
            if not results_dir.exists():
                return None

            for date_dir in results_dir.iterdir():
                if date_dir.is_dir():
                    target_dir = date_dir / drift_id
                    if target_dir.exists():
                        json_path = target_dir / "drift_result.json"
                        if json_path.exists():
                            with open(json_path, "r") as f:
                                data = json.load(f)
                            return DriftAnalysisResult(**data)
            return None
        except Exception as e:
            logger.error(f"Failed to load drift result {drift_id}: {e}")
            raise DriftStorageError(f"Failed to load drift result: {e}")

    def load_latest_result(self) -> DriftAnalysisResult | None:
        try:
            results = self.list_recent_results(limit=1)
            if results:
                return self.load_result(results[0]["drift_id"])
            return None
        except Exception as e:
            logger.error(f"Failed to load latest drift result: {e}")
            return None

    def list_recent_results(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            results_dir = self.base_dir / "results"
            if not results_dir.exists():
                return []

            all_runs = []
            for date_dir in sorted(results_dir.iterdir(), reverse=True):
                if date_dir.is_dir():
                    for id_dir in date_dir.iterdir():
                        if id_dir.is_dir():
                            json_path = id_dir / "drift_result.json"
                            if json_path.exists():
                                try:
                                    with open(json_path, "r") as f:
                                        data = json.load(f)
                                        all_runs.append({
                                            "drift_id": data.get("drift_id"),
                                            "generated_at": data.get("generated_at"),
                                            "status": data.get("status"),
                                            "severity": data.get("severity")
                                        })
                                except Exception:
                                    pass

            all_runs.sort(key=lambda x: x["generated_at"] if x["generated_at"] else "", reverse=True)
            return all_runs[:limit]
        except Exception as e:
            logger.error(f"Failed to list recent results: {e}")
            return []

    def save_feature_results(self, results: list[FeatureDriftResult], output_dir: Path) -> Path:
        rows = []
        for r in results:
            row = {
                "feature_name": r.feature_name,
                "status": r.status.value,
                "severity": r.severity.value
            }
            for m in r.metrics:
                row[f"{m.metric_name}_value"] = m.value
            rows.append(row)

        df = pd.DataFrame(rows)
        path = output_dir / "feature_drift.csv"
        df.to_csv(path, index=False)
        return path

    def save_calibration_reports(self, reports: list[CalibrationReport], output_dir: Path) -> Path:
        path = output_dir / "calibration.json"
        with open(path, "w") as f:
            json.dump([r.model_dump(mode='json') for r in reports], f, indent=2)
        return path
