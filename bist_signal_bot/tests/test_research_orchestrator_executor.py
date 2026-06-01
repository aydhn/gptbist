import pytest
from bist_signal_bot.research_orchestrator.executor import ResearchRunExecutor
from bist_signal_bot.research_orchestrator.models import ResearchTask, ResearchTaskType, ResearchRunPlan, ResearchCampaignType, ResearchRunStatus
from datetime import datetime, timezone

def test_executor_dry_run():
    executor = ResearchRunExecutor()
    plan = ResearchRunPlan(
        plan_id="p1",
        campaign_type=ResearchCampaignType.CUSTOM,
        name="test",
        created_at=datetime.now(timezone.utc),
        tasks=[ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1")]
    )
    run = executor.execute_plan(plan, dry_run=True)
    assert run.status == ResearchRunStatus.DRY_RUN
    assert run.task_results[0].status == ResearchRunStatus.DRY_RUN

def test_executor_unsafe_command_blocked():
    executor = ResearchRunExecutor()
    plan = ResearchRunPlan(
        plan_id="p1",
        campaign_type=ResearchCampaignType.CUSTOM,
        name="test",
        created_at=datetime.now(timezone.utc),
        tasks=[ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", command="buy order AAPL")]
    )
    run = executor.execute_plan(plan, dry_run=False)
    assert run.status == ResearchRunStatus.BLOCKED
    assert run.task_results[0].status == ResearchRunStatus.BLOCKED

def test_executor_skip_on_fail():
    executor = ResearchRunExecutor()
    t1 = ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", command="broker fail")
    t2 = ResearchTask(task_id="t2", task_type=ResearchTaskType.CUSTOM, name="t2", depends_on=["t1"])
    plan = ResearchRunPlan(
        plan_id="p1",
        campaign_type=ResearchCampaignType.CUSTOM,
        name="test",
        created_at=datetime.now(timezone.utc),
        tasks=[t1, t2]
    )
    # executor stop_on_fail stops execution
    run = executor.execute_plan(plan, dry_run=False, stop_on_fail=False)
    assert len(run.task_results) == 2
    assert run.task_results[0].status == ResearchRunStatus.BLOCKED
    assert run.task_results[1].status == ResearchRunStatus.SKIPPED
