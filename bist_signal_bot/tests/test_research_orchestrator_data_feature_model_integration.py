import pytest
from bist_signal_bot.research_orchestrator.dependencies import ResearchDependencyResolver
from bist_signal_bot.research_orchestrator.models import ResearchTask, ResearchTaskType

def test_data_catalog_gate_mock():
    res = ResearchDependencyResolver()
    task = ResearchTask(task_id="t1", task_type=ResearchTaskType.DATA_CATALOG_GATE, name="Data Catalog Gate")
    checks = res.check_external_requirements(task)
    assert len(checks) == 1
    assert checks[0].status == "PASS"
