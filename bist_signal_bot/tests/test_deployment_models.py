import pytest
from bist_signal_bot.deployment.models import DeploymentProfile, DeploymentProfileType

def test_deployment_profile_validation():
    # Valid profile
    profile = DeploymentProfile(
        profile_id="test",
        profile_type=DeploymentProfileType.RESEARCH_ONLY,
        name="Test Profile",
        safe_defaults=True,
        broker_enabled=False,
        real_order_enabled=False
    )
    assert profile.name == "Test Profile"

def test_deployment_profile_invalid_broker():
    with pytest.raises(ValueError, match="broker_enabled cannot be true"):
        DeploymentProfile(
            profile_id="test",
            profile_type=DeploymentProfileType.RESEARCH_ONLY,
            name="Test Profile",
            broker_enabled=True,
            real_order_enabled=False
        )

def test_deployment_profile_invalid_real_order():
    with pytest.raises(ValueError, match="real_order_enabled cannot be true"):
        DeploymentProfile(
            profile_id="test",
            profile_type=DeploymentProfileType.RESEARCH_ONLY,
            name="Test Profile",
            broker_enabled=False,
            real_order_enabled=True
        )
