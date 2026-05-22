from datetime import datetime, timedelta
import logging

from bist_signal_bot.scheduler.models import ScheduledJob, ScheduledJobRun

logger = logging.getLogger(__name__)

class ScheduledJobDeduplicator:
    def build_run_key(self, job: ScheduledJob, now: datetime) -> str:
        # Key based on job_id and the current hour/minute depending on trigger
        # For simplicity, we just use job_id and rely on time window filtering
        return job.job_id

    def is_duplicate_run(self, job: ScheduledJob, recent_runs: list[ScheduledJobRun], dedupe_minutes: int) -> bool:
        if dedupe_minutes <= 0:
            return False

        now = datetime.utcnow()
        window_start = now - timedelta(minutes=dedupe_minutes)

        for run in recent_runs:
            if run.job_id == job.job_id and run.started_at >= window_start:
                return True

        return False

    def filter_duplicate_due_jobs(
        self,
        jobs: list[ScheduledJob],
        recent_runs: list[ScheduledJobRun],
        dedupe_minutes: int
    ) -> tuple[list[ScheduledJob], list[ScheduledJob]]:
        unique_jobs = []
        duplicate_jobs = []

        for job in jobs:
            if self.is_duplicate_run(job, recent_runs, dedupe_minutes):
                duplicate_jobs.append(job)
            else:
                unique_jobs.append(job)

        return unique_jobs, duplicate_jobs
