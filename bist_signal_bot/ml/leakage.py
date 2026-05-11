import pandas as pd
from bist_signal_bot.ml.models import MLDatasetSchema, DatasetSplitMode
from bist_signal_bot.core.exceptions import MLLeakageError

class MLLeakageGuard:
    def validate_no_future_feature_columns(self, data: pd.DataFrame, feature_cols: list[str]) -> list[str]:
        leaky_keywords = ["future", "fwd", "forward", "label", "target", "next", "shifted_minus", "lead"]
        issues = []
        for col in feature_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in leaky_keywords):
                issues.append(f"Possible leakage in feature column: {col}")
        return issues

    def validate_label_not_in_features(self, feature_cols: list[str], label_cols: list[str]) -> None:
        intersection = set(feature_cols).intersection(set(label_cols))
        if intersection:
            raise MLLeakageError(f"CRITICAL LEAKAGE: Label columns found in feature_cols: {intersection}")

    def validate_time_order(self, data: pd.DataFrame, timestamp_col: str = "timestamp") -> None:
        if timestamp_col not in data.columns:
            return

        # check if it is sorted
        # in a multi-symbol dataframe, it should be sorted by timestamp then symbol, or symbol then timestamp.
        # we check if within each symbol, it is monotonically increasing
        if "symbol" in data.columns:
            for _, grp in data.groupby("symbol"):
                if not grp[timestamp_col].is_monotonic_increasing:
                    raise MLLeakageError("Time order is violated within a symbol's group.")
        else:
            if not data[timestamp_col].is_monotonic_increasing:
                raise MLLeakageError("Time order is violated. Timestamps must be monotonic increasing.")

    def validate_no_random_split(self, split_mode: DatasetSplitMode) -> None:
        pass # In our context random splits are not even supported in the Enum, so just a stub or sanity check

    def run_all_checks(self, data: pd.DataFrame, schema: MLDatasetSchema) -> list[str]:
        issues = []

        # 1. Label/Feature intersection
        self.validate_label_not_in_features(schema.feature_cols, schema.label_cols)

        # 2. Suspicious feature names
        suspicious = self.validate_no_future_feature_columns(data, schema.feature_cols)
        issues.extend(suspicious)

        # 3. Time ordering
        try:
            self.validate_time_order(data, schema.timestamp_col)
        except MLLeakageError as e:
            issues.append(f"Time Order Issue: {e}")

        return issues
