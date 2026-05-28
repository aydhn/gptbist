import uuid
import pandas as pd
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthUniverseSnapshot
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.core.exceptions import BreadthInputError

class BreadthInputBuilder:
    def __init__(self, settings: Settings | None = None, data_service: MarketDataService | None = None):
        self.settings = settings or Settings()
        self.data_service = data_service or MarketDataService(self.settings)

    def build_inputs(self, universe: BreadthUniverseSnapshot, as_of: datetime | None = None) -> list[BreadthInputRow]:
        inputs = []
        for symbol in universe.symbols:
            try:
                row = self.input_for_symbol(symbol, as_of=as_of)
                if row:
                    row.sector = universe.sectors.get(symbol, "UNKNOWN")
                    inputs.append(row)
            except Exception as e:
                pass # Skip failed symbols
        return inputs

    def input_for_symbol(self, symbol: str, as_of: datetime | None = None) -> BreadthInputRow | None:
        try:
            df = self.data_service.get_adjusted_ohlcv(symbol)
            if df.empty:
                return None

            if as_of:
                # Filter up to as_of
                df = df[df.index <= pd.to_datetime(as_of).tz_localize(None)]
                if df.empty:
                    return None

            # Ensure we have enough data for long windows
            if len(df) < 2:
                return None

            current_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            close = float(current_row['Close'])
            prev_close = float(prev_row['Close'])
            volume = float(current_row['Volume']) if 'Volume' in current_row else None

            warnings = []
            if volume is None or volume < 0:
                if self.settings.BREADTH_REQUIRE_VOLUME:
                    return None
                volume = 0.0
                warnings.append(f"Missing or negative volume for {symbol}")

            closes = df['Close'].tolist()
            highs = df['High'].tolist() if 'High' in df.columns else closes
            lows = df['Low'].tolist() if 'Low' in df.columns else closes

            # Parse windows
            ma_windows = [int(x.strip()) for x in self.settings.BREADTH_MA_WINDOWS.split(",") if x.strip().isdigit()]
            ma_20 = self.moving_average(closes, 20) if 20 in ma_windows else None
            ma_50 = self.moving_average(closes, 50) if 50 in ma_windows else None
            ma_200 = self.moving_average(closes, 200) if 200 in ma_windows else None

            short_window = self.settings.BREADTH_HIGH_LOW_SHORT_WINDOW
            long_window = self.settings.BREADTH_HIGH_LOW_LONG_WINDOW

            high_20d = self.rolling_high(highs, short_window)
            low_20d = self.rolling_low(lows, short_window)
            high_252d = self.rolling_high(highs, long_window)
            low_252d = self.rolling_low(lows, long_window)

            return BreadthInputRow(
                row_id=str(uuid.uuid4()),
                symbol=symbol,
                as_of=as_of or datetime.now(),
                close=close,
                previous_close=prev_close,
                volume=volume,
                turnover=None,
                ma_20=ma_20,
                ma_50=ma_50,
                ma_200=ma_200,
                high_20d=high_20d,
                low_20d=low_20d,
                high_252d=high_252d,
                low_252d=low_252d,
                return_1d_pct=self.return_1d_pct(close, prev_close),
                warnings=warnings
            )
        except Exception as e:
            return None

    def moving_average(self, values: list[float], window: int) -> float | None:
        if not values or len(values) < window or window <= 0:
            return None
        return sum(values[-window:]) / window

    def rolling_high(self, values: list[float], window: int) -> float | None:
        if not values or len(values) < window or window <= 0:
            return None
        return max(values[-window:])

    def rolling_low(self, values: list[float], window: int) -> float | None:
        if not values or len(values) < window or window <= 0:
            return None
        return min(values[-window:])

    def return_1d_pct(self, close: float | None, previous_close: float | None) -> float | None:
        if close is None or previous_close is None or previous_close <= 0:
            return None
        return ((close - previous_close) / previous_close) * 100.0
