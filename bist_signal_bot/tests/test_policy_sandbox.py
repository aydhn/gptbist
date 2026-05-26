
from bist_signal_bot.whatif.policy_sandbox import PolicySandbox
from bist_signal_bot.config.settings import Settings

def test_policy_sandbox():
    settings = Settings()
    sandbox = PolicySandbox(settings, None, None)
    sc = sandbox.policy_to_scenario({"CONFIDENCE_THRESHOLD": 80})
    assert len(sc.assumptions) == 1
    assert sc.assumptions[0].new_value == 80
