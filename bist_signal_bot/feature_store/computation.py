from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import numpy as np
from bist_signal_bot.feature_store.models import FeatureValue, FeatureFrame, FeatureSet

class FeatureComputationEngine:
    def compute_feature(self, symbol: str, feature_name: str, as_of: datetime | None = None) -> FeatureValue:
        now = as_of or datetime.now(timezone.utc)
        return FeatureValue(
            value_id=f"val_{symbol}_{feature_name}_{now.timestamp()}",
            feature_name=feature_name,
            symbol=symbol,
            timestamp=now,
            as_of=now,
            value=0.0
        )

    def compute_feature_set(self, symbols: list[str], feature_set: FeatureSet | str, as_of: datetime | None = None, point_in_time: bool = True) -> FeatureFrame:
        now = as_of or datetime.now(timezone.utc)
        fs_id = feature_set.feature_set_id if isinstance(feature_set, FeatureSet) else feature_set
        return FeatureFrame(
            frame_id=f"frame_{fs_id}_{now.timestamp()}",
            feature_set_id=fs_id,
            symbols=symbols,
            as_of=now,
            row_count=0,
            column_count=0,
            point_in_time_safe=point_in_time
        )

    def compute_technical_features(self, symbol: str, as_of: datetime | None = None) -> list[FeatureValue]:
        return []

    def compute_context_features(self, symbol: str, as_of: datetime | None = None) -> list[FeatureValue]:
        return []

    def safe_pct_change(self, values: list[float], window: int) -> float | None:
        if len(values) <= window or window <= 0:
            return None
        start_val = values[-(window+1)]
        end_val = values[-1]
        if start_val == 0:
            return None
        return (end_val - start_val) / start_val

    def safe_rolling_std(self, values: list[float], window: int) -> float | None:
        if len(values) < window or window <= 1:
            return None
        return float(np.std(values[-window:], ddof=1))

    def safe_zscore(self, values: list[float], window: int) -> float | None:
        if len(values) < window or window <= 1:
            return None
        window_vals = values[-window:]
        mean = np.mean(window_vals)
        std = np.std(window_vals, ddof=1)
        if std == 0:
            return None
        return float((window_vals[-1] - mean) / std)

    def compute_hash(self, feature_name: str, inputs: dict[str, Any]) -> str:
        data = f"{feature_name}:{json.dumps(inputs, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()
