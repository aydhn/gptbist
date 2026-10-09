import pandas as pd
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from bist_signal_bot.core.exceptions import TimeSeriesSplitError
from datetime import datetime, timedelta
import uuid

from bist_signal_bot.validation.models import ValidationSplit, ValidationSplitType

class ValidationSplitBuilder:
    def build_rolling_splits(
        self, start: datetime, end: datetime, train_window_days: int,
        test_window_days: int, step_days: int, purge_days: int = 0, embargo_days: int = 0
    ) -> List[ValidationSplit]:
        splits = []
        current_train_start = start
        fold_index = 1

        while True:
            current_train_end = current_train_start + timedelta(days=train_window_days)
            current_test_start = current_train_end
            current_test_end = current_test_start + timedelta(days=test_window_days)

            if current_test_end > end:
                break

            split = ValidationSplit(
                split_id=f"ROLLING_{fold_index}_{uuid.uuid4().hex[:8]}",
                split_type=ValidationSplitType.ROLLING,
                train_start=current_train_start,
                train_end=current_train_end,
                test_start=current_test_start,
                test_end=current_test_end,
                purge_days=purge_days,
                embargo_days=embargo_days,
                fold_index=fold_index
            )
            splits.append(self.apply_embargo(split))
            current_train_start += timedelta(days=step_days)
            fold_index += 1
        return splits

    def build_anchored_splits(self, *args, **kwargs) -> List[ValidationSplit]:
        return []

    def build_expanding_splits(self, *args, **kwargs) -> List[ValidationSplit]:
        return []

    def build_purged_kfold_splits(
        self, dates: List[datetime], folds: int, purge_days: int, embargo_days: int
    ) -> List[ValidationSplit]:
        if not dates or folds < 2: return []
        dates = sorted(dates)
        start = dates[0]
        end = dates[-1]
        total_days = (end - start).days
        fold_size = total_days // folds
        splits = []
        for i in range(folds):
            test_start = start + timedelta(days=i * fold_size)
            test_end = test_start + timedelta(days=fold_size) if i < folds - 1 else end
            split = ValidationSplit(
                split_id=f"PURGED_CV_{i+1}_{uuid.uuid4().hex[:8]}",
                split_type=ValidationSplitType.PURGED_K_FOLD,
                train_start=start, train_end=test_start if test_start > start else start + timedelta(days=1),
                test_start=test_start, test_end=test_end,
                purge_days=purge_days, embargo_days=embargo_days, fold_index=i+1
            )
            splits.append(self.apply_embargo(split))
        return splits

    def validate_no_overlap(self, splits: List[ValidationSplit]) -> List[str]:
        warnings = []
        for split in splits:
            eff_test_start = split.test_start
            eff_train_end = split.train_end - timedelta(days=split.purge_days)
            if eff_train_end > eff_test_start:
                warnings.append(f"Leakage warning in fold {split.fold_index}")
        return warnings

    def apply_embargo(self, split: ValidationSplit) -> ValidationSplit:
        return split


class TimeSeriesSplit(BaseModel):
    """Row-based train/test split used by walk-forward optimisation."""
    split_id: int
    train_start: Any
    train_end: Any
    test_start: Any
    test_end: Any
    train_rows: int = 0
    test_rows: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
