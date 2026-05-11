import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_ml_feature_store_dir
from bist_signal_bot.ml.models import MLDatasetResult, MLDatasetSchema, FeatureStoreFormat
from bist_signal_bot.core.exceptions import MLFeatureStoreError

logger = logging.getLogger(__name__)

class FeatureStore:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_ml_feature_store_dir(settings)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_feature_store_dir(self) -> Path:
        return self.base_dir

    def create_dataset_dir(self, result: MLDatasetResult) -> Path:
        date_str = result.started_at.strftime("%Y%m%d")
        # generate a somewhat unique ID based on timestamp and symbols
        ds_id = f"{result.started_at.strftime('%H%M%S')}_{len(result.request.symbols)}"
        dataset_dir = self.base_dir / date_str / ds_id
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir

    def save_dataset(self, result: MLDatasetResult, formats: list[FeatureStoreFormat] | None = None, output_dir: Path | None = None) -> dict[str, Path]:
        if result.data is None or result.data.empty:
            raise MLFeatureStoreError("Cannot save empty dataset.")

        if output_dir is None:
            output_dir = self.create_dataset_dir(result)

        if not formats:
            formats = result.request.formats

        output_files = {}

        try:
            self.save_schema(result.schema_, output_dir)
            self.save_summary(result, output_dir)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

        for fmt in formats:
            if fmt == FeatureStoreFormat.CSV:
                csv_path = output_dir / "dataset.csv"
                result.data.to_csv(csv_path, index=False, encoding="utf-8")
                output_files["dataset.csv"] = str(csv_path)

                if result.train_data is not None and not result.train_data.empty:
                    train_path = output_dir / "train.csv"
                    result.train_data.to_csv(train_path, index=False, encoding="utf-8")
                    output_files["train.csv"] = str(train_path)

                if result.test_data is not None and not result.test_data.empty:
                    test_path = output_dir / "test.csv"
                    result.test_data.to_csv(test_path, index=False, encoding="utf-8")
                    output_files["test.csv"] = str(test_path)

            elif fmt == FeatureStoreFormat.PARQUET:
                try:
                    pq_path = output_dir / "dataset.parquet"
                    result.data.to_parquet(pq_path, index=False)
                    output_files["dataset.parquet"] = str(pq_path)

                    if result.train_data is not None and not result.train_data.empty:
                        train_path = output_dir / "train.parquet"
                        result.train_data.to_parquet(train_path, index=False)
                        output_files["train.parquet"] = str(train_path)

                    if result.test_data is not None and not result.test_data.empty:
                        test_path = output_dir / "test.parquet"
                        result.test_data.to_parquet(test_path, index=False)
                        output_files["test.parquet"] = str(test_path)
                except Exception as e:
                    logger.warning(f"Failed to save Parquet (maybe pyarrow/fastparquet missing?): {e}. Falling back to CSV.")
                    result.issues.append(f"Parquet save failed: {e}")
                    if FeatureStoreFormat.CSV not in formats:
                        # force fallback
                        csv_path = output_dir / "dataset.csv"
                        result.data.to_csv(csv_path, index=False, encoding="utf-8")
                        output_files["dataset.csv"] = str(csv_path)

            elif fmt == FeatureStoreFormat.JSON:
                json_path = output_dir / "dataset.json"
                result.data.to_json(json_path, orient="records")
                output_files["dataset.json"] = str(json_path)

        result.output_files = output_files
        return output_files

    def save_schema(self, schema: MLDatasetSchema, output_dir: Path) -> Path:
        schema_path = output_dir / "dataset_schema.json"

        data_dict = {
            "symbol_col": schema.symbol_col,
            "timestamp_col": schema.timestamp_col,
            "feature_cols": schema.feature_cols,
            "label_cols": schema.label_cols,
            "target_col": schema.target_col,
            "metadata_cols": schema.metadata_cols,
            "excluded_cols": schema.excluded_cols,
            "generated_at": schema.generated_at.isoformat() if schema.generated_at else None,
            "metadata": schema.metadata
        }

        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4)
        return schema_path

    def save_summary(self, result: MLDatasetResult, output_dir: Path) -> Path:
        summary_path = output_dir / "dataset_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(result.summary(), f, indent=4)
        return summary_path

    def load_dataset(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise MLFeatureStoreError(f"Dataset path not found: {path}")

        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        elif path.suffix == ".csv":
            return pd.read_csv(path)
        elif path.suffix == ".json":
            return pd.read_json(path, orient="records")
        else:
            raise MLFeatureStoreError(f"Unsupported file format: {path.suffix}")

    def list_recent_datasets(self, limit: int = 20) -> list[dict[str, Any]]:
        datasets = []
        if not self.base_dir.exists():
            return datasets

        for date_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            for ds_dir in sorted(date_dir.iterdir(), reverse=True):
                if not ds_dir.is_dir():
                    continue

                summary_file = ds_dir / "dataset_summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, "r", encoding="utf-8") as f:
                            summary = json.load(f)
                            summary["id"] = f"{date_dir.name}/{ds_dir.name}"
                            datasets.append(summary)
                            if len(datasets) >= limit:
                                return datasets
                    except Exception:
                        pass
        return datasets
