import csv
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Optional

from bist_signal_bot.scheduler.models import MarketDayType, MarketCalendarDay
from bist_signal_bot.core.exceptions import MarketCalendarError

logger = logging.getLogger(__name__)

class BISTMarketCalendar:
    def __init__(self, data_dir: Path | str = "data"):
        self.data_dir = Path(data_dir)
        self.calendar_file = self.data_dir / "scheduler" / "calendar" / "bist_holidays.csv"
        self._holidays: dict[datetime.date, MarketCalendarDay] = {}
        self._loaded = False

    def load_calendar(self) -> list[MarketCalendarDay]:
        days = []
        if not self.calendar_file.exists():
            logger.warning(f"Calendar file not found: {self.calendar_file}. Relying on default weekend checks.")
            self._loaded = True
            return days

        try:
            with open(self.calendar_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        # convert date back to a naive datetime at midnight for our model
                        dt = datetime.combine(date_obj, datetime.min.time())

                        day_type = MarketDayType(row.get('day_type', 'UNKNOWN'))
                        day = MarketCalendarDay(
                            date=dt,
                            day_type=day_type,
                            description=row.get('description'),
                            open_time=row.get('open_time'),
                            close_time=row.get('close_time'),
                            half_day_close_time=row.get('half_day_close_time')
                        )
                        days.append(day)
                        self._holidays[date_obj] = day
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing calendar row {row}: {e}")
            self._loaded = True
            return days
        except Exception as e:
            raise MarketCalendarError(f"Failed to load calendar from {self.calendar_file}: {e}")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load_calendar()

    def get_day(self, date: datetime) -> MarketCalendarDay:
        self._ensure_loaded()
        dt_date = date.date()

        if dt_date in self._holidays:
            day = self._holidays[dt_date]
            # Create a new instance matching the requested datetime
            return MarketCalendarDay(
                date=date,
                day_type=day.day_type,
                description=day.description,
                open_time=day.open_time,
                close_time=day.close_time,
                half_day_close_time=day.half_day_close_time,
                metadata=day.metadata.copy()
            )

        # Default fallback
        if dt_date.weekday() >= 5: # Saturday = 5, Sunday = 6
            return MarketCalendarDay(date=date, day_type=MarketDayType.WEEKEND)
        return MarketCalendarDay(date=date, day_type=MarketDayType.TRADING_DAY)

    def is_trading_day(self, date: datetime) -> bool:
        day = self.get_day(date)
        return day.day_type in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY)

    def is_holiday(self, date: datetime) -> bool:
        return self.get_day(date).day_type == MarketDayType.HOLIDAY

    def is_half_day(self, date: datetime) -> bool:
        return self.get_day(date).day_type == MarketDayType.HALF_DAY

    def next_trading_day(self, date: datetime) -> MarketCalendarDay:
        current = date + timedelta(days=1)
        # Prevent infinite loops in case calendar is fully blocked (unlikely)
        for _ in range(365):
            day = self.get_day(current)
            if day.day_type in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY):
                return day
            current += timedelta(days=1)
        raise MarketCalendarError("Could not find next trading day within 1 year")

    def previous_trading_day(self, date: datetime) -> MarketCalendarDay:
        current = date - timedelta(days=1)
        for _ in range(365):
            day = self.get_day(current)
            if day.day_type in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY):
                return day
            current -= timedelta(days=1)
        raise MarketCalendarError("Could not find previous trading day within 1 year")

    def import_calendar_file(self, path: Path, confirm: bool = False) -> int:
        if not confirm:
            logger.info("Import requires confirm=True")
            return 0

        if not path.exists():
            raise MarketCalendarError(f"File not found: {path}")

        # Ensure target dir exists
        self.calendar_file.parent.mkdir(parents=True, exist_ok=True)

        # Simple copy
        try:
            with open(path, 'r', encoding='utf-8') as src, \
                 open(self.calendar_file, 'w', encoding='utf-8', newline='') as dst:
                content = src.read()
                dst.write(content)

            self._loaded = False
            days = self.load_calendar()
            return len(days)
        except Exception as e:
            raise MarketCalendarError(f"Failed to import calendar: {e}")
