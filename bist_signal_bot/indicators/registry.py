from typing import Dict, List, Optional
from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory
from bist_signal_bot.core.exceptions import IndicatorRegistryError

class IndicatorRegistry:
    def __init__(self):
        self._indicators: Dict[str, BaseIndicator] = {}

    def register(self, indicator: BaseIndicator) -> None:
        name = indicator.spec.name.lower()
        if name in self._indicators:
            raise IndicatorRegistryError(f"Indicator '{name}' is already registered.")
        self._indicators[name] = indicator

    def get(self, name: str) -> BaseIndicator:
        normalized_name = name.lower()
        if normalized_name not in self._indicators:
            raise IndicatorRegistryError(f"Indicator '{name}' not found in registry.")
        return self._indicators[normalized_name]

    def exists(self, name: str) -> bool:
        return name.lower() in self._indicators

    def list_specs(self, category: Optional[IndicatorCategory] = None) -> List[IndicatorSpec]:
        specs = [ind.spec for ind in self._indicators.values()]
        if category:
            specs = [s for s in specs if s.category == category]
        return specs

    def list_names(self, category: Optional[IndicatorCategory] = None) -> List[str]:
        return [s.name for s in self.list_specs(category)]

    @classmethod
    def create_default_registry(cls) -> "IndicatorRegistry":

        from bist_signal_bot.indicators.momentum import (
            MomentumIndicator, RateOfChangePercentIndicator, RSIEnhancedIndicator,
            StochasticEnhancedIndicator, WilliamsRIndicator, CCIIndicator, MFIIndicator,
            TSIIndicator, UltimateOscillatorIndicator, PPOIndicator, KSTIndicator,
            ConnorsRSIIndicator, MomentumStrengthCompositeIndicator
        )

        from bist_signal_bot.indicators.native import (
            SMAIndicator, EMAIndicator, WMAIndicator, RSIIndicator, ROCIndicator,
            TrueRangeIndicator, ATRIndicator, BollingerBandsIndicator, MACDIndicator,
            StochasticIndicator, OBVIndicator, VWAPIndicator, DailyReturnIndicator,
            LogReturnIndicator, RollingVolatilityIndicator
        )

        from bist_signal_bot.indicators.trend import (
            MovingAverageDistanceIndicator, MovingAverageCrossoverStateIndicator,
            MovingAverageCrossoverEventIndicator, MovingAverageSlopeIndicator,
            PriceAboveMovingAverageIndicator, ConsecutiveAboveBelowMAIndicator,
            DonchianChannelIndicator, KeltnerChannelIndicator, ADXIndicator,
            AroonIndicator, IchimokuIndicator, SupertrendIndicator,
            LinearRegressionSlopeIndicator, TrendStrengthCompositeIndicator
        )
        from bist_signal_bot.indicators.volatility import (
            ATRPercentIndicator, NormalizedTrueRangeIndicator,
            HistoricalVolatilityIndicator, RealizedVolatilityIndicator,
            ParkinsonVolatilityIndicator, GarmanKlassVolatilityIndicator,
            RogersSatchellVolatilityIndicator, RangePercentIndicator,
            GapPercentIndicator, BollingerBandwidthPercentileIndicator,
            ATRPercentileIndicator, VolatilityZScoreIndicator,
            VolatilityCompressionScoreIndicator, VolatilityExpansionScoreIndicator,
            VolatilityRegimeFeatureIndicator, VolatilityCompositeScoreIndicator
        )


        registry = cls()
        registry.register(MovingAverageDistanceIndicator())
        registry.register(MovingAverageCrossoverStateIndicator())
        registry.register(MovingAverageCrossoverEventIndicator())
        registry.register(MovingAverageSlopeIndicator())
        registry.register(PriceAboveMovingAverageIndicator())
        registry.register(ConsecutiveAboveBelowMAIndicator())
        registry.register(DonchianChannelIndicator())
        registry.register(KeltnerChannelIndicator())
        registry.register(ADXIndicator())
        registry.register(AroonIndicator())
        registry.register(IchimokuIndicator())
        registry.register(SupertrendIndicator())
        registry.register(LinearRegressionSlopeIndicator())
        registry.register(TrendStrengthCompositeIndicator())

        registry.register(SMAIndicator())
        registry.register(EMAIndicator())
        registry.register(WMAIndicator())
        registry.register(RSIIndicator())
        registry.register(ROCIndicator())
        registry.register(TrueRangeIndicator())
        registry.register(ATRIndicator())
        registry.register(BollingerBandsIndicator())
        registry.register(MACDIndicator())
        registry.register(StochasticIndicator())
        registry.register(OBVIndicator())
        registry.register(VWAPIndicator())
        registry.register(DailyReturnIndicator())
        registry.register(LogReturnIndicator())
        registry.register(RollingVolatilityIndicator())

        registry.register(MomentumIndicator())
        registry.register(RateOfChangePercentIndicator())
        registry.register(RSIEnhancedIndicator())
        registry.register(StochasticEnhancedIndicator())
        registry.register(WilliamsRIndicator())
        registry.register(CCIIndicator())
        registry.register(MFIIndicator())
        registry.register(TSIIndicator())
        registry.register(UltimateOscillatorIndicator())
        registry.register(PPOIndicator())
        registry.register(KSTIndicator())
        registry.register(ConnorsRSIIndicator())
        registry.register(MomentumStrengthCompositeIndicator())
        registry.register(ATRPercentIndicator())
        registry.register(NormalizedTrueRangeIndicator())
        registry.register(HistoricalVolatilityIndicator())
        registry.register(RealizedVolatilityIndicator())
        registry.register(ParkinsonVolatilityIndicator())
        registry.register(GarmanKlassVolatilityIndicator())
        registry.register(RogersSatchellVolatilityIndicator())
        registry.register(RangePercentIndicator())
        registry.register(GapPercentIndicator())
        registry.register(BollingerBandwidthPercentileIndicator())
        registry.register(ATRPercentileIndicator())
        registry.register(VolatilityZScoreIndicator())
        registry.register(VolatilityCompressionScoreIndicator())
        registry.register(VolatilityExpansionScoreIndicator())
        registry.register(VolatilityRegimeFeatureIndicator())
        registry.register(VolatilityCompositeScoreIndicator())
        return registry
