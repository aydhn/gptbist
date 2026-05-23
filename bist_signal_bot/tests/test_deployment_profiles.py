from bist_signal_bot.deployment.profiles import DeploymentProfileManager
from bist_signal_bot.deployment.models import DeploymentProfileType

def test_deployment_profile_manager_defaults():
    manager = DeploymentProfileManager()
    profiles = manager.default_profiles()
    assert len(profiles) >= 6

def test_research_only_profile_is_safe():
    manager = DeploymentProfileManager()
    profile = manager.get_profile(DeploymentProfileType.RESEARCH_ONLY)

    assert profile.broker_enabled is False
    assert profile.real_order_enabled is False
    assert profile.telegram_send_enabled is False
    assert profile.settings_overrides.get("FORCE_RESEARCH_ONLY") is True

def test_full_local_safe_profile_is_safe():
    manager = DeploymentProfileManager()
    profile = manager.get_profile(DeploymentProfileType.FULL_LOCAL_SAFE)

    assert profile.broker_enabled is False
    assert profile.real_order_enabled is False
    assert profile.telegram_send_enabled is False
    assert profile.settings_overrides.get("ENABLE_LOCAL_SCHEDULER") is True
    assert profile.settings_overrides.get("GOVERNANCE_REQUIRE_RELEASE_GATE") is True
