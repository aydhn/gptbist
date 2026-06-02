from datetime import timezone
from typing import Any

import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus

class SyntheticFinancialsGenerator:
    def quarter_periods(self, start_date: str, end_date: str) -> list[str]:
        # Simple quarterly logic
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        periods = []
        for y in range(start_year, end_year + 1):
            periods.extend([f"{y}Q1", f"{y}Q2", f"{y}Q3", f"{y}Q4"])
        return periods

    def generate_symbol_financials(self, symbol: str, spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        periods = self.quarter_periods(spec.start_date, spec.end_date)
        r = random.Random(spec.seed + hash(symbol))
        rows = []
        for p in periods:
            rows.append({
                "symbol": symbol,
                "period": p,
                "revenue": round(r.uniform(1000, 5000), 2),
                "net_income": round(r.uniform(100, 500), 2),
                "equity": round(r.uniform(2000, 10000), 2),
                "assets": round(r.uniform(5000, 20000), 2),
                "liabilities": round(r.uniform(3000, 10000), 2),
                "operating_cash_flow": round(r.uniform(200, 800), 2)
            })
        return rows

    def generate_financials(self, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        all_rows = []
        for sym in spec.symbols:
            all_rows.extend(self.generate_symbol_financials(sym, spec))

        cols = ["symbol", "period", "revenue", "net_income", "equity", "assets", "liabilities", "operating_cash_flow"]
        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.FINANCIALS,
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
