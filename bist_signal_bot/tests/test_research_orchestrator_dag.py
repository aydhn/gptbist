import pytest
from bist_signal_bot.research_orchestrator.planner import ResearchRunPlanner
from bist_signal_bot.research_orchestrator.dag import ResearchDAGBuilder
from bist_signal_bot.research_orchestrator.models import ResearchCampaignType, ResearchTask, ResearchTaskType, ResearchDependency

def test_dag_topological_sort():
    planner = ResearchRunPlanner()
    dag = ResearchDAGBuilder()
    plan = planner.create_plan(campaign_type=ResearchCampaignType.QUICK_RESEARCH_SCAN)

    sorted_tasks = dag.topological_sort(plan.tasks, plan.dependencies)
    assert len(sorted_tasks) == 6
    assert sorted_tasks[0].task_type == "DATA_CATALOG_GATE"
    assert sorted_tasks[-1].task_type == "REPORT_BUILD"

def test_dag_cycle_detection():
    dag = ResearchDAGBuilder()
    tasks = [
        ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1"),
        ResearchTask(task_id="t2", task_type=ResearchTaskType.CUSTOM, name="t2")
    ]
    deps = [
        ResearchDependency(dependency_id="d1", from_task_id="t1", to_task_id="t2", status="SATISFIED"),
        ResearchDependency(dependency_id="d2", from_task_id="t2", to_task_id="t1", status="SATISFIED")
    ]
    cycles = dag.detect_cycles(tasks, deps)
    assert cycles
    assert "t1" in cycles or "t2" in cycles
