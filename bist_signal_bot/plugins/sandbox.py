from typing import Any
from bist_signal_bot.plugins.models import PluginManifest

class PluginSandboxPolicy:
    def default_policy(self) -> dict[str, Any]:
        return {
            "static_scan_enabled": True,
            "blocked_imports": self.blocked_import_patterns(),
            "blocked_commands": self.blocked_command_patterns()
        }

    def validate_manifest_sandbox(self, manifest: PluginManifest) -> list[str]:
        findings = []
        if manifest.metadata.get("unsafe_language", False):
             findings.append("Unsafe language detected in metadata.")
        return findings

    def allowed_paths(self, manifest: PluginManifest) -> list[str]:
        return []

    def blocked_import_patterns(self) -> list[str]:
        return [
            "requests",
            "httpx",
            "urllib",
            "websocket",
            "openai",
            "broker",
            "ccxt",
            "binance",
            "okx"
        ]

    def blocked_command_patterns(self) -> list[str]:
        return [
            "market order",
            "buy order",
            "sell order",
            "live trading",
            "subprocess",
            "os.system",
            "eval",
            "exec"
        ]

    def sandbox_summary(self, manifest: PluginManifest) -> dict[str, Any]:
        return {
            "plugin_id": manifest.plugin_id,
            "policy": "DEFAULT",
            "blocked_imports_count": len(self.blocked_import_patterns()),
            "blocked_commands_count": len(self.blocked_command_patterns())
        }
