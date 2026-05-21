from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import GovernanceGateRequest, GovernanceStatus, GovernanceDecision
from bist_signal_bot.governance.gate import GovernanceGate

def test_governance_gate_allow():
    gate = GovernanceGate(Settings())
    # A safe payload
    res = gate.runtime_gate({"command": "scan"})

    # Should pass because payload has no forbidden text or policy violation
    # Note: If no domains match, or no rules trigger, it passes.
    assert res.status in (GovernanceStatus.PASS, GovernanceStatus.WARN)
    assert res.decision in (GovernanceDecision.ALLOW, GovernanceDecision.WARN)

def test_governance_gate_block():
    gate = GovernanceGate(Settings())
    # payload missing confirm might trigger a warning/block depending on policy,
    # but let's trigger a forbidden pattern in a way that the evaluator might catch if we had a rule for it.
    # Actually, the evaluator checks if 'confirm' is present for CONFIRM_REQUIRED
    # Maintenance gate has BACKUP_RESTORE domain, but we put CONFIRM_REQUIRED under RESEARCH_ONLY for policy updates.
    # Let's directly construct a gate request that triggers CONFIRM_REQUIRED

    from bist_signal_bot.governance.models import GovernanceDomain
    req = GovernanceGateRequest(
        gate_name="test_gate",
        domains=[GovernanceDomain.RESEARCH_ONLY],
        payload={"something_else": True} # missing "confirm"
    )
    res = gate.run_gate(req)
    assert res.status == GovernanceStatus.BLOCKED
    assert res.blocked is True
