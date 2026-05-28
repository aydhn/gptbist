
from typing import List, Dict, Any
from bist_signal_bot.factors.models import FactorType

class FactorLibrary:
    def __init__(self, settings=None):
        self.settings = settings

    def supported_factors(self) -> List[FactorType]:
        return [
            FactorType.MOMENTUM, FactorType.VALUE, FactorType.QUALITY,
            FactorType.LOW_VOLATILITY, FactorType.LIQUIDITY, FactorType.SIZE,
            FactorType.GROWTH, FactorType.PROFITABILITY, FactorType.LEVERAGE,
            FactorType.DIVIDEND
        ]

    def factor_definition(self, factor_type: FactorType) -> Dict[str, Any]:
        defs = {
            FactorType.MOMENTUM: {"description": "20/60/120 günlük fiyat momentumu"},
            FactorType.VALUE: {"description": "valuation score ve relative valuation"},
            FactorType.QUALITY: {"description": "earnings quality, cash conversion, margins"},
            FactorType.LOW_VOLATILITY: {"description": "düşük volatilite"},
            FactorType.LIQUIDITY: {"description": "hacim ve turnover kalitesi"},
            FactorType.SIZE: {"description": "market cap/floating size"},
            FactorType.GROWTH: {"description": "revenue/net income growth"},
            FactorType.PROFITABILITY: {"description": "ROE, margin quality"},
            FactorType.LEVERAGE: {"description": "debt-to-equity düşük risk context"},
            FactorType.DIVIDEND: {"description": "dividend yield context"}
        }
        return defs.get(factor_type, {"description": "Custom factor"})

    def required_inputs(self, factor_type: FactorType) -> List[str]:
        return []

    def direction(self, factor_type: FactorType) -> str:
        if factor_type in [FactorType.LOW_VOLATILITY, FactorType.LEVERAGE, FactorType.SIZE]:
            return "LOWER_IS_BETTER"
        return "HIGHER_IS_BETTER"

    def default_weights(self) -> Dict[FactorType, float]:
        return {
            FactorType.MOMENTUM: 0.15,
            FactorType.VALUE: 0.15,
            FactorType.QUALITY: 0.15,
            FactorType.LOW_VOLATILITY: 0.10,
            FactorType.LIQUIDITY: 0.10,
            FactorType.SIZE: 0.05,
            FactorType.GROWTH: 0.10,
            FactorType.PROFITABILITY: 0.10,
            FactorType.LEVERAGE: 0.05,
            FactorType.DIVIDEND: 0.05
        }
