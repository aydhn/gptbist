from datetime import timezone

from datetime import datetime, timedelta
import random
import uuid
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioGeneratorConfig

class SyntheticScenarioGenerator:
    def __init__(self, config: SyntheticScenarioGeneratorConfig):
        self.ohlcv_gen = config.ohlcv_gen
        self.macro_gen = config.macro_gen
        self.breadth_gen = config.breadth_gen
        self.fin_gen = config.fin_gen
        self.evt_gen = config.evt_gen
        self.disc_gen = config.disc_gen
        self.feature_gen = config.feature_gen
        self.model_fix_gen = config.model_fix_gen
        self.port_gen = config.port_gen
        self.stress_bld = config.stress_bld
        self.edge_fac = config.edge_fac

    def date_index(self, spec: SyntheticScenarioSpec) -> list[str]:
        start = datetime.strptime(spec.start_date, "%Y-%m-%d")
        end = datetime.strptime(spec.end_date, "%Y-%m-%d")
        dates = []
        curr = start
        while curr <= end:
            if curr.weekday() < 5:
                dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)
        return dates

    def rng(self, spec: SyntheticScenarioSpec):
        r = random.Random(spec.seed)
        return r

    def generate_output(self, spec: SyntheticScenarioSpec, output_kind: SyntheticOutputKind) -> SyntheticDataset:
        if output_kind == SyntheticOutputKind.OHLCV:
            return self.ohlcv_gen.generate_ohlcv(spec, adjusted=False)
        elif output_kind == SyntheticOutputKind.ADJUSTED_OHLCV:
            return self.ohlcv_gen.generate_ohlcv(spec, adjusted=True)
        elif output_kind == SyntheticOutputKind.MACRO:
            return self.macro_gen.generate_macro(spec)
        elif output_kind == SyntheticOutputKind.BREADTH:
            return self.breadth_gen.generate_breadth(spec)
        elif output_kind == SyntheticOutputKind.FINANCIALS:
            return self.fin_gen.generate_financials(spec)
        elif output_kind == SyntheticOutputKind.EVENTS:
            return self.evt_gen.generate_events(spec)
        elif output_kind == SyntheticOutputKind.DISCLOSURES:
            return self.disc_gen.generate_disclosures(spec)
        elif output_kind == SyntheticOutputKind.FEATURE_FRAME:
            return self.feature_gen.generate_feature_frame(spec)
        elif output_kind == SyntheticOutputKind.MODEL_PREDICTIONS:
            return self.model_fix_gen.generate_model_predictions(spec)
        elif output_kind == SyntheticOutputKind.CALIBRATION_OUTCOMES:
            return self.model_fix_gen.generate_calibration_outcomes(spec)
        elif output_kind == SyntheticOutputKind.PORTFOLIO_OUTCOMES:
            return self.port_gen.generate_portfolio_outcomes(spec)

        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=output_kind,
            created_at=datetime.now(timezone.utc),
            rows=[],
            row_count=0,
            column_count=0,
            columns=[],
            status=SyntheticScenarioStatus.GENERATED
        )

    def generate(self, spec: SyntheticScenarioSpec) -> list[SyntheticDataset]:
        datasets = []
        for ok in spec.output_kinds:
            ds = self.generate_output(spec, ok)
            ds = self.apply_scenario_effects(ds, spec)
            datasets.append(ds)
        return datasets

    def apply_scenario_effects(self, dataset: SyntheticDataset, spec: SyntheticScenarioSpec) -> SyntheticDataset:
        edges = self.edge_fac.default_edge_cases(spec)
        for ec in edges:
             dataset = self.edge_fac.apply_edge_case(dataset, ec)
        return dataset

    def generate_all_default(self) -> list[SyntheticDataset]:
        return []
