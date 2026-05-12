import pandas as pd
import logging
import time
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.regime.models import (
    RegimeConfig, UniverseRegimeReport, RegimeClassification, MarketRegime, TrendRegime, VolatilityRegime
)
from bist_signal_bot.regime.engine import RegimeEngine

class UniverseRegimeAnalyzer:
    def __init__(self,
                 regime_engine: RegimeEngine | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.engine = regime_engine or RegimeEngine(settings=self.settings)

    def market_breadth_summary(self, classifications: list[RegimeClassification]) -> dict[str, Any]:
        market_counts = {}
        trend_counts = {}
        vol_counts = {}

        for c in classifications:
            market_counts[c.market_regime.value] = market_counts.get(c.market_regime.value, 0) + 1
            trend_counts[c.trend_regime.value] = trend_counts.get(c.trend_regime.value, 0) + 1
            vol_counts[c.volatility_regime.value] = vol_counts.get(c.volatility_regime.value, 0) + 1

        total = len(classifications)
        if total == 0:
            return {
                "market_counts": {}, "trend_counts": {}, "vol_counts": {},
                "risk_on_pct": 0.0, "risk_off_pct": 0.0, "stress_pct": 0.0,
                "avg_score": 0.0
            }

        risk_on = sum(1 for c in classifications if c.market_regime in (MarketRegime.RISK_ON, MarketRegime.TRENDING_UP))
        risk_off = sum(1 for c in classifications if c.market_regime in (MarketRegime.RISK_OFF, MarketRegime.TRENDING_DOWN))
        stress = sum(1 for c in classifications if c.volatility_regime == VolatilityRegime.STRESS or c.market_regime == MarketRegime.HIGH_VOLATILITY_STRESS)

        avg_score = sum(c.regime_score for c in classifications) / total

        return {
            "market_counts": market_counts,
            "trend_counts": trend_counts,
            "vol_counts": vol_counts,
            "risk_on_pct": (risk_on / total) * 100.0,
            "risk_off_pct": (risk_off / total) * 100.0,
            "stress_pct": (stress / total) * 100.0,
            "avg_score": avg_score
        }

    def calculate_correlation_stress(self, data_by_symbol: dict[str, pd.DataFrame], window: int) -> dict[str, Any]:
        if len(data_by_symbol) < 2:
            return {"status": "warning", "message": "Not enough symbols for correlation analysis"}

        try:
            returns_df = pd.DataFrame()
            for sym, df in data_by_symbol.items():
                if len(df) >= window:
                    returns_df[sym] = df['close'].pct_change().tail(window)

            if returns_df.shape[1] < 2:
                return {"status": "warning", "message": "Not enough data for correlation analysis"}

            corr_matrix = returns_df.corr()
            avg_corr = corr_matrix.mean().mean()

            status = "normal"
            if avg_corr > 0.7:
                status = "stress (high correlation)"
            elif avg_corr < 0.1:
                status = "low correlation"

            return {
                "status": "success",
                "average_correlation": float(avg_corr),
                "symbols_used": returns_df.shape[1],
                "correlation_status": status
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def analyze_universe(self, data_by_symbol: dict[str, pd.DataFrame], config: RegimeConfig | None = None) -> UniverseRegimeReport:
        start_time = time.time()
        issues = []

        batch_result = self.engine.classify_many(data_by_symbol, config)
        classifications = batch_result.classifications

        if batch_result.failed_count > 0:
            issues.append(f"Failed to classify {batch_result.failed_count} symbols.")

        breadth = self.market_breadth_summary(classifications)

        corr_info = {}
        if config and config.correlation_window > 0:
            corr_info = self.calculate_correlation_stress(data_by_symbol, config.correlation_window)
            if corr_info.get("status") in ("warning", "error"):
                issues.append(f"Correlation: {corr_info['message']}")

        symbols = [c.symbol for c in classifications]

        return UniverseRegimeReport(
            symbols=symbols,
            classifications=classifications,
            market_regime_counts=breadth["market_counts"],
            trend_regime_counts=breadth["trend_counts"],
            volatility_regime_counts=breadth["vol_counts"],
            risk_on_pct=breadth["risk_on_pct"],
            risk_off_pct=breadth["risk_off_pct"],
            stress_pct=breadth["stress_pct"],
            average_regime_score=breadth["avg_score"],
            elapsed_seconds=time.time() - start_time,
            issues=issues,
            metadata={"correlation": corr_info}
        )
