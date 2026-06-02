from datetime import timezone
from typing import Any

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
            created_at=datetime.now(timezone.utc),
            rows=all_rows,
            row_count=len(all_rows),
            column_count=len(cols),
            columns=cols,
            status=SyntheticScenarioStatus.GENERATED
        )
