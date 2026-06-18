import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    ScheduledJobRun,
    SchedulerRunResult,
    ScheduleTrigger,
    ScheduledJobType,
    ScheduledJobStatus,
    ScheduledJobDecision,
    ScheduleTriggerType,
    MarketSessionType
)
from bist_signal_bot.storage.paths import get_scheduler_dir

logger = logging.getLogger(__name__)

class SchedulerStore:
    def __init__(self, data_dir: Path | str = "data"):
        self.scheduler_dir = Path(data_dir) / "scheduler"
        self.jobs_file = self.scheduler_dir / "jobs" / "scheduled_jobs.jsonl"
        self.runs_file = self.scheduler_dir / "runs" / "scheduled_job_runs.jsonl"

        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self.runs_file.parent.mkdir(parents=True, exist_ok=True)

    def _job_to_dict(self, job: ScheduledJob) -> dict:
        d = {
            "job_id": job.job_id,
            "name": job.name,
            "job_type": job.job_type.value,
            "status": job.status.value,
            "trigger": {
                "trigger_id": job.trigger.trigger_id,
                "trigger_type": job.trigger.trigger_type.value,
                "timezone": job.trigger.timezone,
                "hour": job.trigger.hour,
                "minute": job.trigger.minute,
                "weekdays": job.trigger.weekdays,
                "interval_minutes": job.trigger.interval_minutes,
                "market_sessions": [s.value for s in job.trigger.market_sessions],
                "only_trading_days": job.trigger.only_trading_days,
                "skip_holidays": job.trigger.skip_holidays,
                "metadata": job.trigger.metadata
            },
            "command_preview": job.command_preview,
            "enabled": job.enabled,
            "dry_run": job.dry_run,
            "requires_market_open": job.requires_market_open,
            "allow_after_hours": job.allow_after_hours,
            "cooldown_minutes": job.cooldown_minutes,
            "max_runtime_seconds": job.max_runtime_seconds,
            "max_retries": job.max_retries,
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
            "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "metadata": job.metadata,
            "warnings": job.warnings
        }
        return d

    def _dict_to_job(self, d: dict) -> ScheduledJob:
        td = d["trigger"]
        trigger = ScheduleTrigger(
            trigger_id=td["trigger_id"],
            trigger_type=ScheduleTriggerType(td["trigger_type"]),
            timezone=td["timezone"],
            hour=td.get("hour"),
            minute=td.get("minute"),
            weekdays=td.get("weekdays", []),
            interval_minutes=td.get("interval_minutes"),
            market_sessions=[MarketSessionType(s) for s in td.get("market_sessions", [])],
            only_trading_days=td.get("only_trading_days", False),
            skip_holidays=td.get("skip_holidays", False),
            metadata=td.get("metadata", {})
        )

        return ScheduledJob(
            job_id=d["job_id"],
            name=d["name"],
            job_type=ScheduledJobType(d["job_type"]),
            status=ScheduledJobStatus(d.get("status", "UNKNOWN")),
            trigger=trigger,
            command_preview=d.get("command_preview", []),
            enabled=d.get("enabled", True),
            dry_run=d.get("dry_run", True),
            requires_market_open=d.get("requires_market_open", False),
            allow_after_hours=d.get("allow_after_hours", True),
            cooldown_minutes=d.get("cooldown_minutes", 30),
            max_runtime_seconds=d.get("max_runtime_seconds", 3600),
            max_retries=d.get("max_retries", 0),
            last_run_at=datetime.fromisoformat(d["last_run_at"]) if d.get("last_run_at") else None,
            next_run_at=datetime.fromisoformat(d["next_run_at"]) if d.get("next_run_at") else None,
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            metadata=d.get("metadata", {}),
            warnings=d.get("warnings", [])
        )

    def save_job(self, job: ScheduledJob) -> Path:
        jobs = self.load_jobs()
        # Remove if exists
        jobs = [j for j in jobs if j.job_id != job.job_id]
        jobs.append(job)

        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            for j in jobs:
                f.write(json.dumps(self._job_to_dict(j)) + '\n')
        return self.jobs_file

    def load_jobs(self, limit: int = 1000) -> list[ScheduledJob]:
        if not self.jobs_file.exists():
            return []

        jobs = []
        with open(self.jobs_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    jobs.append(self._dict_to_job(json.loads(line)))
                except Exception as e:
                    logger.warning(f"Failed to parse job line: {e}")
        return jobs

    def get_job(self, job_id: str) -> ScheduledJob | None:
        jobs = self.load_jobs()
        for j in jobs:
            if j.job_id == job_id:
                return j
        return None

    def update_job(self, job: ScheduledJob) -> Path:
        return self.save_job(job)

    def append_run(self, run: ScheduledJobRun) -> Path:
        d = {
            "run_id": run.run_id,
            "job_id": run.job_id,
            "job_name": run.job_name,
            "job_type": run.job_type.value,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "status": run.status.value,
            "decision": run.decision.value,
            "elapsed_seconds": run.elapsed_seconds,
            "exit_code": run.exit_code,
            "output_refs": run.output_refs,
            "warnings": run.warnings,
            "errors": run.errors,
            "disclaimer": run.disclaimer,
            "metadata": run.metadata
        }

        with open(self.runs_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(d) + '\n')

        return self.runs_file

    def load_runs(self, job_id: str | None = None, limit: int = 1000) -> list[ScheduledJobRun]:
        if not self.runs_file.exists():
            return []

        runs = []
        # Load all, filter, sort (descending), limit - inefficient for huge files but ok for local MVP
        with open(self.runs_file, 'r', encoding='utf-8') as f:
            lines = [line for line in f if line.strip()]

        for line in reversed(lines): # Read backwards
            try:
                d = json.loads(line)
                if job_id and d.get("job_id") != job_id:
                    continue

                # We won't reconstruct the full object here to save time for this mock,
                # but we'll return a basic parsed dict
                runs.append(d)
                if len(runs) >= limit:
                    break
            except Exception:
                pass

        res = []
        for d in runs:
            run = ScheduledJobRun(
                run_id=d["run_id"],
                job_id=d["job_id"],
                job_name=d["job_name"],
                job_type=ScheduledJobType(d["job_type"]),
                started_at=datetime.fromisoformat(d["started_at"]),
                finished_at=datetime.fromisoformat(d["finished_at"]) if d.get("finished_at") else None,
                status=ScheduledJobStatus(d.get("status", "UNKNOWN")),
                decision=ScheduledJobDecision(d.get("decision", "ERROR")),
                elapsed_seconds=d.get("elapsed_seconds", 0.0),
                exit_code=d.get("exit_code"),
                output_refs=d.get("output_refs", {}),
                warnings=d.get("warnings", []),
                errors=d.get("errors", []),
                disclaimer=d.get("disclaimer", "Scheduled job run is research-only. Not investment advice. No real order was sent."),
                metadata=d.get("metadata", {})
            )
            res.append(run)

        return res

    def save_scheduler_run(self, result: SchedulerRunResult) -> dict[str, Path]:
        # Would save to reports folder
        return {}
