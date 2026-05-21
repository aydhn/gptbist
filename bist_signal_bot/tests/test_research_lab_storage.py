import pytest
from bist_signal_bot.research_lab.storage import ResearchLabStore
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchBatchPlan, ResearchJobTrigger

@pytest.fixture
def store(tmp_path):
    return ResearchLabStore(base_dir=tmp_path)

def test_store_job_append_load(store):
    j1 = ResearchJob(job_id="1", job_type=ResearchJobType.CUSTOM, title="A")
    store.append_job(j1)
    jobs = store.load_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_id == "1"

def test_store_plan_save_load(store):
    plan = ResearchBatchPlan(plan_id="p1", trigger=ResearchJobTrigger.MANUAL)
    store.save_plan(plan)
    loaded = store.load_plan("p1")
    assert loaded is not None
    assert loaded.plan_id == "p1"
