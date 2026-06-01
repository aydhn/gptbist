import pytest
from bist_signal_bot.research_orchestrator.guardrails import ResearchOrchestratorGuardrails
from bist_signal_bot.research_orchestrator.models import ResearchRunPlan, ResearchCampaignType, ResearchTask, ResearchTaskType
from datetime import datetime, timezone

def test_guardrails_unsafe_language():
    guard = ResearchOrchestratorGuardrails()
    plan = ResearchRunPlan(
        plan_id="p1", campaign_type=ResearchCampaignType.CUSTOM, name="plan", created_at=datetime.now(timezone.utc),
        tasks=[ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="kesin al stratejisi")]
    )

    check = guard.check_safe_language(plan)
    assert check.blocked is True
    assert check.status == "BLOCKED"

def test_guardrails_broker_command():
    guard = ResearchOrchestratorGuardrails()
    plan = ResearchRunPlan(
        plan_id="p1", campaign_type=ResearchCampaignType.CUSTOM, name="plan", created_at=datetime.now(timezone.utc),
        tasks=[ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="t1", command="send live broker order")]
    )

    check = guard.check_no_broker_commands(plan)
    assert check.blocked is True

def test_guardrails_pass():
    guard = ResearchOrchestratorGuardrails()
    plan = ResearchRunPlan(
        plan_id="p1", campaign_type=ResearchCampaignType.CUSTOM, name="plan", created_at=datetime.now(timezone.utc),
        tasks=[ResearchTask(task_id="t1", task_type=ResearchTaskType.CUSTOM, name="safe research")]
    )

    checks = guard.run_preflight(plan)
    blocked = guard.blocking_checks(checks)
    assert len(blocked) == 0
