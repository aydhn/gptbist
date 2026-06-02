from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime, timedelta
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticBreadthGenerator:
    def breadth_score(self, kind: SyntheticScenarioKind, index: int, n: int) -> float:
        if kind == SyntheticScenarioKind.TREND_UP: return 80.0
        if kind == SyntheticScenarioKind.TREND_DOWN: return 20.0
        return 50.0

    def advance_decline_series(self, dates: list[str], spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        rows = []
        for i, d in enumerate(dates):
            rows.append({
                "date": d,
                "breadth_score": self.breadth_score(spec.kind, i, len(dates)),
                "advances": 200,
                "declines": 100
            })
        return rows

    def generate_breadth(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        start = datetime.strptime(spec.start_date, "%Y-%m-%d")
        end = datetime.strptime(spec.end_date, "%Y-%m-%d")
        dates = []
        curr = start
        while curr <= end:
            if curr.weekday() < 5: dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        rows = self.advance_decline_series(dates, spec)
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.BREADTH,
            created_at=datetime.now(timezone.utc),
            rows=rows,
            row_count=len(rows),
            column_count=4,
            columns=["date", "breadth_score", "advances", "declines"],
            status=SyntheticScenarioStatus.GENERATED
        )
