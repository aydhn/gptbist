import pytest
from bist_signal_bot.research_lab.reporting import format_batch_plan_text, batch_plan_to_dict
from bist_signal_bot.research_lab.models import ResearchBatchPlan, ResearchJobTrigger

def test_reporting_formatting():
    plan = ResearchBatchPlan(plan_id="p1", trigger=ResearchJobTrigger.MANUAL)
    txt = format_batch_plan_text(plan)
    assert "Disclaimer" in txt
    assert "p1" in txt

    d = batch_plan_to_dict(plan)
    assert d["plan_id"] == "p1"
