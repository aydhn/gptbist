from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobResult, ResearchLabPolicy

class ResearchRetryPolicy:
    def should_retry(self, job: ResearchJob, result: ResearchJobResult, policy: ResearchLabPolicy) -> bool:
        if job.retry_count >= (job.max_retries or policy.default_max_retries):
            return False
        if result.exit_code in [2, 126, 127]:
            return False
        err_text = " ".join(result.errors).lower()
        if any(w in err_text for w in ["validation", "forbidden", "security", "unauthorized", "confirm required"]):
            return False
        if result.exit_code == 124 or "timeout" in err_text or "lock" in err_text or "network" in err_text:
             return True
        return False

    def next_retry_job(self, job: ResearchJob, result: ResearchJobResult) -> ResearchJob:
        job.retry_count += 1
        job.status = "QUEUED"
        job.started_at = None
        job.finished_at = None
        return job

    def retry_reason(self, result: ResearchJobResult) -> str:
        if result.exit_code == 124:
            return "Execution timeout"
        err_text = " ".join(result.errors).lower()
        if "lock" in err_text:
            return "File lock contention"
        if "network" in err_text:
            return "Transient network error"
        return "Unknown transient error"
