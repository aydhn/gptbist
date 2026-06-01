import pytest
from bist_signal_bot.research_orchestrator.planner import ResearchRunPlanner
from bist_signal_bot.research_orchestrator.models import ResearchCampaignType

def test_planner_default_tasks():
    planner = ResearchRunPlanner()
    plan = planner.create_plan(campaign_type=ResearchCampaignType.QUICK_RESEARCH_SCAN)
    assert len(plan.tasks) == 6
    assert plan.tasks[0].task_type == "DATA_CATALOG_GATE"
    assert "disclaimer" in plan.model_dump()
    assert len(plan.warnings) == 1
    assert "Missing symbols" in plan.warnings[0]

def test_planner_full_pipeline():
    planner = ResearchRunPlanner()
    plan = planner.create_plan(campaign_type=ResearchCampaignType.FULL_RESEARCH_PIPELINE, symbols=["ASELS"])
    assert len(plan.tasks) == 12
    assert len(plan.dependencies) == 11
    assert not plan.warnings
