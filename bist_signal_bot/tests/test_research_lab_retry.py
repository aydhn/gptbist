import pytest
from bist_signal_bot.research_lab.retry import ResearchRetryPolicy
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobResult, ResearchLabPolicy, ResearchJobStatus
from datetime import datetime

def test_retry_policy():
    rp = ResearchRetryPolicy()
    pol = ResearchLabPolicy()
    job = ResearchJob(job_id="1", job_type="CUSTOM", title="A", max_retries=1, retry_count=0)
    res = ResearchJobResult(result_id="1", job_id="1", status=ResearchJobStatus.FAILED, started_at=datetime.utcnow(), exit_code=124)

    assert rp.should_retry(job, res, pol) is True

    job.retry_count = 1
    assert rp.should_retry(job, res, pol) is False
