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

# 16. PORTFOLIO
port_code = """
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
            created_at=datetime.utcnow(),
            rows=rows,
            row_count=len(rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/portfolio.py", port_code)

# 17. STRESS
stress_code = """
import uuid
from .models import SyntheticScenarioSpec, SyntheticStressCase, SyntheticOutputKind

class SyntheticStressCaseBuilder:
    def default_stress_cases(self, spec: SyntheticScenarioSpec) -> list[SyntheticStressCase]:
        return [
            self.crash_stress(spec),
            self.liquidity_stress(spec),
            self.macro_stress(spec),
            self.schema_stress(spec)
        ]

    def crash_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Crash Stress",
            description="Market crash scenario",
            affected_outputs=[SyntheticOutputKind.OHLCV, SyntheticOutputKind.PORTFOLIO_OUTCOMES],
            severity="HIGH",
            parameters={"drop": -0.2},
            expected_findings=["High drawdown expected"]
        )

    def liquidity_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Liquidity Stress",
            description="Low liquidity scenario",
            affected_outputs=[SyntheticOutputKind.OHLCV],
            severity="MEDIUM",
            parameters={"volume_multiplier": 0.1},
            expected_findings=["Wide spreads expected"]
        )

    def macro_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Macro Stress",
            description="Macro shock scenario",
            affected_outputs=[SyntheticOutputKind.MACRO],
            severity="HIGH",
            parameters={"rate_shock": 0.05},
            expected_findings=["High volatility expected"]
        )

    def schema_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Schema Stress",
            description="Schema changes",
            affected_outputs=[SyntheticOutputKind.OHLCV],
            severity="LOW",
            parameters={"extra_cols": 2},
            expected_findings=["Should not crash"]
        )

    def expected_findings(self, case: SyntheticStressCase) -> list[str]:
        return case.expected_findings
"""
ensure_file("bist_signal_bot/synthetic_scenarios/stress.py", stress_code)

# 18. EDGE CASES
edge_code = """
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
"""
ensure_file("bist_signal_bot/synthetic_scenarios/edge_cases.py", edge_code)

# 19. MANIFEST
manifest_code = """
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioManifest

class SyntheticScenarioManifestBuilder:
    def dataset_refs(self, datasets: list[SyntheticDataset]) -> dict[str, str]:
        return {ds.dataset_id: ds.output_kind.value for ds in datasets}

    def row_counts(self, datasets: list[SyntheticDataset]) -> dict[str, int]:
        return {ds.dataset_id: ds.row_count for ds in datasets}

    def checksum_manifest(self, datasets: list[SyntheticDataset], output_paths: dict[str, str] | None = None) -> dict[str, str]:
        # Fake checksum for now
        return {ds.dataset_id: f"hash_{ds.dataset_id}" for ds in datasets}

    def validate_manifest(self, manifest: SyntheticScenarioManifest) -> list[str]:
        warnings = []
        if not manifest.dataset_refs: warnings.append("No datasets referenced")
        return warnings

    def build_manifest(self, spec: SyntheticScenarioSpec, datasets: list[SyntheticDataset], output_paths: dict[str, str] | None = None) -> SyntheticScenarioManifest:
        return SyntheticScenarioManifest(
            manifest_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            created_at=datetime.utcnow(),
            spec=spec,
            dataset_refs=self.dataset_refs(datasets),
            output_paths=output_paths or {},
            checksum_manifest=self.checksum_manifest(datasets, output_paths),
            row_counts=self.row_counts(datasets),
            validation_status="PENDING"
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/manifest.py", manifest_code)
