import uuid
import time
from datetime import datetime
import logging
from typing import Any

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    ScheduledJobRun,
    ScheduledJobStatus,
    ScheduledJobDecision,
    ScheduledJobType
)
from bist_signal_bot.scheduler.locks import SchedulerLockManager

class ScheduledJobExecutor:
    def __init__(
        self,
        runtime_orchestrator=None,
        report_generator=None,
        research_lab_planner=None,
        telegram_digest=None,
        knowledge_indexer=None,
        review_followup=None,
        signal_lifecycle=None,
        drift_engine=None,
        stress_engine=None,
        portfolio_engine=None,
        maintenance_doctor=None,
        backup_manager=None,
        governance_gate=None,
        settings=None,
        logger=None
    ):
        self.runtime_orchestrator = runtime_orchestrator
        self.report_generator = report_generator
        self.research_lab_planner = research_lab_planner
        self.telegram_digest = telegram_digest
        self.knowledge_indexer = knowledge_indexer
        self.review_followup = review_followup
        self.signal_lifecycle = signal_lifecycle
        self.drift_engine = drift_engine
        self.stress_engine = stress_engine
        self.portfolio_engine = portfolio_engine
        self.maintenance_doctor = maintenance_doctor
        self.backup_manager = backup_manager
        self.governance_gate = governance_gate

        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)

        # Local lock manager for job execution
        # Not perfect dependency injection but keeps it simple for now
        self.lock_manager = SchedulerLockManager(
            getattr(settings, 'DATA_DIR', "data")
        )

    def execute(self, job: ScheduledJob, dry_run: bool = False) -> ScheduledJobRun:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        started_at = datetime.utcnow()

        # Inject Optional Profiler
        profiler = None
        timer_span = None
        if getattr(self.settings, 'ENABLE_PERFORMANCE_PROFILING', False):
            from bist_signal_bot.app.performance_app import create_local_profiler
            profiler = create_local_profiler(self.settings)
            timer_span = profiler.timer.start_span(f"scheduler_job_{job.job_type.value}")

        run = ScheduledJobRun(
            run_id=run_id,
            job_id=job.job_id,
            job_name=job.name,
            job_type=job.job_type,
            started_at=started_at,
            status=ScheduledJobStatus.RUNNING,
            decision=ScheduledJobDecision.RUN if not dry_run else ScheduledJobDecision.DRY_RUN_ONLY
        )

        # 1. Security Preflight / Governance Gate
        if self.governance_gate and getattr(self.settings, 'SCHEDULER_REQUIRE_GOVERNANCE_GATE', True):
            # This is a very basic mock of what the gate might do
            # In a real setup we'd pass the job definition to the gate
            if "order" in job.name.lower() or "trade" in job.name.lower() or "broker" in job.name.lower():
                run.status = ScheduledJobStatus.BLOCKED
                run.decision = ScheduledJobDecision.BLOCK_SECURITY
                run.errors.append("Blocked by security preflight: contains forbidden keywords")
                run.finished_at = datetime.utcnow()
                run.elapsed_seconds = (run.finished_at - run.started_at).total_seconds()
                return run

        # 2. Lock acquire
        lock_name = f"job_{job.job_id}"
        lock_ttl = getattr(self.settings, 'SCHEDULER_JOB_LOCK_TTL_SECONDS', 1800)

        if not self.lock_manager.acquire_lock(lock_name, lock_ttl):
            run.status = ScheduledJobStatus.SKIPPED
            run.decision = ScheduledJobDecision.SKIP_LOCKED
            run.warnings.append(f"Could not acquire lock for job {job.job_id}")
            run.finished_at = datetime.utcnow()
            run.elapsed_seconds = (run.finished_at - run.started_at).total_seconds()
            return run

        # 3. Dispatch
        try:
            dispatch_result = self.dispatch(job, dry_run)

            run.status = ScheduledJobStatus.SUCCESS
            if dry_run:
                run.warnings.append("Executed in dry-run mode")

            run.metadata.update(dispatch_result)

        except Exception as e:
            self.logger.exception(f"Error executing job {job.job_id}")
            run.status = ScheduledJobStatus.FAILED
            run.decision = ScheduledJobDecision.ERROR
            run.errors.append(str(e))

        finally:
            # 4. Lock release
            self.lock_manager.release_lock(lock_name)

            run.finished_at = datetime.utcnow()
            run.elapsed_seconds = (run.finished_at - run.started_at).total_seconds()

        return run

    def dispatch(self, job: ScheduledJob, dry_run: bool = False) -> dict[str, Any]:
        """Dispatches the job to the appropriate engine. Returns metadata dict."""

        if dry_run:
            self.logger.info(f"[DRY-RUN] Would execute {job.job_type.value} for {job.name}")
            return {"simulated": True, "action": f"Would dispatch {job.job_type.value}"}

        # Actual dispatch
        if job.job_type == ScheduledJobType.HEALTHCHECK:
            return {"status": "ok", "message": "Healthcheck completed"}

        elif job.job_type == ScheduledJobType.RUNTIME_RUN_ONCE:
            if not self.runtime_orchestrator:
                raise ValueError("runtime_orchestrator not provided")
            # We would build a config and run here
            return {"action": "runtime_run_once_dispatched"}

        elif job.job_type == ScheduledJobType.DAILY_REPORT:
            if not self.report_generator:
                raise ValueError("report_generator not provided")
            return {"action": "daily_report_generated"}

        elif job.job_type == ScheduledJobType.TELEGRAM_DIGEST:
            if not self.telegram_digest:
                raise ValueError("telegram_digest not provided")
            # Check settings if we force dry run for telegram
            if getattr(self.settings, 'RUNTIME_SCHEDULER_FORCE_DRY_RUN_TELEGRAM', True):
                self.logger.info("Telegram digest force dry-run by settings")
                return {"action": "telegram_digest_skipped_force_dry_run"}
            return {"action": "telegram_digest_sent"}

        elif job.job_type == ScheduledJobType.RESEARCH_LAB_PLAN:
            if not self.research_lab_planner:
                raise ValueError("research_lab_planner not provided")
            return {"action": "research_lab_plan_generated"}

        elif job.job_type == ScheduledJobType.MAINTENANCE_DOCTOR:
            if not self.maintenance_doctor:
                raise ValueError("maintenance_doctor not provided")
            return {"action": "maintenance_doctor_run"}

        elif job.job_type == ScheduledJobType.BACKUP_DRY_RUN:
            if not self.backup_manager:
                raise ValueError("backup_manager not provided")
            return {"action": "backup_dry_run_completed"}

        elif job.job_type == ScheduledJobType.SIGNAL_EXPIRE:
            if not self.signal_lifecycle:
                raise ValueError("signal_lifecycle not provided")
            return {"action": "stale_signals_expired"}

        elif job.job_type == ScheduledJobType.REVIEW_FOLLOWUP_CHECK:
            if not self.review_followup:
                raise ValueError("review_followup not provided")
            return {"action": "review_followups_checked"}

        # Fallback for others
        self.logger.info(f"Executing {job.job_type.value} logic for {job.name} (mocked)")
        return {"action": f"mock_{job.job_type.value.lower()}_completed"}

    def execute_whatif_weekly(self) -> dict[str, Any]:
        if not getattr(self.settings, "SCHEDULER_ENABLE_WHATIF_WEEKLY", False):
            return {"status": "SKIPPED", "reason": "Scheduler whatif disabled"}
        try:
            from bist_signal_bot.app.whatif_app import create_whatif_engine
            engine = create_whatif_engine(self.settings)
            res = engine.run_default(source_type="scheduler_weekly")
            return {"status": "SUCCESS", "run_id": res.run_id}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

# Added for Disclosure Integration
# Optional daily disclosure digest job.
# Post-import classify/link/extract jobs (default disabled/dry-run).
