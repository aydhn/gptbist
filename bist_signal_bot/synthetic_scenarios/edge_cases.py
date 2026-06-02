from typing import Any

import uuid
import random
from .models import SyntheticScenarioSpec, SyntheticEdgeCase, SyntheticDataset

class SyntheticEdgeCaseFactory:
    def default_edge_cases(self, spec: SyntheticScenarioSpec) -> list[SyntheticEdgeCase]:
        return [
            self.missing_required_column_case(spec),
            self.duplicate_rows_case(spec),
            self.invalid_date_case(spec),
            self.outlier_case(spec),
            self.stale_data_case(spec)
        ]

    def missing_required_column_case(self, spec: SyntheticScenarioSpec) -> SyntheticEdgeCase:
        return SyntheticEdgeCase(str(uuid.uuid4()), spec.scenario_id, "Missing Column", "Removes a column", "OHLCV", "FAIL", ["remove_high"])

    def duplicate_rows_case(self, spec: SyntheticScenarioSpec) -> SyntheticEdgeCase:
        return SyntheticEdgeCase(str(uuid.uuid4()), spec.scenario_id, "Duplicate Rows", "Duplicates rows", "OHLCV", "PASS", ["duplicate_first"])

    def invalid_date_case(self, spec: SyntheticScenarioSpec) -> SyntheticEdgeCase:
        return SyntheticEdgeCase(str(uuid.uuid4()), spec.scenario_id, "Invalid Date", "Invalid date format", "OHLCV", "FAIL", ["bad_date"])

    def outlier_case(self, spec: SyntheticScenarioSpec) -> SyntheticEdgeCase:
        return SyntheticEdgeCase(str(uuid.uuid4()), spec.scenario_id, "Outlier", "Adds outlier", "OHLCV", "PASS", ["extreme_price"])

    def stale_data_case(self, spec: SyntheticScenarioSpec) -> SyntheticEdgeCase:
        return SyntheticEdgeCase(str(uuid.uuid4()), spec.scenario_id, "Stale Data", "Repeats last price", "OHLCV", "PASS", ["repeat_price"])

    def apply_edge_case(self, dataset: SyntheticDataset, edge_case: SyntheticEdgeCase) -> SyntheticDataset:
        # Mock logic, returns dataset unmodified for now
        return dataset
