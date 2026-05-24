import pandas as pd
from typing import List
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
