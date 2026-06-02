from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime, timedelta
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus

class SyntheticMacroGenerator:
    def default_indicators(self) -> list[str]:
        return ["policy_rate", "inflation", "usdtry", "cds_proxy", "global_risk_proxy"]

    def generate_indicator(self, indicator: str, dates: list[str], spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        r = random.Random(spec.seed + hash(indicator))
        val = 10.0
        rows = []
        for d in dates:
            val += r.uniform(-0.1, 0.1)
            rows.append({"date": d, "indicator": indicator, "value": round(val, 2)})
        return rows

    def generate_macro(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        start = datetime.strptime(spec.start_date, "%Y-%m-%d")
        end = datetime.strptime(spec.end_date, "%Y-%m-%d")
        dates = []
        curr = start
        while curr <= end:
            if curr.weekday() < 5: dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        all_rows = []
        for ind in self.default_indicators():
            all_rows.extend(self.generate_indicator(ind, dates, spec))

        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.MACRO,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=3,
            columns=["date", "indicator", "value"],
            status=SyntheticScenarioStatus.GENERATED
        )
