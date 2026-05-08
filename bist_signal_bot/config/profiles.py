from enum import Enum
from typing import Any

from pydantic import BaseModel


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"

class RunMode(str, Enum):
    RESEARCH = "research"
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE_SIGNAL = "live_signal"

class ConfigProfile(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    env: AppEnvironment
    description: str
    safe_defaults: dict[str, Any]

def get_profile(env: str) -> ConfigProfile:
    """Returns the configuration profile based on the environment name."""
    try:
        env_enum = AppEnvironment(env.lower())
    except ValueError:
        from bist_signal_bot.core.exceptions import ConfigurationError
        raise ConfigurationError(f"Invalid APP_ENV: '{env}'. Must be one of {', '.join([e.value for e in AppEnvironment])}")

    if env_enum == AppEnvironment.DEVELOPMENT:
        return ConfigProfile(
            env=env_enum,
            description="Development environment. Dry runs and extra logging enabled.",
            safe_defaults={
                "DRY_RUN": True,
                "TELEGRAM_DRY_RUN": True,
                "LOG_LEVEL": "INFO",
                "DEBUG_TRACEBACKS": False,
            }
        )
    elif env_enum == AppEnvironment.TEST:
        return ConfigProfile(
            env=env_enum,
            description="Test environment. Integrations disabled. Isolated execution.",
            safe_defaults={
                "DRY_RUN": True,
                "ENABLE_TELEGRAM": False,
                "TELEGRAM_DRY_RUN": True,
                "LOG_TO_FILE": False,
                "ENABLE_AUDIT_LOG": False,
                "LOG_LEVEL": "DEBUG",
                # Don't try to load external real paths here, that's done via overrides
            }
        )
    elif env_enum == AppEnvironment.PRODUCTION:
        return ConfigProfile(
            env=env_enum,
            description="Production environment. Strict safety checks, real signaling.",
            safe_defaults={
                "DRY_RUN": True, # Real trading is not allowed in this phase anyway
                "DEBUG_TRACEBACKS": False,
                "MASK_SECRETS_IN_LOGS": True,
                "LOG_TO_FILE": True,
                "ENABLE_AUDIT_LOG": True,
            }
        )

    # Should be unreachable
    from bist_signal_bot.core.exceptions import ConfigurationError
    raise ConfigurationError(f"Unknown environment: {env}")
