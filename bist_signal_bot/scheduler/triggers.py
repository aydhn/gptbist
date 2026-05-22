from datetime import datetime, timedelta
import logging

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    ScheduleTrigger,
    MarketSessionSnapshot,
    ScheduleTriggerType,
    MarketDayType
)

logger = logging.getLogger(__name__)

class ScheduleTriggerEvaluator:
    def is_due(self, job: ScheduledJob, now: datetime, session: MarketSessionSnapshot) -> tuple[bool, str]:
        if not job.enabled:
            return False, "Job is disabled"

        # Trading day checks
        if job.trigger.only_trading_days and session.day_type not in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY):
            return False, "Only runs on trading days"

        if job.trigger.skip_holidays and session.day_type == MarketDayType.HOLIDAY:
            return False, "Skipping holiday"

        # Cooldown check
        if job.last_run_at:
            cooldown_delta = timedelta(minutes=job.cooldown_minutes)
            if now < job.last_run_at + cooldown_delta:
                return False, f"In cooldown until {job.last_run_at + cooldown_delta}"

        trigger_type = job.trigger.trigger_type

        if trigger_type == ScheduleTriggerType.DAILY:
            is_due = self.daily_due(job.trigger, now)
            return is_due, "Daily trigger due" if is_due else "Not time for daily trigger"

        elif trigger_type == ScheduleTriggerType.WEEKLY:
            is_due = self.weekly_due(job.trigger, now)
            return is_due, "Weekly trigger due" if is_due else "Not time for weekly trigger"

        elif trigger_type == ScheduleTriggerType.INTERVAL_MINUTES:
            is_due = self.interval_due(job, now)
            return is_due, "Interval trigger due" if is_due else "Interval not elapsed"

        elif trigger_type == ScheduleTriggerType.MARKET_SESSION:
            is_due = self.market_session_due(job.trigger, session)
            return is_due, "Market session trigger due" if is_due else "Not in required market session"

        elif trigger_type == ScheduleTriggerType.MANUAL:
            return False, "Manual trigger only"

        return False, f"Unsupported trigger type: {trigger_type}"

    def next_run_time(self, job: ScheduledJob, now: datetime) -> datetime | None:
        # Simplified prediction for UI/logs
        if job.trigger.trigger_type == ScheduleTriggerType.INTERVAL_MINUTES and job.trigger.interval_minutes:
            if job.last_run_at:
                return job.last_run_at + timedelta(minutes=job.trigger.interval_minutes)
            return now
        return None

    def daily_due(self, trigger: ScheduleTrigger, now: datetime) -> bool:
        if trigger.hour is None or trigger.minute is None:
            return False

        # Due if we are exactly at or slightly past the scheduled time (within 5 mins grace period)
        scheduled_time = now.replace(hour=trigger.hour, minute=trigger.minute, second=0, microsecond=0)
        return scheduled_time <= now <= (scheduled_time + timedelta(minutes=5))

    def weekly_due(self, trigger: ScheduleTrigger, now: datetime) -> bool:
        if now.weekday() not in trigger.weekdays:
            return False
        return self.daily_due(trigger, now)

    def interval_due(self, job: ScheduledJob, now: datetime) -> bool:
        if not job.trigger.interval_minutes:
            return False

        if not job.last_run_at:
            return True

        next_run = job.last_run_at + timedelta(minutes=job.trigger.interval_minutes)
        return now >= next_run

    def market_session_due(self, trigger: ScheduleTrigger, session: MarketSessionSnapshot) -> bool:
        if not trigger.market_sessions:
            return False
        return session.session_type in trigger.market_sessions
