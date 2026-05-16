from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import uuid

import pandas as pd
import numpy as np

from bist_signal_bot.scenarios.models import ScenarioFixture, ScenarioFixtureType

class ScenarioFixtureBuilder:
    def __init__(self):
        pass

    def build_mock_ohlcv(self, symbols: List[str], rows: int = 250) -> Dict[str, pd.DataFrame]:
        np.random.seed(42)
        results = {}
        dates = pd.date_range(end=pd.Timestamp.now().floor("D"), periods=rows, freq="B")
        for sym in symbols:
            # Deterministic base price
            base = 10.0 if sym != "THYAO" else 100.0
            closes = base * (1 + np.random.randn(rows) * 0.02).cumprod()
            df = pd.DataFrame(index=dates)
            df["Close"] = closes
            df["Open"] = df["Close"] * (1 + np.random.randn(rows) * 0.005)
            df["High"] = df[["Open", "Close"]].max(axis=1) * (1 + abs(np.random.randn(rows)) * 0.005)
            df["Low"] = df[["Open", "Close"]].min(axis=1) * (1 - abs(np.random.randn(rows)) * 0.005)
            df["Volume"] = np.random.randint(100000, 10000000, size=rows)
            results[sym] = df
        return results

    def build_mock_symbol_universe(self, symbols: List[str]) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_SYMBOL_UNIVERSE,
            data_summary={"count": len(symbols), "symbols": symbols}
        )

    def build_mock_scan_report(self, symbols: List[str], strategy_name: str) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_SCAN_REPORT,
            data_summary={"symbols": symbols, "strategy": strategy_name, "signals": len(symbols) // 2}
        )

    def build_mock_backtest_result(self, symbol: str, strategy_name: str) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_BACKTEST_RESULT,
            data_summary={"symbol": symbol, "strategy": strategy_name, "sharpe": 1.5, "trades": 50}
        )

    def build_mock_optimization_result(self, symbol: str, strategy_name: str) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_OPTIMIZATION_RESULT,
            data_summary={"symbol": symbol, "strategy": strategy_name, "best_params": {"period": 20}}
        )

    def build_mock_paper_ledger(self, symbols: List[str]) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_PAPER_LEDGER,
            data_summary={"symbols": symbols, "open_positions": len(symbols)}
        )

    def build_mock_ml_model(self, symbols: List[str]) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_ML_MODEL,
            data_summary={"symbols": symbols, "model_type": "dummy", "accuracy": 0.55}
        )

    def build_mock_runtime_state(self) -> ScenarioFixture:
        return ScenarioFixture(
            fixture_id=str(uuid.uuid4()),
            fixture_type=ScenarioFixtureType.MOCK_RUNTIME_STATE,
            data_summary={"state": "running", "uptime": 3600}
        )

    def write_fixtures_to_sandbox(self, fixtures: List[ScenarioFixture], sandbox_dir: Path) -> Dict[str, Path]:
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        for fix in fixtures:
            file_name = f"{fix.fixture_type.value.lower()}_{fix.fixture_id}.json"
            file_path = sandbox_dir / file_name
            with open(file_path, "w") as f:
                json.dump(fix.model_dump(mode='json'), f, indent=2)
            paths[fix.fixture_id] = file_path
        return paths
