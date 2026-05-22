import uuid
from datetime import datetime
import logging
from typing import Any

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    ScheduledJobRun,
    SchedulerRunResult,
    ScheduledJobStatus,
    ScheduledJobType,
    ScheduleTrigger,
    ScheduleTriggerType,
    MarketSessionType
)

logger = logging.getLogger(__name__)

class LocalSchedulerOrchestrator:
    def __init__(
        self,
        store,
        calendar,
        session_resolver,
        trigger_evaluator,
        due_finder,
        lock_manager,
        deduplicator,
        executor,
        settings=None,
        logger=None
    ):
        self.store = store
        self.calendar = calendar
        self.session_resolver = session_resolver
        self.trigger_evaluator = trigger_evaluator
        self.due_finder = due_finder
        self.lock_manager = lock_manager
        self.deduplicator = deduplicator
        self.executor = executor

        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)

    def run_due(self, now: datetime | None = None, dry_run: bool = False, limit: int | None = None) -> SchedulerRunResult:
        if now is None:
            now = datetime.utcnow()

        run_id = f"sch_{uuid.uuid4().hex[:8]}"
        started_at = now

        result = SchedulerRunResult(
            scheduler_run_id=run_id,
            started_at=started_at,
            status=ScheduledJobStatus.RUNNING
        )

        # Global lock
        global_lock_name = "scheduler_run_due_global"
        global_lock_ttl = getattr(self.settings, 'SCHEDULER_GLOBAL_LOCK_TTL_SECONDS', 3600)

        if not self.lock_manager.acquire_lock(global_lock_name, global_lock_ttl):
            self.logger.warning("Could not acquire global scheduler lock. Another run_due is likely active.")
            result.status = ScheduledJobStatus.SKIPPED
            result.warnings.append("Skipped due to global lock")
            result.finished_at = datetime.utcnow()
            return result

        try:
            # 1. Load jobs
            jobs = self.store.load_jobs()

            # 2. Find due
            due_result = self.due_finder.find_due_jobs(jobs, now)
            result.due_result = due_result

            due_jobs = due_result.due_jobs

            # 3. Dedupe
            dedupe_window = getattr(self.settings, 'SCHEDULER_DEDUPE_WINDOW_MINUTES', 30)
            recent_runs = []
            if due_jobs and dedupe_window > 0:
                # Naive load, in a real system we'd query by date
                recent_runs = self.store.load_runs(limit=100)

            unique_due, dupes = self.deduplicator.filter_duplicate_due_jobs(due_jobs, recent_runs, dedupe_window)

            if dupes:
                result.warnings.append(f"Filtered {len(dupes)} duplicate jobs")
                due_result.skipped_jobs.extend(dupes)

            # 4. Limit
            actual_limit = limit or getattr(self.settings, 'SCHEDULER_RUN_DUE_LIMIT', 10)
            jobs_to_run = unique_due[:actual_limit]

            if len(unique_due) > actual_limit:
                result.warnings.append(f"Limited run to {actual_limit} out of {len(unique_due)} due jobs")

            # 5. Execute
            runs = []
            success_count = 0
            failed_count = 0

            for job in jobs_to_run:
                run = self.executor.execute(job, dry_run=dry_run)
                runs.append(run)

                # Update job last run time if not dry run
                if not dry_run and run.status == ScheduledJobStatus.SUCCESS:
                    job.last_run_at = now
                    job.updated_at = now
                    self.store.update_job(job)

                self.store.append_run(run)

                if run.status == ScheduledJobStatus.SUCCESS:
                    success_count += 1
                elif run.status == ScheduledJobStatus.FAILED:
                    failed_count += 1

            result.job_runs = runs
            result.success_count = success_count
            result.failed_count = failed_count
            result.skipped_count = len(due_result.skipped_jobs)
            result.blocked_count = len(due_result.blocked_jobs)

            result.status = ScheduledJobStatus.SUCCESS

        except Exception as e:
            self.logger.exception("Error in scheduler run_due")
            result.status = ScheduledJobStatus.FAILED
            result.errors.append(str(e))

        finally:
            self.lock_manager.release_lock(global_lock_name)
            result.finished_at = datetime.utcnow()
            result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

            # Save result
            self.store.save_scheduler_run(result)

        return result

    def list_jobs(self, enabled_only: bool = False) -> list[ScheduledJob]:
        jobs = self.store.load_jobs()
        if enabled_only:
            return [j for j in jobs if j.enabled]
        return jobs

    def add_job(self, job: ScheduledJob, confirm: bool = False) -> ScheduledJob:
        if not confirm:
            self.logger.info("add_job requires confirm=True")
            return job
        self.store.save_job(job)
        return job

    def enable_job(self, job_id: str, confirm: bool = False) -> ScheduledJob:
        job = self.store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if confirm:
            job.enabled = True
            job.updated_at = datetime.utcnow()
            self.store.update_job(job)
        return job

    def disable_job(self, job_id: str, confirm: bool = False) -> ScheduledJob:
        job = self.store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if confirm:
            job.enabled = False
            job.updated_at = datetime.utcnow()
            self.store.update_job(job)
        return job

    def run_job(self, job_id: str, dry_run: bool = False, confirm: bool = False) -> ScheduledJobRun:
        if not dry_run and not confirm:
            raise ValueError("Must provide confirm=True for non-dry-run manual execution")

        job = self.store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        run = self.executor.execute(job, dry_run=dry_run)

        if not dry_run and run.status == ScheduledJobStatus.SUCCESS:
            job.last_run_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            self.store.update_job(job)

        self.store.append_run(run)
        return run

    def history(self, limit: int = 100) -> list[ScheduledJobRun]:
        return self.store.load_runs(limit=limit)

    def default_jobs(self) -> list[ScheduledJob]:
        now = datetime.utcnow()
        jobs = []

        # 1. Healthcheck (Daily, Pre-market)
        jobs.append(ScheduledJob(
            job_id="job_default_healthcheck",
            name="Daily Healthcheck",
            job_type=ScheduledJobType.HEALTHCHECK,
            status=ScheduledJobStatus.ENABLED,
            trigger=ScheduleTrigger(
                trigger_id="trg_healthcheck",
                trigger_type=ScheduleTriggerType.MARKET_SESSION,
                timezone="Europe/Istanbul",
                market_sessions=[MarketSessionType.PRE_MARKET],
                only_trading_days=True
            ),
            created_at=now,
            updated_at=now
        ))

        # 2. Daily Report (Daily, Post-market)
        jobs.append(ScheduledJob(
            job_id="job_default_daily_report",
            name="Daily Research Report",
            job_type=ScheduledJobType.DAILY_REPORT,
            status=ScheduledJobStatus.ENABLED,
            trigger=ScheduleTrigger(
                trigger_id="trg_daily_report",
                trigger_type=ScheduleTriggerType.MARKET_SESSION,
                timezone="Europe/Istanbul",
                market_sessions=[MarketSessionType.POST_MARKET],
                only_trading_days=True
            ),
            created_at=now,
            updated_at=now
        ))

        # 3. Maintenance Doctor (Weekly)
        jobs.append(ScheduledJob(
            job_id="job_default_maintenance_doctor",
            name="Weekly Maintenance Doctor",
            job_type=ScheduledJobType.MAINTENANCE_DOCTOR,
            status=ScheduledJobStatus.ENABLED,
            trigger=ScheduleTrigger(
                trigger_id="trg_maintenance",
                trigger_type=ScheduleTriggerType.WEEKLY,
                timezone="Europe/Istanbul",
                hour=2,
                minute=0,
                weekdays=[6] # Sunday
            ),
            created_at=now,
            updated_at=now
        ))

        return jobs
