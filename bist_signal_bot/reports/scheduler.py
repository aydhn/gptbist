from datetime import datetime, timedelta
from bist_signal_bot.reports.models import ReportType

class ReportScheduleHelper:
    def should_generate_daily(self, now: datetime | None = None) -> bool:
        return True # Simplified

    def should_generate_weekly(self, now: datetime | None = None) -> bool:
        return True # Simplified

    def build_runtime_report_job_config(self) -> dict[str, bool]:
        return {"generate": True}

    def next_report_time(self, report_type: ReportType, now: datetime | None = None) -> datetime:
        now = now or datetime.utcnow()
        return now + timedelta(hours=24)
