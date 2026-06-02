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

# 7. GENERATOR
generator_code = """
from datetime import datetime, timedelta
import random
import uuid
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus

class SyntheticScenarioGenerator:
    def __init__(self, ohlcv_gen, macro_gen, breadth_gen, fin_gen, evt_gen, disc_gen, feature_gen, model_fix_gen, port_gen, stress_bld, edge_fac):
        self.ohlcv_gen = ohlcv_gen
        self.macro_gen = macro_gen
        self.breadth_gen = breadth_gen
        self.fin_gen = fin_gen
        self.evt_gen = evt_gen
        self.disc_gen = disc_gen
        self.feature_gen = feature_gen
        self.model_fix_gen = model_fix_gen
        self.port_gen = port_gen
        self.stress_bld = stress_bld
        self.edge_fac = edge_fac

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
            created_at=datetime.utcnow(),
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
"""
ensure_file("bist_signal_bot/synthetic_scenarios/generator.py", generator_code)

# 8. OHLCV
ohlcv_code = """
import random
import uuid
from datetime import datetime
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticOutputKind, SyntheticScenarioStatus, SyntheticScenarioKind

class SyntheticOHLCVGenerator:
    def price_path(self, start_price: float, n: int, kind: SyntheticScenarioKind, seed: int) -> list[float]:
        r = random.Random(seed)
        prices = [start_price]
        for _ in range(n-1):
            change = r.uniform(-0.02, 0.02)
            if kind == SyntheticScenarioKind.TREND_UP: change += 0.005
            elif kind == SyntheticScenarioKind.TREND_DOWN: change -= 0.005
            elif kind == SyntheticScenarioKind.CRASH: change -= 0.02

            p = max(0.01, prices[-1] * (1 + change))
            prices.append(round(p, 2))
        return prices

    def volume_path(self, n: int, kind: SyntheticScenarioKind, seed: int) -> list[int]:
        r = random.Random(seed)
        vols = []
        for _ in range(n):
            v = int(r.uniform(10000, 1000000))
            if kind == SyntheticScenarioKind.LOW_LIQUIDITY: v = int(v * 0.1)
            vols.append(v)
        return vols

    def generate_symbol_series(self, symbol: str, dates: list[str], spec: SyntheticScenarioSpec, adjusted: bool = False) -> list[dict[str, Any]]:
        r = random.Random(spec.seed + hash(symbol))
        prices = self.price_path(100.0, len(dates), spec.kind, spec.seed + hash(symbol))
        vols = self.volume_path(len(dates), spec.kind, spec.seed + hash(symbol))

        rows = []
        for i, d in enumerate(dates):
            p = prices[i]
            change_h = r.uniform(0, 0.03)
            change_l = r.uniform(0, 0.03)

            o = round(p * (1 + r.uniform(-0.01, 0.01)), 2)
            c = round(p, 2)
            h = round(max(o, c) * (1 + change_h), 2)
            l = round(min(o, c) * (1 - change_l), 2)

            row = {"date": d, "symbol": symbol, "open": o, "high": h, "low": l, "close": c, "volume": vols[i]}
            if adjusted:
                 row["adj_close"] = c
            rows.append(row)
        return rows

    def inject_gaps(self, rows: list[dict[str, Any]], spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        if spec.kind != SyntheticScenarioKind.GAP_UP and spec.kind != SyntheticScenarioKind.GAP_DOWN:
            return rows
        r = random.Random(spec.seed)
        for i in range(1, len(rows)):
            if r.random() < 0.05:
                gap = 1.05 if spec.kind == SyntheticScenarioKind.GAP_UP else 0.95
                rows[i]["open"] = round(rows[i]["open"] * gap, 2)
                rows[i]["close"] = round(rows[i]["close"] * gap, 2)
                rows[i]["high"] = round(max(rows[i]["open"], rows[i]["close"]) * 1.01, 2)
                rows[i]["low"] = round(min(rows[i]["open"], rows[i]["close"]) * 0.99, 2)
        return rows

    def inject_missing_rows(self, rows: list[dict[str, Any]], spec: SyntheticScenarioSpec) -> list[dict[str, Any]]:
        if spec.kind != SyntheticScenarioKind.MISSING_DATA:
            return rows
        r = random.Random(spec.seed)
        return [row for row in rows if r.random() > 0.05]

    def validate_ohlcv_rows(self, rows: list[dict[str, Any]]) -> list[str]:
        findings = []
        for i, r in enumerate(rows):
            if r["high"] < max(r["open"], r["close"]): findings.append(f"Row {i} high invariant failed")
            if r["low"] > min(r["open"], r["close"]): findings.append(f"Row {i} low invariant failed")
            if r["volume"] < 0: findings.append(f"Row {i} volume < 0")
        return findings

    def generate_ohlcv(self, spec: SyntheticScenarioSpec, adjusted: bool = False) -> SyntheticDataset:
        from .generator import SyntheticScenarioGenerator # need date_index
        # Use a dummy or recreate logic for date index
        from datetime import datetime, timedelta
        start = datetime.strptime(spec.start_date, "%Y-%m-%d")
        end = datetime.strptime(spec.end_date, "%Y-%m-%d")
        dates = []
        curr = start
        while curr <= end:
            if curr.weekday() < 5:
                dates.append(curr.strftime("%Y-%m-%d"))
            curr += timedelta(days=1)

        all_rows = []
        for sym in spec.symbols:
            rows = self.generate_symbol_series(sym, dates, spec, adjusted)
            rows = self.inject_gaps(rows, spec)
            rows = self.inject_missing_rows(rows, spec)
            all_rows.extend(rows)

        cols = ["date", "symbol", "open", "high", "low", "close", "volume"]
        if adjusted: cols.append("adj_close")

        return SyntheticDataset(
            dataset_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            output_kind=SyntheticOutputKind.ADJUSTED_OHLCV if adjusted else SyntheticOutputKind.OHLCV,
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/ohlcv.py", ohlcv_code)

# 9. MACRO
macro_code = """
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
            created_at=datetime.utcnow(),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=3,
            columns=["date", "indicator", "value"],
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/macro.py", macro_code)

# 10. BREADTH
breadth_code = """
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
            created_at=datetime.utcnow(),
            rows=rows,
            row_count=len(rows),
            column_count=4,
            columns=["date", "breadth_score", "advances", "declines"],
            status=SyntheticScenarioStatus.GENERATED
        )
"""
ensure_file("bist_signal_bot/synthetic_scenarios/breadth.py", breadth_code)
