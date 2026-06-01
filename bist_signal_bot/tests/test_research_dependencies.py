import pytest
from bist_signal_bot.research_orchestrator.dependencies import ResearchDependencyResolver
from bist_signal_bot.research_orchestrator.models import ResearchTaskResult, ResearchRunStatus, ResearchDependencyStatus, ResearchTask, ResearchTaskType

def test_dependency_resolver():
    resolver = ResearchDependencyResolver()

    t1_res = ResearchTaskResult(
        result_id="1", task_id="t1", task_type=ResearchTaskType.CUSTOM,
        started_at="2023-01-01T00:00:00Z", status=ResearchRunStatus.FAIL
    )

    status = resolver.dependency_status_from_result(t1_res, required=True)
    assert status == ResearchDependencyStatus.FAILED

    status_missing = resolver.dependency_status_from_result(None, required=True)
    assert status_missing == ResearchDependencyStatus.MISSING
