from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticPortfolioOutcomeGenerator:
    def synthetic_return(self, kind: SyntheticScenarioKind, index: int, seed: int) -> float:
        r = random.Random(seed + index)
        if kind == SyntheticScenarioKind.CRASH: return r.uniform(-0.10, -0.05)
        return r.uniform(-0.02, 0.02)

    def generate_ledger_rows(self, spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        rows = []
        for sym in spec.symbols:
             rows.append({"date": spec.start_date, "symbol": sym, "return": self.synthetic_return(spec.kind, 0, spec.seed)})
        return rows

    def generate_portfolio_outcomes(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        rows = self.generate_ledger_rows(spec)
        cols = ["date", "symbol", "return"]
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.PORTFOLIO_OUTCOMES,
            created_at=datetime.now(timezone.utc),
            rows=rows,
            row_count=len(rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
