from typing import Any

from .models import SyntheticScenarioSpec, SyntheticScenarioKind, SyntheticOutputKind, SyntheticFrequency

class SyntheticScenarioLibrary:
    def default_specs(self) -> list[SyntheticScenarioSpec]:
        base_outputs = [SyntheticOutputKind.OHLCV, SyntheticOutputKind.MACRO, SyntheticOutputKind.BREADTH]
        all_outputs = list(SyntheticOutputKind)

        return [
            SyntheticScenarioSpec("trend_up_basic_v1", "Trend Up Basic", SyntheticScenarioKind.TREND_UP, "Upward trend", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("trend_down_basic_v1", "Trend Down Basic", SyntheticScenarioKind.TREND_DOWN, "Downward trend", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("range_bound_basic_v1", "Range Bound Basic", SyntheticScenarioKind.RANGE_BOUND, "Range bound", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("high_volatility_v1", "High Volatility", SyntheticScenarioKind.HIGH_VOLATILITY, "High volatility", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("low_liquidity_v1", "Low Liquidity", SyntheticScenarioKind.LOW_LIQUIDITY, "Low liquidity", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("crash_rebound_v1", "Crash Rebound", SyntheticScenarioKind.CRASH, "Crash and rebound", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("gap_events_v1", "Gap Events", SyntheticScenarioKind.GAP_UP, "Gaps", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("stale_data_v1", "Stale Data", SyntheticScenarioKind.STALE_DATA, "Stale data simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("missing_data_v1", "Missing Data", SyntheticScenarioKind.MISSING_DATA, "Missing data simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("schema_drift_v1", "Schema Drift", SyntheticScenarioKind.SCHEMA_DRIFT, "Schema drift simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("macro_stress_v1", "Macro Stress", SyntheticScenarioKind.MACRO_STRESS, "Macro stress simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("mixed_regime_v1", "Mixed Regime", SyntheticScenarioKind.MIXED_REGIME, "Mixed regimes", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("full_pipeline_demo_v1", "Full Pipeline Demo", SyntheticScenarioKind.CUSTOM, "Full pipeline demo", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, all_outputs),
        ]

    def get_spec(self, scenario_id_or_name: str) -> SyntheticScenarioSpec | None:
        for spec in self.default_specs():
            if spec.scenario_id == scenario_id_or_name or spec.name == scenario_id_or_name:
                return spec
        return None

    def list_specs(self, kind: SyntheticScenarioKind | None = None) -> list[SyntheticScenarioSpec]:
        specs = self.default_specs()
        if kind:
            specs = [s for s in specs if s.kind == kind]
        return specs

    def validate_spec(self, spec: SyntheticScenarioSpec) -> list[str]:
        warnings = []
        if not spec.output_kinds:
            warnings.append("No output kinds specified.")
        return warnings

    def spec_summary(self, spec: SyntheticScenarioSpec) -> dict[str, 'Any']:
        return {
            "scenario_id": spec.scenario_id,
            "kind": spec.kind.value,
            "symbols": spec.symbols,
            "seed": spec.seed
        }
