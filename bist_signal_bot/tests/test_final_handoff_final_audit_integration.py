import pytest
from bist_signal_bot.final_handoff.builder import FinalHandoffBuilder

def test_final_audit_integration_reads_go_no_go():
    builder = FinalHandoffBuilder()
    status = builder.collect_latest_release_status()
    # verify mocked data reflects what final audit should pass
    assert "go_no_go_decision" in status
    assert status["go_no_go_decision"] == "GO_WITH_WARNINGS"
