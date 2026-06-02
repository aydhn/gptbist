from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticDisclosureGenerator:
    def disclosure_text(self, symbol: str, kind: SyntheticScenarioKind, index: int) -> str:
        return f"Synthetic disclosure for {symbol} regarding scenario {kind.value}"

    def disclosure_risk_score(self, kind: SyntheticScenarioKind, index: int) -> float:
        if kind == SyntheticScenarioKind.CRASH: return 0.9
        return 0.1

    def generate_disclosures(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        r = random.Random(spec.seed)
        all_rows = []
        for sym in spec.symbols:
            all_rows.append({
                "date": spec.start_date,
                "symbol": sym,
                "text": self.disclosure_text(sym, spec.kind, 0),
                "risk_score": self.disclosure_risk_score(spec.kind, 0)
            })

        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.DISCLOSURES,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=4,
            columns=["date", "symbol", "text", "risk_score"],
            status=SyntheticScenarioStatus.GENERATED
        )
