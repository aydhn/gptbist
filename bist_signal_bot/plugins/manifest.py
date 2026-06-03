import json
import hashlib
from pathlib import Path
from typing import Any
from bist_signal_bot.plugins.models import PluginManifest

class PluginManifestParser:
    def parse_manifest(self, path: Path) -> PluginManifest:
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse_manifest_dict(data, source_path=path)

    def parse_manifest_dict(self, data: dict[str, Any], source_path: Path | None = None) -> PluginManifest:
        manifest = PluginManifest(**data)
        if source_path:
            manifest.checksum = self.checksum_manifest(source_path)
            manifest.metadata["source_path"] = str(source_path)
        return manifest

    def checksum_manifest(self, path: Path) -> str | None:
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def validate_manifest_schema(self, manifest: PluginManifest) -> list[str]:
        findings = []
        if not manifest.plugin_id:
            findings.append("Missing plugin_id")
        if not manifest.name:
            findings.append("Missing name")
        if not manifest.version:
            findings.append("Missing version")

        # PathGuard checks
        if manifest.entrypoint and (".." in manifest.entrypoint or manifest.entrypoint.startswith("/")):
            findings.append("Unsafe entrypoint path")
        if manifest.module_path and (".." in manifest.module_path or manifest.module_path.startswith("/")):
            findings.append("Unsafe module_path")

        return findings

    def safe_manifest_summary(self, manifest: PluginManifest) -> dict[str, Any]:
        return {
            "plugin_id": manifest.plugin_id,
            "name": manifest.name,
            "version": manifest.version,
            "kind": manifest.kind.value,
            "hooks": [h.value for h in manifest.hooks],
            "requested_capabilities": [c.value for c in manifest.requested_capabilities],
            "enabled": manifest.enabled,
            "checksum": manifest.checksum
        }
