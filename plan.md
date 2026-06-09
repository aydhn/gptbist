1.  *Update `DataQualityChecker` constructor in `bist_signal_bot/data/quality.py`.*
    - Add an optional `market_calendar` parameter of type `BistMarketCalendar | None = None`. Add `from bist_signal_bot.calendar.market_calendar import BistMarketCalendar` to the imports.
2.  *Update `_check_large_date_gaps` method.*
    - When checking for large gaps, initially filter `gaps > pd.Timedelta(days=self.max_allowed_gap_days)` as candidate gaps.
    - If `self.market_calendar` is provided, evaluate each candidate gap by calculating `missing_trading_days = sum(1 for d in self.market_calendar.trading_days_between(start_date.date(), end_date.date()) if start_date.date() < d < end_date.date())`.
    - If `missing_trading_days > self.max_allowed_gap_days` (or if no calendar is provided and calendar gap > max_allowed_gap_days), consider it a real large date gap.
3.  *Add test logic in `bist_signal_bot/tests/test_data_quality.py`.*
    - Add test cases to verify the gap logic with and without `market_calendar`, particularly for dates spanning a weekend or holiday.
4.  *Complete pre commit steps.*
    - Complete pre commit steps to make sure proper testing, verifications, reviews and reflections are done.
