import pandas as pd
import numpy as np
import logging
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.regime.models import RegimeConfig, RegimeFeatureSet

class RegimeFeatureBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def clamp_score(self, value: float) -> float:
        if pd.isna(value):
            return 50.0
        return max(0.0, min(100.0, float(value)))

    def calculate_trend_score(self, data: pd.DataFrame, window: int) -> float:
        if len(data) < window:
            return 50.0

        close = data['close']
        sma = close.rolling(window=window).mean()

        current_close = close.iloc[-1]
        current_sma = sma.iloc[-1]

        if pd.isna(current_sma):
            return 50.0

        dist_pct = (current_close - current_sma) / current_sma
        score = 50.0 + (dist_pct * 250.0)

        if len(sma) >= 5:
            sma_slope = (sma.iloc[-1] - sma.iloc[-5]) / sma.iloc[-5]
            score += sma_slope * 500.0

        return self.clamp_score(score)

    def calculate_volatility_score(self, data: pd.DataFrame, window: int) -> float:
        if len(data) < window:
            return 50.0

        close = data['close']
        returns = close.pct_change()

        hist_vol = returns.rolling(window=window).std() * np.sqrt(252)
        current_vol = hist_vol.iloc[-1]

        if pd.isna(current_vol):
            return 50.0

        score = (current_vol - 0.10) / 0.50 * 100.0
        return self.clamp_score(score)

    def calculate_liquidity_score(self, data: pd.DataFrame, window: int) -> float:
        if len(data) < window or 'volume' not in data.columns:
            return 50.0

        volume = data['volume']
        avg_vol = volume.rolling(window=window).mean()

        current_vol = volume.iloc[-1]
        current_avg = avg_vol.iloc[-1]

        if pd.isna(current_avg) or current_avg == 0:
            return 0.0

        ratio = current_vol / current_avg

        zero_vol_count = (volume.iloc[-window:] == 0).sum()
        penalty = zero_vol_count * 10.0

        score = (ratio - 0.5) / 1.5 * 100.0 - penalty
        return self.clamp_score(score)

    def calculate_momentum_score(self, data: pd.DataFrame, window: int) -> float:
        if len(data) < window:
            return 50.0

        close = data['close']
        roc = close.pct_change(periods=window)

        current_roc = roc.iloc[-1]
        if pd.isna(current_roc):
            return 50.0

        score = 50.0 + (current_roc * 250.0)
        return self.clamp_score(score)

    def calculate_range_breakout_scores(self, data: pd.DataFrame, window: int) -> tuple[float, float]:
        if len(data) < window:
            return 50.0, 50.0

        high = data['high']
        low = data['low']
        close = data['close']

        recent_high = high.rolling(window=window).max().iloc[-1]
        recent_low = low.rolling(window=window).min().iloc[-1]
        current_close = close.iloc[-1]

        if pd.isna(recent_high) or pd.isna(recent_low) or recent_high == recent_low:
            return 50.0, 50.0

        range_pos = (current_close - recent_low) / (recent_high - recent_low) * 100.0
        range_score = self.clamp_score(range_pos)

        range_size = (recent_high - recent_low) / recent_low
        narrowness = max(0, 1.0 - (range_size * 5)) * 50.0

        proximity_high = abs(current_close - recent_high) / recent_high
        proximity_low = abs(current_close - recent_low) / recent_low

        min_prox = min(proximity_high, proximity_low)
        prox_score = max(0, 1.0 - (min_prox * 20)) * 50.0

        breakout_score = self.clamp_score(narrowness + prox_score)

        return range_score, breakout_score

    def build_feature_set(self, data: pd.DataFrame, symbol: str, config: RegimeConfig | None = None, benchmark_data: pd.DataFrame | None = None) -> RegimeFeatureSet:
        if config is None:
            config = RegimeConfig()

        if len(data) == 0:
            self.logger.warning(f"Empty data provided for {symbol} regime features")
            return RegimeFeatureSet(
                symbol=symbol,
                trend_score=50.0,
                volatility_score=50.0,
                liquidity_score=50.0,
                momentum_score=50.0,
                range_score=50.0,
                breakout_score=50.0,
                composite_regime_score=50.0,
                warnings=["Empty data provided"]
            )

        trend_score = self.calculate_trend_score(data, config.trend_window)
        vol_score = self.calculate_volatility_score(data, config.volatility_window)
        liq_score = self.calculate_liquidity_score(data, config.liquidity_window)
        mom_score = self.calculate_momentum_score(data, config.momentum_window)
        range_score, breakout_score = self.calculate_range_breakout_scores(data, config.trend_window)

        composite_score = (
            trend_score * 0.4 +
            (100.0 - vol_score) * 0.2 +
            liq_score * 0.2 +
            mom_score * 0.2
        )

        timestamp = data.index[-1] if isinstance(data.index, pd.DatetimeIndex) else None

        features = {
            "close": float(data['close'].iloc[-1]) if len(data) > 0 else 0.0,
            "volume": float(data.get('volume', pd.Series([0.0])).iloc[-1]) if len(data) > 0 else 0.0
        }

        return RegimeFeatureSet(
            symbol=symbol,
            timestamp=timestamp,
            trend_score=trend_score,
            volatility_score=vol_score,
            liquidity_score=liq_score,
            momentum_score=mom_score,
            range_score=range_score,
            breakout_score=breakout_score,
            composite_regime_score=self.clamp_score(composite_score),
            features=features
        )

    def add_regime_feature_columns(self, data: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
        if config is None:
            config = RegimeConfig()

        df = data.copy()

        window = config.trend_window
        sma = df['close'].rolling(window=window).mean()
        dist_pct = (df['close'] - sma) / sma
        df['regime_trend_score'] = (50.0 + (dist_pct * 250.0)).clip(0, 100)

        vol_window = config.volatility_window
        returns = df['close'].pct_change()
        hist_vol = returns.rolling(window=vol_window).std() * np.sqrt(252)
        df['regime_volatility_score'] = ((hist_vol - 0.10) / 0.50 * 100.0).clip(0, 100)

        liq_window = config.liquidity_window
        if 'volume' in df.columns:
            avg_vol = df['volume'].rolling(window=liq_window).mean()
            avg_vol_safe = avg_vol.replace(0, np.nan)
            ratio = df['volume'] / avg_vol_safe
            df['regime_liquidity_score'] = ((ratio - 0.5) / 1.5 * 100.0).clip(0, 100)
            df['regime_liquidity_score'].fillna(50.0, inplace=True)
        else:
            df['regime_liquidity_score'] = 50.0

        mom_window = config.momentum_window
        roc = df['close'].pct_change(periods=mom_window)
        df['regime_momentum_score'] = (50.0 + (roc * 250.0)).clip(0, 100)

        recent_high = df['high'].rolling(window=window).max()
        recent_low = df['low'].rolling(window=window).min()
        range_size = recent_high - recent_low
        range_size_safe = range_size.replace(0, np.nan)
        df['regime_range_score'] = ((df['close'] - recent_low) / range_size_safe * 100.0).clip(0, 100)
        df['regime_range_score'].fillna(50.0, inplace=True)

        df['regime_breakout_score'] = 50.0

        df['regime_composite_score'] = (
            df['regime_trend_score'] * 0.4 +
            (100.0 - df['regime_volatility_score']) * 0.2 +
            df['regime_liquidity_score'] * 0.2 +
            df['regime_momentum_score'] * 0.2
        ).clip(0, 100)

        cols = ['regime_trend_score', 'regime_volatility_score', 'regime_liquidity_score',
                'regime_momentum_score', 'regime_range_score', 'regime_breakout_score',
                'regime_composite_score']
        df[cols] = df[cols].fillna(50.0)

        return df
