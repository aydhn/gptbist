from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticEventGenerator:
    def default_event_types(self) -> list[str]:
        return ["earnings", "dividend", "capital_increase", "index_rebalance", "macro_event", "custom_notice"]

    def event_severity(self, kind: SyntheticScenarioKind, index: int) -> str:
        if kind == SyntheticScenarioKind.EVENT_SHOCK: return "HIGH"
        return "MEDIUM"

    def generate_events(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        r = random.Random(spec.seed)
        all_rows = []
        for sym in spec.symbols:
            for _ in range(r.randint(1, 5)):
                all_rows.append({
                    "date": spec.start_date, # simplified
                    "symbol": sym,
                    "event_type": r.choice(self.default_event_types()),
                    "severity": self.event_severity(spec.kind, 0)
                })

        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.EVENTS,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=4,
            columns=["date", "symbol", "event_type", "severity"],
            status=SyntheticScenarioStatus.GENERATED
        )
