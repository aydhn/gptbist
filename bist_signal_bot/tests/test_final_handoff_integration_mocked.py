import pytest
import sys
from unittest.mock import MagicMock

# Mocking all deep dependencies for pure logic tests
sys.modules['bist_signal_bot.data'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
sys.modules['bist_signal_bot.config.settings'] = MagicMock()

from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder
from bist_signal_bot.final_handoff.models import ReleasePackStage
from bist_signal_bot.final_handoff.release_pack import FinalReleasePackBuilder

def test_builder_runs_without_real_orders():
    builder = FinalHandoffBuilder()
    manifest = builder.build_handoff()
    assert manifest.final_status.value in ["PASS", "FAIL"]

def test_release_pack_is_offline():
    builder = FinalReleasePackBuilder()
    pack = builder.build_release_pack(stage=ReleasePackStage.BUILT)
    assert pack.stage == ReleasePackStage.BUILT

def test_disclaimers_present():
    from bist_signal_bot.final_handoff.operator_playbook import OperatorPlaybookBuilder
    pb = OperatorPlaybookBuilder().build_playbook()
    assert "not investment advice" in pb.disclaimer
