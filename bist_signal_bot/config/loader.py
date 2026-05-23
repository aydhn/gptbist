from bist_signal_bot.config.settings import Settings

def load_with_deployment_profile(settings: Settings, profile_type_str: str) -> Settings:
    from bist_signal_bot.deployment.profiles import DeploymentProfileManager
    from bist_signal_bot.deployment.models import DeploymentProfileType
    try:
        ptype = DeploymentProfileType[profile_type_str]
        manager = DeploymentProfileManager()
        profile = manager.get_profile(ptype)
        manager.apply_profile_to_settings(profile, settings)
    except KeyError:
        pass # Ignore invalid profile type string fallback
    return settings
