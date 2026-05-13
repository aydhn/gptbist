import logging
import uuid
import time
from datetime import datetime
from typing import Callable, Any, Tuple, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import (
    RuntimeJobType, RuntimeJobConfig, RuntimeJobResult,
    RuntimeJobStatus, SessionPolicy
)

class RuntimeJobRunner:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def run_job(self, job_type: RuntimeJobType, func: Callable[[], Any], config: Optional[RuntimeJobConfig] = None) -> RuntimeJobResult:
        config = config or self.build_default_job_config(job_type)
        job_id = str(uuid.uuid4())

        result = RuntimeJobResult(
            job_id=job_id,
            job_type=job_type,
            status=RuntimeJobStatus.RUNNING,
            started_at=datetime.utcnow(),
            metadata=config.metadata
        )

        if not config.enabled:
            result.status = RuntimeJobStatus.SKIPPED
            result.finished_at = datetime.utcnow()
            result.issues.append("Job is disabled via config.")
            return result

        attempts = 0
        max_attempts = config.max_retries + 1
        last_exception = None

        while attempts < max_attempts:
            attempts += 1
            result.attempts = attempts
            try:
                out = func()
                result.status = RuntimeJobStatus.SUCCESS
                if isinstance(out, dict):
                    result.summary = out
                else:
                    result.summary = {"output": str(out)}
                break
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Job {job_type.value} attempt {attempts} failed: {e}")
                if attempts < max_attempts:
                    time.sleep(config.retry_delay_seconds)

        if result.status == RuntimeJobStatus.RUNNING: # Failed all attempts
            result.status = RuntimeJobStatus.FAILED
            result.issues.append(f"Job failed after {attempts} attempts. Last error: {str(last_exception)}")

        result.finished_at = datetime.utcnow()
        result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

        return result

    def should_run_in_session(self, session_policy: SessionPolicy, now: Optional[datetime] = None) -> Tuple[bool, str]:
        # Fallback behaviour if phase 6 calendar module is absent
        if session_policy == SessionPolicy.RUN_ALWAYS:
            return True, "RUN_ALWAYS policy active."
        return True, "Session check fallback: proceeding."

    def build_default_job_config(self, job_type: RuntimeJobType) -> RuntimeJobConfig:
        return RuntimeJobConfig(
            job_type=job_type,
            enabled=True,
            max_retries=self.settings.RUNTIME_JOB_MAX_RETRIES,
            retry_delay_seconds=self.settings.RUNTIME_JOB_RETRY_DELAY_SECONDS,
            timeout_seconds=self.settings.RUNTIME_JOB_TIMEOUT_SECONDS,
            session_policy=SessionPolicy.RUN_ALWAYS
        )
