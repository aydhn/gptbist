import pytest
from bist_signal_bot.research_lab.queue import ResearchJobQueue
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchJobPriority, ResearchJobTrigger, ResearchJobStatus
from bist_signal_bot.core.exceptions import ResearchQueueError

@pytest.fixture
def queue(tmp_path):
    return ResearchJobQueue(base_dir=tmp_path)

def test_enqueue_and_list(queue):
    job = ResearchJob(job_id="test1", job_type=ResearchJobType.BACKTEST, title="T", priority=ResearchJobPriority.NORMAL, trigger=ResearchJobTrigger.MANUAL)
    queue.enqueue(job)

    jobs = queue.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_id == "test1"
    assert jobs[0].status == ResearchJobStatus.QUEUED

def test_queue_cancel_requires_confirm(queue):
    job = ResearchJob(job_id="test2", job_type=ResearchJobType.BACKTEST, title="T", priority=ResearchJobPriority.NORMAL, trigger=ResearchJobTrigger.MANUAL)
    queue.enqueue(job)
    with pytest.raises(ResearchQueueError):
        queue.cancel_job("test2", confirm=False)

    queue.cancel_job("test2", confirm=True)
    assert queue.get_job("test2").status == ResearchJobStatus.CANCELLED
