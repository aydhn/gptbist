import re
import uuid
import time
import subprocess
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from bist_signal_bot.research_lab.models import (
    ResearchJob, ResearchJobResult, ResearchJobStatus, ResearchBatchPlan,
    ResearchBatchRun, ResearchLabPolicy, ResearchJobRiskLevel
)
from bist_signal_bot.core.exceptions import ResearchJobExecutionError
from bist_signal_bot.core.audit import AuditLogger, AuditEventType
from bist_signal_bot.research_lab.storage import ResearchLabStore
from bist_signal_bot.research_lab.queue import ResearchJobQueue

logger = logging.getLogger(__name__)

class ResearchJobExecutor:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self.audit = AuditLogger(settings)
        self.store = ResearchLabStore(settings, base_dir)
        self.queue = ResearchJobQueue(settings, base_dir)

    def execute_job(self, job: ResearchJob, policy: ResearchLabPolicy) -> ResearchJobResult:
        result = ResearchJobResult(
            result_id=f"res_{uuid.uuid4().hex[:8]}",
            job_id=job.job_id,
            status=ResearchJobStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        if job.risk_level == ResearchJobRiskLevel.REQUIRES_CONFIRM:
             if not getattr(self, '_confirm_heavy_override', False):
                 result.status = ResearchJobStatus.BLOCKED
                 result.errors.append("Job requires confirmation but was executed in an automated batch without override.")
                 return self._finalize_result(result)
        if job.max_runtime_seconds > policy.max_runtime_seconds_per_job:
            job.max_runtime_seconds = policy.max_runtime_seconds_per_job

        env = {
            "BIST_BOT_DISABLE_TELEGRAM": "true",
            "BIST_BOT_FORCE_RESEARCH_ONLY": "true",
            "BIST_BOT_ALLOW_BROKER": "false"
        }
        try:
            if job.command_preview:
                exit_code, stdout, stderr = self.execute_command(job.command_preview, job.max_runtime_seconds, env)
                result.exit_code = exit_code
                result.stdout_tail = stdout[-1000:] if stdout else ""
                result.stderr_tail = stderr[-1000:] if stderr else ""
                if exit_code == 0:
                    result.status = ResearchJobStatus.SUCCESS
                elif exit_code == 124:
                    result.status = ResearchJobStatus.TIMEOUT
                    result.errors.append("Command timed out")
                else:
                    result.status = ResearchJobStatus.FAILED
                    result.errors.append(f"Command failed with code {exit_code}")
            else:
                result = self.dispatch_internal(job)
        except Exception as e:
            logger.exception(f"Error executing job {job.job_id}")
            result.status = ResearchJobStatus.FAILED
            result.errors.append(str(e))
        return self._finalize_result(result)

    def _finalize_result(self, result: ResearchJobResult) -> ResearchJobResult:
        result.finished_at = datetime.utcnow()
        result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()
        return result

    def dispatch_internal(self, job: ResearchJob) -> ResearchJobResult:
        result = ResearchJobResult(
            result_id=f"res_{uuid.uuid4().hex[:8]}",
            job_id=job.job_id,
            status=ResearchJobStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        result.status = ResearchJobStatus.SUCCESS
        result.metadata["dispatched_internal"] = True
        return self._finalize_result(result)

    def execute_command(self, command: List[str], timeout_seconds: int, env: Dict[str, str]) -> Tuple[int, str, str]:
        import os
        import sys

        # Security validation: strictly allow only bist_signal_bot module execution
        if not command or len(command) < 3:
            return 1, "", f"Security Error: Command too short or empty."

        if command[0] not in ("python", sys.executable) or command[1] != "-m" or command[2] != "bist_signal_bot":
            return 1, "", f"Security Error: Unauthorized command execution blocked. Only 'python -m bist_signal_bot' is allowed."

        command[0] = sys.executable

        # Security validation: strict whitelist of allowed characters for arguments to prevent command injection
        # Allows alphanumeric, dash, underscore, and equals. Disallows shell metacharacters and arbitrary scripts.
        allowed_pattern = re.compile(r'^[a-zA-Z0-9_=-]+$')
        for arg in command[3:]:
            if not allowed_pattern.match(arg):
                return 1, "", f"Security Error: Argument '{arg}' contains unauthorized characters."

        merged_env = os.environ.copy()
        merged_env.update(env)
        try:
            proc = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                env=merged_env,
                text=True,
                shell=False
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            return 124, e.stdout.decode() if e.stdout else "", e.stderr.decode() if e.stderr else ""
        except Exception as e:
            return 1, "", str(e)

    def execute_batch(self, plan_or_jobs: ResearchBatchPlan | List[ResearchJob], policy: Optional[ResearchLabPolicy] = None, confirm_heavy: bool = False) -> ResearchBatchRun:
        if not policy:
            from bist_signal_bot.research_lab.policy import ResearchLabPolicyManager
            policy = ResearchLabPolicyManager(self.settings).default_policy()
        self._confirm_heavy_override = confirm_heavy
        jobs = plan_or_jobs.jobs if isinstance(plan_or_jobs, ResearchBatchPlan) else plan_or_jobs
        plan_id = plan_or_jobs.plan_id if isinstance(plan_or_jobs, ResearchBatchPlan) else None
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        run = ResearchBatchRun(
            batch_id=batch_id,
            plan_id=plan_id,
            status=ResearchJobStatus.RUNNING,
            jobs=jobs
        )
        self.audit.log(AuditEventType.RESEARCH_LAB_BATCH_STARTED, {"batch_id": batch_id, "job_count": len(jobs), "no_real_order_sent": True})
        from bist_signal_bot.research_lab.retry import ResearchRetryPolicy
        retry_pol = ResearchRetryPolicy()
        for j in jobs:
            if j.status == ResearchJobStatus.PLANNED:
                self.queue.enqueue(j)
        start_time = time.time()
        while True:
            if time.time() - start_time > policy.max_runtime_seconds_per_batch:
                run.status = ResearchJobStatus.TIMEOUT
                run.errors.append("Batch overall timeout reached")
                break
            ready = self.queue.pop_next_ready_jobs(limit=policy.max_parallel_jobs)
            if not ready:
                active = [j for j in self.queue.list_jobs(limit=1000) if j.status in [ResearchJobStatus.QUEUED, ResearchJobStatus.RUNNING] and j.job_id in [rj.job_id for rj in jobs]]
                if not active:
                    run.status = ResearchJobStatus.SUCCESS
                    break
                else:
                    time.sleep(1)
                    continue
            for job in ready:
                self.audit.log(AuditEventType.RESEARCH_LAB_JOB_STARTED, {"job_id": job.job_id, "type": job.job_type.value})
                res = self.execute_job(job, policy)
                if res.status != ResearchJobStatus.SUCCESS and retry_pol.should_retry(job, res, policy):
                    self.audit.log(AuditEventType.RESEARCH_LAB_JOB_RETRIED, {"job_id": job.job_id, "reason": retry_pol.retry_reason(res)})
                    self.queue.update_job(retry_pol.next_retry_job(job, res))
                else:
                    self.queue.mark_result(job.job_id, res)
                    run.results.append(res)
                    if res.status == ResearchJobStatus.SUCCESS:
                        run.success_count += 1
                        self.audit.log(AuditEventType.RESEARCH_LAB_JOB_COMPLETED, {"job_id": job.job_id})
                    elif res.status in [ResearchJobStatus.SKIPPED, ResearchJobStatus.BLOCKED]:
                        run.skipped_count += 1
                        self.audit.log(AuditEventType.RESEARCH_LAB_JOB_CANCELLED, {"job_id": job.job_id, "status": res.status.value})
                    else:
                        run.failed_count += 1
                        self.audit.log(AuditEventType.RESEARCH_LAB_JOB_FAILED, {"job_id": job.job_id})
        run.finished_at = datetime.utcnow()
        run.elapsed_seconds = (run.finished_at - run.started_at).total_seconds()
        if run.failed_count > 0 and run.status == ResearchJobStatus.SUCCESS:
             run.status = ResearchJobStatus.PARTIAL_SUCCESS
        self.store.save_batch_run(run)
        status_evt = AuditEventType.RESEARCH_LAB_BATCH_FAILED if run.failed_count == len(jobs) and len(jobs) > 0 else AuditEventType.RESEARCH_LAB_BATCH_COMPLETED
        self.audit.log(status_evt, run.summary())
        return run
