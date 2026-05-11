import pandas as pd
from typing import Any
from datetime import datetime, timezone
from bist_signal_bot.ml.models import MLDatasetSchema, FeatureConfig, LabelConfig
from bist_signal_bot.core.exceptions import MLSchemaError

class MLSchemaBuilder:
    def build_schema(self, data: pd.DataFrame, feature_config: FeatureConfig, label_config: LabelConfig) -> MLDatasetSchema:
        feature_cols = [c for c in data.columns if c.startswith("feat_")]

        # If there are indicators without feat_ prefix but they aren't labels or metadata
        if not feature_cols:
            exclude = ["symbol", "timestamp", "timeframe", "open", "high", "low", "close", "volume"]
            feature_cols = [c for c in data.columns if not c.startswith("label_") and not c.startswith("target_") and c not in exclude]

        label_cols = self.identify_label_columns(data)
        metadata_cols = self.identify_metadata_columns(data)

        excluded_cols = [c for c in data.columns if c not in feature_cols and c not in label_cols and c not in metadata_cols]

        if not feature_cols:
            raise MLSchemaError("No feature columns identified in dataset.")

        if not label_cols:
            raise MLSchemaError("No label columns identified in dataset.")

        intersection = set(feature_cols).intersection(set(label_cols))
        if intersection:
            raise MLSchemaError(f"Overlap between features and labels: {intersection}")

        schema = MLDatasetSchema(
            symbol_col="symbol",
            timestamp_col="timestamp",
            feature_cols=feature_cols,
            label_cols=label_cols,
            target_col=label_cols[0] if label_cols else None,
            metadata_cols=metadata_cols,
            excluded_cols=excluded_cols,
            generated_at=datetime.now(timezone.utc),
            metadata={}
        )
        self.validate_schema(data, schema)
        return schema

    def identify_label_columns(self, data: pd.DataFrame) -> list[str]:
        return [c for c in data.columns if c.startswith("label_")]

    def identify_metadata_columns(self, data: pd.DataFrame) -> list[str]:
        meta = []
        if "symbol" in data.columns:
            meta.append("symbol")
        if "timestamp" in data.columns:
            meta.append("timestamp")
        if "timeframe" in data.columns:
            meta.append("timeframe")
        return meta

    def validate_schema(self, data: pd.DataFrame, schema: MLDatasetSchema) -> None:
        if not schema.feature_cols:
            raise MLSchemaError("Schema validation failed: feature_cols is empty.")
        if not schema.label_cols:
            raise MLSchemaError("Schema validation failed: label_cols is empty.")

    def schema_to_json_dict(self, schema: MLDatasetSchema) -> dict[str, Any]:
        return {
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
