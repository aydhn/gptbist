import pandas as pd
from typing import List, Tuple
from bist_signal_bot.divergence.models import (
    PivotMode, PivotType, DivergenceType, DivergenceStrength,
    DivergenceEvent, DivergenceIssue, DivergenceRequest
)
from bist_signal_bot.divergence.pivots import PivotDetector
from bist_signal_bot.config.settings import Settings

class DivergenceDetector:
    def __init__(self, pivot_detector: PivotDetector, settings: Settings | None = None):
        self.pivot_detector = pivot_detector
        self.settings = settings or Settings()

    def detect_for_indicator(self, data: pd.DataFrame, price_col: str, indicator_col: str, request: DivergenceRequest, symbol: str, timeframe: str) -> Tuple[pd.DataFrame, List[DivergenceEvent], List[DivergenceIssue]]:
        """
        Detects divergences between a price column and an indicator column.
        Returns the modified DataFrame with feature columns, a list of events, and any issues.
        """
        events = []
        issues = []
        df = data.copy()

        if price_col not in df.columns or indicator_col not in df.columns:
            issues.append(DivergenceIssue(
                indicator=indicator_col,
                message=f"Missing required columns. Found: {df.columns.tolist()}",
                severity="ERROR"
            ))
            return df, events, issues

        if len(df) < max(request.lookback, request.max_pivot_distance) * 2:
             issues.append(DivergenceIssue(
                indicator=indicator_col,
                message=f"Not enough data points. Need at least {max(request.lookback, request.max_pivot_distance) * 2}",
                severity="WARNING"
            ))
             return df, events, issues

        # Detect Highs (for Bearish divergence)
        price_high_flags = self.pivot_detector.detect_pivots(df[price_col], PivotType.HIGH)
        ind_high_flags = self.pivot_detector.detect_pivots(df[indicator_col], PivotType.HIGH)

        price_high_pivots = self.pivot_detector.extract_pivot_points(df[price_col], PivotType.HIGH, price_high_flags)
        ind_high_pivots = self.pivot_detector.extract_pivot_points(df[indicator_col], PivotType.HIGH, ind_high_flags)

        high_pairs = self.pivot_detector.pair_recent_pivots(
            price_high_pivots, ind_high_pivots, request.min_pivot_distance, request.max_pivot_distance
        )

        # Detect Lows (for Bullish divergence)
        price_low_flags = self.pivot_detector.detect_pivots(df[price_col], PivotType.LOW)
        ind_low_flags = self.pivot_detector.detect_pivots(df[indicator_col], PivotType.LOW)

        price_low_pivots = self.pivot_detector.extract_pivot_points(df[price_col], PivotType.LOW, price_low_flags)
        ind_low_pivots = self.pivot_detector.extract_pivot_points(df[indicator_col], PivotType.LOW, ind_low_flags)

        low_pairs = self.pivot_detector.pair_recent_pivots(
            price_low_pivots, ind_low_pivots, request.min_pivot_distance, request.max_pivot_distance
        )

        # Initialize feature columns
        self._init_feature_columns(df, indicator_col)

        # Check High Pairs for Bearish Divergence
        for p1, p2, i1, i2 in high_pairs:
            div_type = DivergenceType.NONE

            # Regular Bearish: Price Higher High, Indicator Lower High
            if request.include_regular and p2.value > p1.value and i2.value < i1.value:
                div_type = DivergenceType.REGULAR_BEARISH

            # Hidden Bearish: Price Lower High, Indicator Higher High
            elif request.include_hidden and p2.value < p1.value and i2.value > i1.value:
                div_type = DivergenceType.HIDDEN_BEARISH

            if div_type != DivergenceType.NONE:
                self._create_event(df, div_type, p1, p2, i1, i2, symbol, indicator_col, request, events)

        # Check Low Pairs for Bullish Divergence
        for p1, p2, i1, i2 in low_pairs:
            div_type = DivergenceType.NONE

            # Regular Bullish: Price Lower Low, Indicator Higher Low
            if request.include_regular and p2.value < p1.value and i2.value > i1.value:
                div_type = DivergenceType.REGULAR_BULLISH

            # Hidden Bullish: Price Higher Low, Indicator Lower Low
            elif request.include_hidden and p2.value > p1.value and i2.value < i1.value:
                div_type = DivergenceType.HIDDEN_BULLISH

            if div_type != DivergenceType.NONE:
                self._create_event(df, div_type, p1, p2, i1, i2, symbol, indicator_col, request, events)

        # Calculate bars since last
        self._calculate_bars_since_last(df, indicator_col)

        return df, events, issues

    def _create_event(self, df: pd.DataFrame, div_type: DivergenceType, p1, p2, i1, i2, symbol: str, indicator_col: str, request: DivergenceRequest, events: list):
        bars_between = p2.index_position - p1.index_position
        strength_score = self.calculate_strength(p1.value, p2.value, i1.value, i2.value, bars_between, request.pivot_mode == PivotMode.CONFIRMED_LAGGED)
        strength = self.classify_strength(strength_score)

        if strength_score >= request.min_strength_score:
            event = DivergenceEvent(
                symbol=symbol,
                indicator=indicator_col,
                divergence_type=div_type,
                pivot_mode=request.pivot_mode,
                price_pivot_1_timestamp=p1.timestamp,
                price_pivot_2_timestamp=p2.timestamp,
                indicator_pivot_1_value=i1.value,
                indicator_pivot_2_value=i2.value,
                price_pivot_1_value=p1.value,
                price_pivot_2_value=p2.value,
                bars_between=bars_between,
                strength_score=strength_score,
                strength=strength,
                confirmed=(request.pivot_mode == PivotMode.CONFIRMED_LAGGED),
                metadata={"p2_index": p2.index_position, "detected_at": p2.metadata.get("detected_at", p2.timestamp)}
            )
            events.append(event)
            self._update_features(df, event, indicator_col)

    def calculate_strength(self, p1_val: float, p2_val: float, i1_val: float, i2_val: float, bars: int, is_confirmed: bool) -> float:
        """
        Calculates a simple 0-100 strength score.
        """
        if p1_val == 0 or i1_val == 0:
            return 50.0

        # Price diff %
        price_diff_pct = abs((p2_val - p1_val) / p1_val) * 100

        # Indicator diff ratio (rough heuristic)
        ind_diff_pct = abs((i2_val - i1_val) / i1_val) * 100

        # Base score based on differences
        score = (price_diff_pct * 5) + (ind_diff_pct * 2)

        # Penalty for being too far apart (diluted impact)
        if bars > 30:
            score -= (bars - 30) * 0.5

        # Confirmation bonus
        if is_confirmed:
            score += 10

        return max(0.0, min(100.0, score))

    def classify_strength(self, score: float) -> DivergenceStrength:
        if score < 33:
            return DivergenceStrength.WEAK
        elif score < 66:
            return DivergenceStrength.MEDIUM
        return DivergenceStrength.STRONG

    def _init_feature_columns(self, df: pd.DataFrame, ind: str):
        cols = [
            f"div_regular_bullish_{ind}", f"div_regular_bearish_{ind}",
            f"div_hidden_bullish_{ind}", f"div_hidden_bearish_{ind}",
            f"div_strength_{ind}", f"div_direction_score_{ind}",
            f"div_bars_since_last_{ind}"
        ]
        for col in cols:
            df[col] = 0.0

    def _update_features(self, df: pd.DataFrame, event: DivergenceEvent, ind: str):
        # Feature row is the detection row
        feature_idx_label = event.metadata.get("detected_at", event.price_pivot_2_timestamp)

        if event.divergence_type == DivergenceType.REGULAR_BULLISH:
            df.at[feature_idx_label, f"div_regular_bullish_{ind}"] = 1.0
            df.at[feature_idx_label, f"div_direction_score_{ind}"] = 1.0
        elif event.divergence_type == DivergenceType.REGULAR_BEARISH:
            df.at[feature_idx_label, f"div_regular_bearish_{ind}"] = 1.0
            df.at[feature_idx_label, f"div_direction_score_{ind}"] = -1.0
        elif event.divergence_type == DivergenceType.HIDDEN_BULLISH:
            df.at[feature_idx_label, f"div_hidden_bullish_{ind}"] = 1.0
            df.at[feature_idx_label, f"div_direction_score_{ind}"] = 1.0
        elif event.divergence_type == DivergenceType.HIDDEN_BEARISH:
            df.at[feature_idx_label, f"div_hidden_bearish_{ind}"] = 1.0
            df.at[feature_idx_label, f"div_direction_score_{ind}"] = -1.0

        # Update strength
        current_strength = df.at[feature_idx_label, f"div_strength_{ind}"]
        if event.strength_score > current_strength:
             df.at[feature_idx_label, f"div_strength_{ind}"] = event.strength_score

    def _calculate_bars_since_last(self, df: pd.DataFrame, ind: str):
        # Calculate bars since last divergence event for this indicator
        has_div = (
            (df[f"div_regular_bullish_{ind}"] == 1) |
            (df[f"div_regular_bearish_{ind}"] == 1) |
            (df[f"div_hidden_bullish_{ind}"] == 1) |
            (df[f"div_hidden_bearish_{ind}"] == 1)
        )

        # We can find distances using cumulative sums
        blocks = has_div.cumsum()

        # Calculate distance
        bars_since = df.groupby(blocks).cumcount()
        # The row where the div happens has distance 0, the next is 1, etc.
        # But we only want to start counting AFTER the first divergence.
        # So we mask out the 0 block
        bars_since[blocks == 0] = -1 # Or NaN

        df[f"div_bars_since_last_{ind}"] = bars_since

    def build_feature_columns(self, ind: str) -> List[str]:
        return [
            f"div_regular_bullish_{ind}", f"div_regular_bearish_{ind}",
            f"div_hidden_bullish_{ind}", f"div_hidden_bearish_{ind}",
            f"div_strength_{ind}", f"div_direction_score_{ind}",
            f"div_bars_since_last_{ind}"
        ]
