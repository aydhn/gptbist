import pytest
import os
from pathlib import Path
from bist_signal_bot.research_orchestrator.storage import ResearchOrchestratorStore
from bist_signal_bot.research_orchestrator.models import ResearchCampaign, ResearchCampaignType
from datetime import datetime, timezone

def test_storage_campaigns(tmp_path):
    store = ResearchOrchestratorStore(base_dir=tmp_path)
    camp = ResearchCampaign(
        campaign_id="c1", campaign_type=ResearchCampaignType.CUSTOM, name="test", description="desc", created_at=datetime.now(timezone.utc)
    )
    store.save_campaigns([camp])
    loaded = store.load_campaigns()
    assert len(loaded) == 1
    assert loaded[0].campaign_id == "c1"

def test_storage_missing_campaigns(tmp_path):
    store = ResearchOrchestratorStore(base_dir=tmp_path)
    assert store.load_campaigns() == []
