import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_ml_training_dir
from bist_signal_bot.ml.training.models import MLTrainResult, MLPredictionResult
from bist_signal_bot.ml.training.reporting import format_ml_train_markdown, feature_importance_to_dataframe

logger = logging.getLogger(__name__)

class MLTrainingReportStore:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_ml_training_dir(settings)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_train_result(self, result: MLTrainResult, formats: list[str] | None = None) -> dict[str, Path]:
        if not formats:
            formats = [f.strip().lower() for f in self.settings.ML_TRAIN_REPORT_FORMATS.split(",")]

        date_str = result.started_at.strftime("%Y%m%d")
        run_id = f"train_{result.started_at.strftime('%H%M%S')}"

        run_dir = self.base_dir / date_str / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        output_files = {}

        if "json" in formats or "all" in formats:
            json_path = run_dir / "training_report.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json.loads(result.model_dump_json()), f, indent=2)
            output_files["json"] = json_path

        if "markdown" in formats or "md" in formats or "all" in formats:
            md_path = run_dir / "training_report.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(format_ml_train_markdown(result))
            output_files["markdown"] = md_path

        if "csv" in formats or "all" in formats:
            if result.feature_importance:
                csv_path = run_dir / "feature_importance.csv"
                df = feature_importance_to_dataframe(result.feature_importance)
                df.to_csv(csv_path, index=False)
                output_files["feature_importance_csv"] = csv_path

        return output_files

    def save_prediction_result(self, result: MLPredictionResult, formats: list[str] | None = None) -> dict[str, Path]:
        date_str = result.generated_at.strftime("%Y%m%d")
        run_id = f"predict_{result.generated_at.strftime('%H%M%S')}"

        run_dir = self.base_dir / date_str / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        output_files = {}

        json_path = run_dir / "prediction_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json.loads(result.model_dump_json()), f, indent=2)
        output_files["json"] = json_path

        if result.predictions:
            csv_path = run_dir / "predictions.csv"
            df = pd.DataFrame([p.model_dump() for p in result.predictions])
            df.to_csv(csv_path, index=False)
            output_files["csv"] = csv_path

        return output_files

    def list_recent_training_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        runs = []
        for date_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for run_dir in sorted(date_dir.iterdir(), reverse=True):
                if not run_dir.is_dir() or not run_dir.name.startswith("train_"):
                    continue

                json_path = run_dir / "training_report.json"
                if json_path.exists():
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            runs.append(json.load(f))
                    except Exception as e:
                        logger.warning(f"Failed to load report {json_path}: {e}")

                if len(runs) >= limit:
                    return runs
        return runs
