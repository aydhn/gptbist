import uuid

from bist_signal_bot.config_registry.models import (
    ConfigChangeDecision,
    ConfigGateRequest,
    ConfigGateResult,
    ConfigValidationStatus,
    RuntimeProfileType,
)
from bist_signal_bot.config_registry.validator import ConfigValidator
from bist_signal_bot.config_registry.registry import ConfigRegistry


class ConfigGate:
    def __init__(self, registry: ConfigRegistry, validator: ConfigValidator, store=None):
        self.registry = registry
        self.validator = validator
        self.store = store

    def run_gate(self, request: ConfigGateRequest) -> ConfigGateResult:
        records = self.registry.list_records()
        val_result = self.validator.validate_all(records)

        blocked = False
        decision = ConfigChangeDecision.ALLOW
        warnings = []

        if val_result.blocked_count > 0:
            blocked = True
            decision = ConfigChangeDecision.BLOCK_FORBIDDEN
            warnings.append("Blocked due to forbidden config findings.")

        elif val_result.warning_count > 0:
            if not request.allow_warnings:
                blocked = True
                decision = ConfigChangeDecision.BLOCK_GOVERNANCE
                warnings.append("Blocked due to warnings (allow_warnings=False).")
            else:
                decision = ConfigChangeDecision.WARN

        if request.require_research_only and request.profile_type != RuntimeProfileType.RESEARCH_ONLY:
            # Note: A real implementation would also check profile content (broker_enabled, etc)
            blocked = True
            decision = ConfigChangeDecision.BLOCK_GOVERNANCE
            warnings.append("Blocked: profile is not RESEARCH_ONLY but gate requires it.")

        result = ConfigGateResult(
            gate_id=str(uuid.uuid4()),
            request=request,
            status=ConfigValidationStatus.FAIL if blocked else val_result.status,
            decision=decision,
            validation_result=val_result,
            blocked=blocked,
            warnings=warnings
        )

        if self.store:
            self.store.save_gate(result)

        return result

    def runtime_gate(self, profile_type: RuntimeProfileType | None = None) -> ConfigGateResult:
        req = ConfigGateRequest(
            gate_name="runtime_gate",
            payload={"source": "runtime"},
            profile_type=profile_type,
            require_research_only=True,
            allow_warnings=True
        )
        return self.run_gate(req)

    def scheduler_gate(self) -> ConfigGateResult:
        req = ConfigGateRequest(
            gate_name="scheduler_gate",
            payload={"source": "scheduler"},
            require_research_only=True,
            allow_warnings=True
        )
        return self.run_gate(req)

    def research_lab_gate(self) -> ConfigGateResult:
        req = ConfigGateRequest(
            gate_name="research_lab_gate",
            payload={"source": "research_lab"},
            require_research_only=True,
            allow_warnings=True
        )
        return self.run_gate(req)

    def deployment_gate(self) -> ConfigGateResult:
        req = ConfigGateRequest(
            gate_name="deployment_gate",
            payload={"source": "deployment"},
            require_research_only=False,
            allow_warnings=True
        )
        return self.run_gate(req)

    def release_gate(self) -> ConfigGateResult:
        req = ConfigGateRequest(
            gate_name="release_gate",
            payload={"source": "release"},
            require_research_only=True,
            allow_warnings=False
        )
        return self.run_gate(req)
