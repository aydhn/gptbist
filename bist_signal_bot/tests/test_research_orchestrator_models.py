import pytest
from bist_signal_bot.research_orchestrator.models import ResearchTask, ResearchTaskType

def test_research_task_validation():
    # Empty name
    with pytest.raises(ValueError):
        ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="")

    # Negative timeout
    with pytest.raises(ValueError):
        ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", timeout_seconds=-5)

    # Negative retry
    with pytest.raises(ValueError):
        ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", retry_count=-1)

    # Self dependency
    with pytest.raises(ValueError):
        ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", depends_on=["t1"])
