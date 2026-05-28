
from datetime import datetime
import uuid
from typing import List, Optional, Dict
from bist_signal_bot.factors.models import FactorInputSnapshot

class FactorInputBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_input(self, symbol: str, as_of: Optional[datetime] = None) -> FactorInputSnapshot:
        as_of = as_of or datetime.now()
        warnings = []

        # Mocking values for demonstration without external API
        price_momentum = self.price_momentum_inputs(symbol, as_of)
        volatility = self.volatility_input(symbol)
        liquidity = self.liquidity_inputs(symbol)
        fundamentals = self.fundamental_inputs(symbol)

        if price_momentum.get("price_return_20d_pct") is None:
            warnings.append("Missing core price momentum input")

        return FactorInputSnapshot(
            input_id=str(uuid.uuid4()),
            symbol=symbol,
            as_of=as_of,
            sector=fundamentals.get("sector", "UNKNOWN"),
            market_cap=fundamentals.get("market_cap", 1000000.0),
            price_return_20d_pct=price_momentum.get("price_return_20d_pct"),
            price_return_60d_pct=price_momentum.get("price_return_60d_pct"),
            price_return_120d_pct=price_momentum.get("price_return_120d_pct"),
            volatility_60d_pct=volatility,
            avg_volume_20d=liquidity.get("avg_volume_20d"),
            avg_turnover_20d=liquidity.get("avg_turnover_20d"),
            valuation_score=fundamentals.get("valuation_score"),
            earnings_quality_score=fundamentals.get("earnings_quality_score"),
            revenue_growth_yoy_pct=fundamentals.get("revenue_growth_yoy_pct"),
            net_income_growth_yoy_pct=fundamentals.get("net_income_growth_yoy_pct"),
            debt_to_equity=fundamentals.get("debt_to_equity"),
            roe=fundamentals.get("roe"),
            dividend_yield=fundamentals.get("dividend_yield"),
            warnings=warnings
        )

    def build_inputs(self, symbols: List[str], as_of: Optional[datetime] = None) -> List[FactorInputSnapshot]:
        return [self.build_input(s, as_of) for s in symbols]

    def price_momentum_inputs(self, symbol: str, as_of: Optional[datetime] = None) -> Dict[str, Optional[float]]:
        # Mock values
        return {
            "price_return_20d_pct": 5.0,
            "price_return_60d_pct": 12.0,
            "price_return_120d_pct": 25.0
        }

    def volatility_input(self, symbol: str, lookback_days: int = 60) -> Optional[float]:
        return 1.5

    def liquidity_inputs(self, symbol: str, lookback_days: int = 20) -> Dict[str, Optional[float]]:
        return {
            "avg_volume_20d": 500000.0,
            "avg_turnover_20d": 15000000.0
        }

    def fundamental_inputs(self, symbol: str) -> Dict[str, Optional[float]]:
        return {
            "sector": "TECHNOLOGY",
            "market_cap": 50000000.0,
            "valuation_score": 60.0,
            "earnings_quality_score": 80.0,
            "revenue_growth_yoy_pct": 20.0,
            "net_income_growth_yoy_pct": 15.0,
            "debt_to_equity": 0.5,
            "roe": 18.0,
            "dividend_yield": 2.5
        }
