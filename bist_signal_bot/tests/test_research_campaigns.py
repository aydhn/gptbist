import pytest
from bist_signal_bot.research_orchestrator.campaigns import ResearchCampaignRegistry

def test_campaign_registry():
    reg = ResearchCampaignRegistry()
    campaigns = reg.default_campaigns()
    assert len(campaigns) >= 3

    camp = reg.get_campaign("QUICK_RESEARCH_SCAN")
    assert camp is not None
    assert camp.default_profile == "STANDARD"

    camps_adv = reg.campaigns_for_profile("ADVANCED")
    assert len(camps_adv) == 1
