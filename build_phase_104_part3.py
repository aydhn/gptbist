import os
from pathlib import Path

def ensure_file(path, content, append=False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if append and os.path.exists(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

# 11. FINANCIALS
fin_code = """
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
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/financials.py", fin_code)

# 12. EVENTS
evt_code = """
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
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=4,
            columns=["date", "symbol", "event_type", "severity"],
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/events.py", evt_code)

# 13. DISCLOSURES
disc_code = """
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
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=4,
            columns=["date", "symbol", "text", "risk_score"],
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/disclosures.py", disc_code)

# 14. FEATURES
feat_code = """
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
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/features.py", feat_code)

# 15. MODELS FIXTURE
modfix_code = """
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
            created_at=datetime.utcnow(),
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
            created_at=datetime.utcnow(),
            rows=rows,
            row_count=len(rows),
            column_count=2,
            columns=["bucket", "accuracy"],
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/models_fixture.py", modfix_code)
