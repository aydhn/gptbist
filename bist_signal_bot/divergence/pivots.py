import pandas as pd
from typing import List, Tuple
from bist_signal_bot.divergence.models import PivotType, PivotMode, PivotPoint

class PivotDetector:
    def __init__(self, mode: PivotMode = PivotMode.LOOKBACK_ONLY, lookback: int = 5, confirmation_bars: int = 3):
        self.mode = mode
        self.lookback = lookback
        self.confirmation_bars = confirmation_bars

    def detect_pivots(self, series: pd.Series, pivot_type: PivotType) -> pd.Series:
        """
        Detects pivots in a pandas Series.
        Returns a Series of 1s (pivot) and 0s (no pivot).
        """
        if self.mode == PivotMode.LOOKBACK_ONLY:
            if pivot_type == PivotType.HIGH:
                prev_max = series.rolling(self.lookback).max().shift(1)
                pivots = (series > prev_max).astype(int)
            else:
                prev_min = series.rolling(self.lookback).min().shift(1)
                pivots = (series < prev_min).astype(int)
            return pivots

        elif self.mode == PivotMode.CONFIRMED_LAGGED:
            # For confirmed lagged, a point t is a pivot if it's the extremum in [t-lookback, t+confirmation_bars]
            # To avoid look-ahead bias, the feature is only marked at t+confirmation_bars.

            pivots = pd.Series(0, index=series.index)

            # Using rolling to find max/min
            window = self.lookback + self.confirmation_bars + 1
            if pivot_type == PivotType.HIGH:
                rolling_max = series.rolling(window).max()
                # The extremum must have occurred exactly `confirmation_bars` ago
                is_extremum = (series.shift(self.confirmation_bars) == rolling_max)
                # Ensure it's strictly greater than recent values
                is_strict = (series.shift(self.confirmation_bars) > series.shift(self.confirmation_bars - 1).rolling(self.confirmation_bars).max())

                # Handling NaNs and combining conditions
                pivots.loc[is_extremum & is_strict] = 1
            else:
                rolling_min = series.rolling(window).min()
                is_extremum = (series.shift(self.confirmation_bars) == rolling_min)
                is_strict = (series.shift(self.confirmation_bars) < series.shift(self.confirmation_bars - 1).rolling(self.confirmation_bars).min())
                pivots.loc[is_extremum & is_strict] = 1

            return pivots.fillna(0).astype(int)

    def extract_pivot_points(self, series: pd.Series, pivot_type: PivotType, pivot_flags: pd.Series) -> List[PivotPoint]:
        """
        Extracts a list of PivotPoint objects from a Series and its pivot flags.
        """
        points = []

        # Iterate over non-zero flags
        active_flags = pivot_flags[pivot_flags == 1]

        for idx_label, val in active_flags.items():
            idx_pos = series.index.get_loc(idx_label)

            # For CONFIRMED_LAGGED, the actual pivot happened confirmation_bars ago
            actual_idx_pos = idx_pos
            actual_timestamp = idx_label
            actual_val = series.loc[idx_label]

            if self.mode == PivotMode.CONFIRMED_LAGGED:
                actual_idx_pos = idx_pos - self.confirmation_bars
                if actual_idx_pos >= 0:
                    actual_timestamp = series.index[actual_idx_pos]
                    actual_val = series.iloc[actual_idx_pos]
                else:
                    continue # Skip if out of bounds

            point = PivotPoint(
                timestamp=actual_timestamp,
                index_position=actual_idx_pos,
                pivot_type=pivot_type,
                value=float(actual_val),
                confirmed=(self.mode == PivotMode.CONFIRMED_LAGGED),
                confirmation_lag=self.confirmation_bars if self.mode == PivotMode.CONFIRMED_LAGGED else 0,
                metadata={"detected_at": idx_label}
            )
            points.append(point)

        return points

    def pair_recent_pivots(self, price_pivots: List[PivotPoint], indicator_pivots: List[PivotPoint], min_distance: int, max_distance: int) -> List[Tuple[PivotPoint, PivotPoint, PivotPoint, PivotPoint]]:
        """
        Pairs recent price and indicator pivots.
        Returns a list of tuples (price_pivot_1, price_pivot_2, ind_pivot_1, ind_pivot_2)
        where pivot_1 is the older pivot and pivot_2 is the newer pivot.
        """
        pairs = []

        # We need at least 2 pivots of each
        if len(price_pivots) < 2 or len(indicator_pivots) < 2:
            return pairs

        # Match nearest indicator pivot for each price pivot based on index position
        matched_indicator_pivots = {}
        for p_pivot in price_pivots:
            # Find closest indicator pivot (preferring same index or slightly before/after)
            closest_ind = None
            min_diff = float('inf')

            for i_pivot in indicator_pivots:
                diff = abs(p_pivot.index_position - i_pivot.index_position)
                # Indicator pivot shouldn't be too far from price pivot (e.g. max 2 bars diff)
                if diff < min_diff and diff <= 2:
                    min_diff = diff
                    closest_ind = i_pivot

            if closest_ind is not None:
                matched_indicator_pivots[p_pivot.index_position] = closest_ind

        # Now form pairs of (p1, p2)
        # We iterate over price pivots backwards
        for i in range(len(price_pivots) - 1, 0, -1):
            p2 = price_pivots[i]

            # Find a valid p1
            for j in range(i - 1, -1, -1):
                p1 = price_pivots[j]

                distance = p2.index_position - p1.index_position

                if distance < min_distance:
                    continue # Too close, look further back

                if distance > max_distance:
                    break # Too far, stop looking back for this p2

                # We have a valid price pivot pair (p1, p2). Now get matched ind pivots
                i1 = matched_indicator_pivots.get(p1.index_position)
                i2 = matched_indicator_pivots.get(p2.index_position)

                if i1 is not None and i2 is not None and i1.index_position < i2.index_position:
                    # Prevent matching the exact same indicator pivot
                    if i1.index_position != i2.index_position:
                        pairs.append((p1, p2, i1, i2))
                        # Normally we only want the most recent valid p1 for a given p2,
                        # but we can optionally collect multiple. Here we take the first valid one.
                        break

        return pairs
