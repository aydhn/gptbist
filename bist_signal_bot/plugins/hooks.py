from typing import Any
from bist_signal_bot.plugins.models import PluginHookRegistration, PluginManifest, PluginHookKind, PluginStatus

class PluginHookRegistry:
    def __init__(self):
        self._hooks: dict[PluginHookKind, list[PluginHookRegistration]] = {}

    def register_hook(self, registration: PluginHookRegistration) -> PluginHookRegistration:
        errors = self.validate_registration(registration)
        if errors:
            registration.status = PluginStatus.FAIL
            registration.warnings.extend(errors)
            return registration

        if registration.hook_kind not in self._hooks:
            self._hooks[registration.hook_kind] = []

        self._hooks[registration.hook_kind].append(registration)
        self._hooks[registration.hook_kind].sort(key=lambda x: x.priority)

        registration.status = PluginStatus.ACTIVE
        return registration

    def register_hooks_from_manifest(self, manifest: PluginManifest) -> list[PluginHookRegistration]:
        registrations = []
        for hook_kind in manifest.hooks:
            reg = PluginHookRegistration(
                registration_id=f"hook_{manifest.plugin_id}_{hook_kind.value}",
                plugin_id=manifest.plugin_id,
                hook_kind=hook_kind,
                enabled=manifest.enabled,
                status=PluginStatus.DISCOVERED
            )
            registrations.append(self.register_hook(reg))
        return registrations

    def hooks_for_kind(self, hook_kind: PluginHookKind) -> list[PluginHookRegistration]:
        return [h for h in self._hooks.get(hook_kind, []) if h.enabled]

    def dispatch_hook(self, hook_kind: PluginHookKind, payload: dict[str, Any] | None = None, dry_run: bool = True) -> list[dict[str, Any]]:
        results = []
        hooks = self.hooks_for_kind(hook_kind)

        for hook in hooks:
            # Deterministic, dry-run only output by default
            res = {
                "plugin_id": hook.plugin_id,
                "hook_kind": hook.hook_kind.value,
                "status": "DISPATCHED",
                "dry_run": dry_run,
                "mock_response": True
            }
            if not hook.handler_ref:
                res["warnings"] = ["Missing handler_ref, WATCH status."]
            results.append(res)

        return results

    def validate_registration(self, registration: PluginHookRegistration) -> list[str]:
        findings = []
        if not registration.plugin_id:
            findings.append("Missing plugin_id")
        return findings

    def hook_summary(self) -> dict[str, Any]:
        return {
            "total_registered": sum(len(h) for h in self._hooks.values()),
            "by_kind": {k.value: len(v) for k, v in self._hooks.items()}
        }
