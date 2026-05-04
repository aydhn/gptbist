import pandas as pd

from bist_signal_bot.core.exceptions import TimeSeriesSplitError
from bist_signal_bot.validation.models import TimeSeriesSplit


class TimeSeriesSplitGenerator:
    @staticmethod
    def train_test_split(
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        min_train_rows: int = 100,
        min_test_rows: int = 30,
        gap_rows: int = 0,
    ) -> TimeSeriesSplit:
        if data.empty:
            raise TimeSeriesSplitError("Data is empty")

        total_rows = len(data)
        train_rows = int(total_rows * train_ratio)
        test_rows = total_rows - train_rows - gap_rows

        if train_rows < min_train_rows:
            raise TimeSeriesSplitError(
                f"Insufficient data for train split. Need {min_train_rows}, got {train_rows}"
            )
        if test_rows < min_test_rows:
            raise TimeSeriesSplitError(
                f"Insufficient data for test split. Need {min_test_rows}, got {test_rows}"
            )

        train_end_idx = train_rows
        test_start_idx = train_rows + gap_rows

        train_start = data.index[0]
        train_end = data.index[train_end_idx - 1]
        test_start = data.index[test_start_idx]
        test_end = data.index[-1]

        return TimeSeriesSplit(
            split_id=1,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            train_rows=train_rows,
            test_rows=test_rows,
            metadata={"train_ratio": train_ratio, "gap_rows": gap_rows, "type": "HOLDOUT"},
        )

    @staticmethod
    def walk_forward_splits(
        data: pd.DataFrame,
        train_window_rows: int,
        test_window_rows: int,
        step_rows: int,
        gap_rows: int = 0,
        expanding: bool = False,
        max_splits: int | None = None,
    ) -> list[TimeSeriesSplit]:
        if data.empty:
            raise TimeSeriesSplitError("Data is empty")

        total_rows = len(data)
        min_required_rows = train_window_rows + gap_rows + test_window_rows

        if total_rows < min_required_rows:
            raise TimeSeriesSplitError(
                f"Insufficient data for walk-forward. Need at least {min_required_rows}, got {total_rows}"  # noqa: E501
            )

        splits = []
        train_start_idx = 0
        split_id = 1

        while True:
            train_end_idx = train_start_idx + train_window_rows
            if expanding:
                train_window_rows_current = train_end_idx - 0
                train_start_idx_current = 0
            else:
                train_window_rows_current = train_window_rows
                train_start_idx_current = train_start_idx

            test_start_idx = train_end_idx + gap_rows
            test_end_idx = test_start_idx + test_window_rows

            if test_end_idx > total_rows:
                break

            train_start = data.index[train_start_idx_current]
            train_end = data.index[train_end_idx - 1]
            test_start = data.index[test_start_idx]
            test_end = data.index[test_end_idx - 1]

            splits.append(
                TimeSeriesSplit(
                    split_id=split_id,
                    train_start=train_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                    train_rows=train_window_rows_current,
                    test_rows=test_window_rows,
                    metadata={"expanding": expanding, "gap_rows": gap_rows, "type": "WALK_FORWARD"},
                )
            )

            if max_splits is not None and split_id >= max_splits:
                break

            if not expanding:
                train_start_idx += step_rows
            else:
                train_window_rows += step_rows

            split_id += 1

        if not splits:
            raise TimeSeriesSplitError("Could not generate any splits with the given parameters")

        return splits

    @staticmethod
    def slice_split_data(
        data: pd.DataFrame, split: TimeSeriesSplit
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        train_data = data.loc[split.train_start : split.train_end]
        test_data = data.loc[split.test_start : split.test_end]
        return train_data, test_data
