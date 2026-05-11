import pandas as pd
from bist_signal_bot.core.exceptions import MLTrainingValidationError

class MLTimeSeriesSplitter:
    def train_test_split(self, data: pd.DataFrame, train_ratio: float, timestamp_col: str | None = "timestamp") -> tuple[pd.DataFrame, pd.DataFrame]:
        if data.empty or len(data) < 2:
            raise MLTrainingValidationError("Dataset too small for train/test split")

        if timestamp_col and timestamp_col in data.columns:
            df = data.sort_values(by=timestamp_col)
        else:
            df = data.copy()

        split_idx = int(len(df) * train_ratio)
        if split_idx == 0 or split_idx == len(df):
            raise MLTrainingValidationError("Train ratio results in empty train or test set")

        train = df.iloc[:split_idx].copy()
        test = df.iloc[split_idx:].copy()
        return train, test

    def limit_train_rows(self, train: pd.DataFrame, max_train_rows: int | None) -> pd.DataFrame:
        if max_train_rows and max_train_rows > 0 and len(train) > max_train_rows:
            return train.iloc[-max_train_rows:].copy()
        return train

    def validate_temporal_order(self, train: pd.DataFrame, test: pd.DataFrame, timestamp_col: str | None = "timestamp") -> None:
        if not timestamp_col or timestamp_col not in train.columns or timestamp_col not in test.columns:
            return

        max_train_time = train[timestamp_col].max()
        min_test_time = test[timestamp_col].min()

        if pd.notna(max_train_time) and pd.notna(min_test_time):
            if max_train_time > min_test_time:
                raise MLTrainingValidationError(f"Temporal order violation: max train time ({max_train_time}) > min test time ({min_test_time})")

    def split_features_target(self, data: pd.DataFrame, feature_cols: list[str], target_col: str) -> tuple[pd.DataFrame, pd.Series]:
        if target_col not in data.columns:
            raise MLTrainingValidationError(f"Target column {target_col} not found in dataset")

        missing_features = [col for col in feature_cols if col not in data.columns]
        if missing_features:
            raise MLTrainingValidationError(f"Missing feature columns: {missing_features}")

        X = data[feature_cols].copy()
        y = data[target_col].copy()
        return X, y
