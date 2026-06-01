import pytest
from bist_signal_bot.research_orchestrator.planner import ResearchRunPlanner
from bist_signal_bot.research_orchestrator.models import ResearchCampaignType

def test_leaderboard_tasks_in_plan():
    planner = ResearchRunPlanner()
    plan = planner.create_plan(campaign_type=ResearchCampaignType.FULL_RESEARCH_PIPELINE)
    types = [t.task_type for t in plan.tasks]
    assert "LEADERBOARD_BUILD" in types
    assert "MONITORING_RUN" in types
