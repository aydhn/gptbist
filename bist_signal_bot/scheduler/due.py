from datetime import datetime
import logging

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    MarketSessionSnapshot,
    DueJobResult,
    ScheduledJobDecision,
    ScheduledJobType
)
from bist_signal_bot.scheduler.triggers import ScheduleTriggerEvaluator
from bist_signal_bot.scheduler.session import MarketSessionResolver

logger = logging.getLogger(__name__)

class DueJobFinder:
    def __init__(self, trigger_evaluator: ScheduleTriggerEvaluator, session_resolver: MarketSessionResolver):
        self.trigger_evaluator = trigger_evaluator
        self.session_resolver = session_resolver

        # Execution priority order
        self.priority_order = [
            ScheduledJobType.HEALTHCHECK,
            ScheduledJobType.MAINTENANCE_DOCTOR,
            ScheduledJobType.SIGNAL_EXPIRE,
            ScheduledJobType.REVIEW_FOLLOWUP_CHECK,
            ScheduledJobType.RUNTIME_RUN_ONCE,
            ScheduledJobType.PORTFOLIO_RESEARCH,
            ScheduledJobType.STRESS_TEST,
            ScheduledJobType.DRIFT_CHECK,
            ScheduledJobType.KNOWLEDGE_INDEX,
            ScheduledJobType.DAILY_REPORT,
            ScheduledJobType.TELEGRAM_DIGEST,
            ScheduledJobType.RESEARCH_LAB_PLAN,
            ScheduledJobType.GOVERNANCE_AUDIT,
            ScheduledJobType.BACKUP_DRY_RUN,
        ]

    def find_due_jobs(self, jobs: list[ScheduledJob], now: datetime | None = None) -> DueJobResult:
        if now is None:
            now = datetime.now()

        session_snapshot = self.session_resolver.current_session(now)

        due_jobs = []
        skipped_jobs = []
        blocked_jobs = []
        warnings = []

        for job in jobs:
            decision, reason = self.classify_job(job, now, session_snapshot)

            if decision == ScheduledJobDecision.RUN or decision == ScheduledJobDecision.DRY_RUN_ONLY:
                due_jobs.append(job)
            elif decision in (ScheduledJobDecision.SKIP_DISABLED, ScheduledJobDecision.SKIP_NOT_DUE,
                              ScheduledJobDecision.SKIP_MARKET_CLOSED, ScheduledJobDecision.SKIP_COOLDOWN,
                              ScheduledJobDecision.SKIP_LOCKED):
                skipped_jobs.append(job)
            elif decision in (ScheduledJobDecision.BLOCK_GOVERNANCE, ScheduledJobDecision.BLOCK_SECURITY):
                blocked_jobs.append(job)
                warnings.append(f"Job {job.name} blocked: {reason}")
            else:
                warnings.append(f"Job {job.name} unhandled decision: {decision}")

        return DueJobResult(
            generated_at=now,
            session_snapshot=session_snapshot,
            due_jobs=self.sort_due_jobs(due_jobs),
            skipped_jobs=skipped_jobs,
            blocked_jobs=blocked_jobs,
            warnings=warnings
        )

    def classify_job(self, job: ScheduledJob, now: datetime, session: MarketSessionSnapshot) -> tuple[ScheduledJobDecision, str]:
        if not job.enabled:
            return ScheduledJobDecision.SKIP_DISABLED, "Job is disabled"

        allowed, reason = self.session_resolver.allowed_for_job(job, session)
        if not allowed:
            return ScheduledJobDecision.SKIP_MARKET_CLOSED, reason

        is_due, reason = self.trigger_evaluator.is_due(job, now, session)
        if not is_due:
            if "cooldown" in reason.lower():
                return ScheduledJobDecision.SKIP_COOLDOWN, reason
            return ScheduledJobDecision.SKIP_NOT_DUE, reason

        return ScheduledJobDecision.RUN, "Job is due"

    def sort_due_jobs(self, jobs: list[ScheduledJob]) -> list[ScheduledJob]:
        def get_priority(job: ScheduledJob) -> int:
            try:
                return self.priority_order.index(job.job_type)
            except ValueError:
                return len(self.priority_order) # Custom/unknown types go last

        return sorted(jobs, key=get_priority)
