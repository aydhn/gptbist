from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticModelFixtureGenerator:
    def prediction_score(self, kind: SyntheticScenarioKind, index: int, seed: int) -> float:
        r = random.Random(seed + index)
        return r.uniform(0, 1)

    def calibration_bucket_rows(self, spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        return [{"bucket": i, "accuracy": 0.5 + i*0.05} for i in range(10)]

    def generate_model_predictions(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        r = random.Random(spec.seed)
        all_rows = []
        for sym in spec.symbols:
             all_rows.append({"date": spec.start_date, "symbol": sym, "score": self.prediction_score(spec.kind, 0, spec.seed)})

        cols = ["date", "symbol", "score"]
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.MODEL_PREDICTIONS,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )

    def generate_calibration_outcomes(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        rows = self.calibration_bucket_rows(spec)
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.CALIBRATION_OUTCOMES,
            created_at=datetime.now(timezone.utc),
            rows=rows,
            row_count=len(rows),
            column_count=2,
            columns=["bucket", "accuracy"],
            status=SyntheticScenarioStatus.GENERATED
        )
