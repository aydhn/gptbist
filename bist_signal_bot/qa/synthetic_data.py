from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from bist_signal_bot.qa.models import QAFixtureManifest
from bist_signal_bot.qa.fixtures import QAFixtureManager
from bist_signal_bot.config.settings import get_settings

class SyntheticDataBuilder:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        np.random.seed(self.settings.QA_SYNTHETIC_SEED)

    def build_all(self, tmp_root: Path) -> QAFixtureManifest:
        symbols = self.settings.QA_SYNTHETIC_SYMBOLS.split(",")
        start = datetime.fromisoformat(self.settings.QA_SYNTHETIC_START_DATE)
        periods = self.settings.QA_SYNTHETIC_PERIODS

        payloads = {
            "synthetic_ohlcv.csv": self.build_ohlcv(symbols, start, periods),
            "synthetic_instruments.csv": self.build_instruments(symbols),
            "synthetic_macro.csv": self.build_macro(start, periods),
            "synthetic_events.csv": self.build_events(symbols, start),
            "synthetic_disclosures.csv": self.build_disclosures(symbols, start),
            "synthetic_financials.csv": self.build_financials(symbols, start)
        }

        self.write_csvs(tmp_root, payloads)

        manager = QAFixtureManager(self.settings, base_dir=tmp_root.parent.parent)
        return manager.create_fixture_manifest()

    def build_ohlcv(self, symbols: list[str], start: datetime, periods: int) -> pd.DataFrame:
        dates = pd.date_range(start, periods=periods, freq="B")
        rows = []
        for sym in symbols:
            price = 100.0
            for dt in dates:
                ret = np.random.normal(0.001, 0.02)
                price = price * (1 + ret)
                rows.append({
                    "symbol": sym,
                    "date": dt.date(),
                    "open": price * 0.99,
                    "high": price * 1.02,
                    "low": price * 0.98,
                    "close": price,
                    "volume": np.random.randint(1000, 1000000)
                })
        return pd.DataFrame(rows)

    def build_instruments(self, symbols: list[str]) -> pd.DataFrame:
        return pd.DataFrame([{"symbol": s, "sector": "TECH", "status": "ACTIVE"} for s in symbols])

    def build_macro(self, start: datetime, periods: int) -> pd.DataFrame:
        dates = pd.date_range(start, periods=periods, freq="B")
        return pd.DataFrame({"date": [d.date() for d in dates], "usd_try": np.linspace(30, 35, periods)})

    def build_events(self, symbols: list[str], start: datetime) -> pd.DataFrame:
        return pd.DataFrame([{"symbol": s, "date": start.date(), "event_type": "EARNINGS"} for s in symbols])

    def build_disclosures(self, symbols: list[str], start: datetime) -> pd.DataFrame:
        return pd.DataFrame([{"symbol": s, "date": start.date(), "severity": "HIGH", "text": "Synthetic test"} for s in symbols])

    def build_financials(self, symbols: list[str], start: datetime) -> pd.DataFrame:
        return pd.DataFrame([{"symbol": s, "period": "2023-12", "net_income": 1000000} for s in symbols])

    def write_csvs(self, root: Path, payloads: dict[str, pd.DataFrame]) -> dict[str, str]:
        root.mkdir(parents=True, exist_ok=True)
        res = {}
        for name, df in payloads.items():
            path = root / name
            df.to_csv(path, index=False)
            res[name] = str(path)
        return res
