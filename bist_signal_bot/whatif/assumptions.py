from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import WhatIfAssumptionOverride


class AssumptionOverrideEngine:
    def __init__(self, logger: Any):
        self.logger = logger

    def apply_overrides(self, settings: Settings, overrides: list[WhatIfAssumptionOverride]) -> dict[str, Any]:
        """
        Creates a dictionary of overrides to be applied contextually, WITHOUT mutating the global Settings instance.
        """
        context = self.build_context(overrides)
        return context

    def validate_override(self, override: WhatIfAssumptionOverride) -> list[str]:
        return override.warnings

    def build_context(self, overrides: list[WhatIfAssumptionOverride]) -> dict[str, Any]:
        context = {}
        for override in overrides:
            context[override.assumption_type.value] = override.new_value
        return context

    def redacted_context(self, context: dict[str, Any]) -> dict[str, Any]:
        safe_ctx = {}
        unsafe_keys = {"secret", "api_key", "token", "password", "broker", "live", "real_order"}
        for k, v in context.items():
            if any(u in k.lower() for u in unsafe_keys):
                safe_ctx[k] = "***REDACTED***"
            else:
                safe_ctx[k] = v
        return safe_ctx
