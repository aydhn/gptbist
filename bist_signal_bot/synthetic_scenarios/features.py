from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus

class SyntheticFeatureFrameGenerator:
    def default_feature_names(self) -> list[str]:
        return ["close_return_1d", "close_return_5d", "momentum_20d", "volatility_20d", "volume_zscore_20d", "liquidity_score", "breadth_score", "macro_pressure_score"]

    def feature_rows_from_ohlcv(self, ohlcv: SyntheticDataset, spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        # Mock logic
        return ohlcv.rows.copy()

    def generate_feature_frame(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        r = random.Random(spec.seed)
        all_rows = []
        for sym in spec.symbols:
             all_rows.append({"date": spec.start_date, "symbol": sym, "close_return_1d": r.uniform(-0.05, 0.05)})

        cols = ["date", "symbol", "close_return_1d"]
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.FEATURE_FRAME,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
