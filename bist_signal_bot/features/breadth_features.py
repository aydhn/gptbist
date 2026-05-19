import pandas as pd
from datetime import datetime
from typing import Any

from bist_signal_bot.breadth.engine import BreadthEngine

class BreadthFeatureBuilder:
    def __init__(self, engine: BreadthEngine | None = None):
        self.engine = engine

    def build_feature_row(self, symbol: str, as_of_date: datetime) -> dict[str, Any]:
        if not self.engine:
            return {}

        snapshot = self.engine.build_feature_snapshot(symbol, as_of_date)

        features = {}
        for k, v in snapshot.items():
            features[f"breadth_{k}"] = v

        return features

    def add_breadth_feature_columns(self, df: pd.DataFrame, symbol: str, date_col: str = "date") -> pd.DataFrame:
        if not self.engine or df.empty:
            return df

        df = df.copy()

        if date_col not in df.columns:
            return df

        new_cols = []
        for d in df[date_col]:
            row = self.build_feature_row(symbol, d)
            new_cols.append(row)

        if new_cols and any(new_cols):
            feat_df = pd.DataFrame(new_cols)
            for col in feat_df.columns:
                df[col] = feat_df[col]

        return df

    def available_feature_names(self) -> list[str]:
        return [
            "breadth_composite_score",
            "breadth_status_code",
            "breadth_risk_modifier",
            "breadth_percent_above_sma_20",
            "breadth_percent_above_sma_50",
            "breadth_percent_above_sma_200",
            "breadth_new_high_20_count",
            "breadth_new_low_20_count",
            "breadth_rs_score",
            "breadth_rs_percentile",
            "breadth_sector_rotation_rank",
            "breadth_sector_status_code",
            "breadth_cross_rank",
            "breadth_cross_percentile"
        ]
