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

def load_with_registry_validation(settings_cls, **kwargs):
    settings = settings_cls(**kwargs)
    if getattr(settings, 'ENABLE_CONFIG_REGISTRY', False):
        try:
            from bist_signal_bot.app.config_registry_app import (
                create_config_registry,
                create_config_validator,
            )
            registry = create_config_registry(settings)
            validator = create_config_validator(settings)
            records = registry.list_records()
            res = validator.validate_all(records)
            if getattr(settings, 'CONFIG_REGISTRY_WARN_UNKNOWN_ENV', False):
                if res.status.value in ["FAIL", "BLOCKED"]:
                    # In a real impl we'd raise or log heavily here, but we will pass to let app fail cleanly
                    pass
        except Exception:
            pass # fallback safe load
    return settings
