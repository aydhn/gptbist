import pandas as pd
from typing import Any

from bist_signal_bot.strategies.base_strategy import BaseStrategy
from bist_signal_bot.strategies.models import (
    StrategySpec,
    StrategyCategory,
    StrategyPositionSide,
    StrategyParameter
)
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.signals.models import (
    SignalCandidate,
    SignalDirection,
    SignalReason,
    RiskNote
)
from bist_signal_bot.signals.scoring import classify_signal_strength

class MovingAverageTrendStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(
            name="moving_average_trend",
            display_name="Moving Average Trend",
            category=StrategyCategory.TREND_FOLLOWING,
            description="Simple moving average crossover strategy for baseline testing.",
            position_side=StrategyPositionSide.LONG_SHORT,
            required_columns=["close"],
            parameters=[
                StrategyParameter(name="fast_window", default=20, param_type="int", min_value=1),
                StrategyParameter(name="slow_window", default=50, param_type="int", min_value=1),
                StrategyParameter(name="min_score", default=60.0, param_type="float", min_value=0.0, max_value=100.0),
                StrategyParameter(name="allow_short", default=False, param_type="bool")
            ],
            default_params={
                "fast_window": 20,
                "slow_window": 50,
                "min_score": 60.0,
                "allow_short": False
            },
            min_rows=50,
            supports_short=True
        )

    def prepare_features(self, context: StrategyContext, params: dict[str, Any]) -> pd.DataFrame:
        df = context.data.copy()
        fast = params["fast_window"]
        slow = params["slow_window"]

        if f"sma_{fast}" not in df.columns:
            df[f"sma_{fast}"] = df["close"].rolling(window=fast).mean()
        if f"sma_{slow}" not in df.columns:
            df[f"sma_{slow}"] = df["close"].rolling(window=slow).mean()

        return df

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        fast = params["fast_window"]
        slow = params["slow_window"]
        allow_short = params["allow_short"]
        min_score = params["min_score"]

        df = self.prepare_features(context, params)
        if df.empty or len(df) < slow:
            return None

        latest = df.iloc[-1]

        close = latest["close"]
        sma_fast = latest[f"sma_{fast}"]
        sma_slow = latest[f"sma_{slow}"]

        if pd.isna(sma_fast) or pd.isna(sma_slow):
            return None

        direction = SignalDirection.WATCH
        score = 0.0
        reasons = []

        if close > sma_fast and sma_fast > sma_slow:
            direction = SignalDirection.LONG
            score = 70.0 # simple baseline score
            reasons.append(SignalReason(category="trend", message=f"close > sma_{fast}"))
            reasons.append(SignalReason(category="trend", message=f"sma_{fast} > sma_{slow}"))
        elif allow_short and close < sma_fast and sma_fast < sma_slow:
            direction = SignalDirection.SHORT
            score = 70.0
            reasons.append(SignalReason(category="trend", message=f"close < sma_{fast}"))
            reasons.append(SignalReason(category="trend", message=f"sma_{fast} < sma_{slow}"))
        else:
            direction = SignalDirection.FLAT
            score = 20.0
            reasons.append(SignalReason(category="trend", message="No clear trend alignment"))

        strength = classify_signal_strength(score)

        if direction in [SignalDirection.LONG, SignalDirection.SHORT] and score < min_score:
            direction = SignalDirection.WATCH
            reasons.append(SignalReason(category="filter", message=f"Score {score} < min_score {min_score}"))

        risk_notes = [RiskNote(category="disclaimer", message="Baseline research strategy only.")]

        context.data = df
        context.latest_row = latest

        return self.build_signal_candidate(
            context=context,
            direction=direction,
            score=score,
            strength=strength,
            reasons=reasons,
            risk_notes=risk_notes
        )

class RSIMeanReversionStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(
            name="rsi_mean_reversion",
            display_name="RSI Mean Reversion",
            category=StrategyCategory.MEAN_REVERSION,
            description="Simple RSI oversold/overbought mean reversion strategy.",
            position_side=StrategyPositionSide.LONG_SHORT,
            required_columns=["close"],
            parameters=[
                StrategyParameter(name="rsi_window", default=14, param_type="int", min_value=1),
                StrategyParameter(name="oversold", default=30.0, param_type="float", min_value=0.0, max_value=50.0),
                StrategyParameter(name="overbought", default=70.0, param_type="float", min_value=50.0, max_value=100.0),
                StrategyParameter(name="min_score", default=55.0, param_type="float", min_value=0.0, max_value=100.0),
                StrategyParameter(name="allow_short", default=False, param_type="bool")
            ],
            default_params={
                "rsi_window": 14,
                "oversold": 30.0,
                "overbought": 70.0,
                "min_score": 55.0,
                "allow_short": False
            },
            min_rows=20,
            supports_short=True
        )

    def prepare_features(self, context: StrategyContext, params: dict[str, Any]) -> pd.DataFrame:
        df = context.data.copy()
        window = params["rsi_window"]

        if "rsi" not in df.columns:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

        return df

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        allow_short = params["allow_short"]
        min_score = params["min_score"]
        oversold = params["oversold"]
        overbought = params["overbought"]

        df = self.prepare_features(context, params)
        if df.empty:
            return None

        latest = df.iloc[-1]
        rsi = latest.get("rsi")

        if pd.isna(rsi):
            return None

        direction = SignalDirection.WATCH
        score = 0.0
        reasons = []

        if rsi < oversold:
            direction = SignalDirection.LONG
            score = 65.0 + (oversold - rsi)
            reasons.append(SignalReason(category="momentum", message=f"RSI ({rsi:.1f}) below oversold ({oversold})"))
        elif allow_short and rsi > overbought:
            direction = SignalDirection.SHORT
            score = 65.0 + (rsi - overbought)
            reasons.append(SignalReason(category="momentum", message=f"RSI ({rsi:.1f}) above overbought ({overbought})"))
        else:
            direction = SignalDirection.AVOID
            score = 30.0
            reasons.append(SignalReason(category="momentum", message=f"RSI ({rsi:.1f}) in neutral zone"))

        score = min(100.0, score)
        strength = classify_signal_strength(score)

        if direction in [SignalDirection.LONG, SignalDirection.SHORT] and score < min_score:
            direction = SignalDirection.WATCH

        context.data = df
        context.latest_row = latest

        return self.build_signal_candidate(
            context=context,
            direction=direction,
            score=score,
            strength=strength,
            reasons=reasons,
            risk_notes=[RiskNote(category="disclaimer", message="Mean reversion carries significant risk.")]
        )

class BreakoutVolumeStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(
            name="breakout_volume",
            display_name="Volume Confirmed Breakout",
            category=StrategyCategory.BREAKOUT,
            description="Breakout from recent high/low confirmed by volume increase.",
            position_side=StrategyPositionSide.LONG_SHORT,
            required_columns=["high", "low", "close", "volume"],
            parameters=[
                StrategyParameter(name="price_window", default=20, param_type="int", min_value=5),
                StrategyParameter(name="volume_window", default=20, param_type="int", min_value=5),
                StrategyParameter(name="volume_multiplier", default=1.5, param_type="float", min_value=1.0),
                StrategyParameter(name="min_score", default=60.0, param_type="float", min_value=0.0, max_value=100.0),
                StrategyParameter(name="allow_short", default=False, param_type="bool")
            ],
            default_params={
                "price_window": 20,
                "volume_window": 20,
                "volume_multiplier": 1.5,
                "min_score": 60.0,
                "allow_short": False
            },
            min_rows=25,
            supports_short=True
        )

    def prepare_features(self, context: StrategyContext, params: dict[str, Any]) -> pd.DataFrame:
        df = context.data.copy()
        price_w = params["price_window"]
        vol_w = params["volume_window"]

        df["recent_high"] = df["high"].shift(1).rolling(window=price_w).max()
        df["recent_low"] = df["low"].shift(1).rolling(window=price_w).min()
        df["avg_volume"] = df["volume"].shift(1).rolling(window=vol_w).mean()

        return df

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        allow_short = params["allow_short"]
        min_score = params["min_score"]
        vol_mult = params["volume_multiplier"]

        df = self.prepare_features(context, params)
        if df.empty:
            return None

        latest = df.iloc[-1]

        close = latest["close"]
        vol = latest["volume"]
        recent_high = latest.get("recent_high")
        recent_low = latest.get("recent_low")
        avg_vol = latest.get("avg_volume")

        if pd.isna(recent_high) or pd.isna(avg_vol):
            return None

        direction = SignalDirection.WATCH
        score = 0.0
        reasons = []

        vol_confirmed = vol > (avg_vol * vol_mult)

        if close > recent_high:
            direction = SignalDirection.LONG if vol_confirmed else SignalDirection.WATCH
            score = 80.0 if vol_confirmed else 45.0
            reasons.append(SignalReason(category="breakout", message=f"Close ({close}) broke above recent high ({recent_high})"))
            if vol_confirmed:
                reasons.append(SignalReason(category="volume", message=f"Volume confirmed (> {vol_mult}x avg)"))
            else:
                reasons.append(SignalReason(category="volume", message=f"Volume not confirmed"))
        elif allow_short and close < recent_low:
            direction = SignalDirection.SHORT if vol_confirmed else SignalDirection.WATCH
            score = 80.0 if vol_confirmed else 45.0
            reasons.append(SignalReason(category="breakout", message=f"Close ({close}) broke below recent low ({recent_low})"))
            if vol_confirmed:
                reasons.append(SignalReason(category="volume", message=f"Volume confirmed (> {vol_mult}x avg)"))
        else:
            direction = SignalDirection.FLAT
            score = 20.0
            reasons.append(SignalReason(category="breakout", message="No breakout detected"))

        strength = classify_signal_strength(score)

        if direction in [SignalDirection.LONG, SignalDirection.SHORT] and score < min_score:
            direction = SignalDirection.WATCH

        context.data = df
        context.latest_row = latest

        return self.build_signal_candidate(
            context=context,
            direction=direction,
            score=score,
            strength=strength,
            reasons=reasons,
            risk_notes=[RiskNote(category="risk", message="False breakouts are common without further confirmation.")]
        )

class CompositeFeatureStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(
            name="composite_feature",
            display_name="Composite Feature Score",
            category=StrategyCategory.MULTI_FACTOR,
            description="Baseline multi-factor strategy using predefined feature columns.",
            position_side=StrategyPositionSide.LONG_SHORT,
            required_columns=["close"],
            parameters=[
                StrategyParameter(name="min_score", default=65.0, param_type="float", min_value=0.0, max_value=100.0),
                StrategyParameter(name="allow_short", default=False, param_type="bool"),
                StrategyParameter(name="use_trend", default=True, param_type="bool"),
                StrategyParameter(name="use_momentum", default=True, param_type="bool"),
                StrategyParameter(name="use_volume", default=True, param_type="bool")
            ],
            default_params={
                "min_score": 65.0,
                "allow_short": False,
                "use_trend": True,
                "use_momentum": True,
                "use_volume": True
            },
            min_rows=1,
            supports_short=True
        )

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        allow_short = params["allow_short"]
        min_score = params["min_score"]

        if context.data.empty:
            return None

        latest = context.latest_row

        reasons = []
        risk_notes = []

        trend_score = latest.get("trend_score", 50.0)
        mom_score = latest.get("momentum_score", 50.0)
        vol_score = latest.get("volume_score", 50.0)

        if pd.isna(trend_score):
            trend_score = 50.0
            risk_notes.append(RiskNote(category="data", message="Missing trend score feature, defaulted to 50"))

        if pd.isna(mom_score):
            mom_score = 50.0
            risk_notes.append(RiskNote(category="data", message="Missing momentum score feature, defaulted to 50"))

        components = []
        if params["use_trend"]:
            components.append(trend_score)
        if params["use_momentum"]:
            components.append(mom_score)
        if params["use_volume"]:
            components.append(vol_score)

        if not components:
            score = 50.0
        else:
            score = sum(components) / len(components)

        direction = SignalDirection.WATCH

        if score >= min_score:
            direction = SignalDirection.LONG
            reasons.append(SignalReason(category="composite", message=f"Composite score ({score:.1f}) is high"))
        elif allow_short and score <= (100 - min_score):
            direction = SignalDirection.SHORT
            score = 100 - score
            reasons.append(SignalReason(category="composite", message=f"Composite score is low bearish"))
        else:
            direction = SignalDirection.FLAT
            reasons.append(SignalReason(category="composite", message="Composite score is neutral"))

        strength = classify_signal_strength(score)

        return self.build_signal_candidate(
            context=context,
            direction=direction,
            score=score,
            strength=strength,
            reasons=reasons,
            risk_notes=risk_notes
        )
