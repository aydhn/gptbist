from pathlib import Path
from typing import Any
from bist_signal_bot.plugins.models import PluginManifest
from bist_signal_bot.plugins.manifest import PluginManifestParser

class PluginDiscoveryEngine:
    def __init__(self, parser: PluginManifestParser, root_dir: Path):
        self.parser = parser
        self.root_dir = root_dir

    def discover(self, plugin_dirs: list[Path] | None = None) -> list[PluginManifest]:
        dirs = plugin_dirs or self.default_plugin_dirs()
        manifests = []
        for d in dirs:
            if not d.exists() or not d.is_dir():
                continue
            manifests.extend(self.discover_in_dir(d))
        return manifests

    def default_plugin_dirs(self) -> list[Path]:
        return [
            self.root_dir / "plugins",
            self.root_dir / "examples" / "plugins"
        ]

    def discover_in_dir(self, path: Path) -> list[PluginManifest]:
        # Block out-of-bounds discovery
        try:
            path.resolve().relative_to(self.root_dir.resolve())
        except ValueError:
            return []

        manifests = []
        for file in self.find_manifest_files(path):
            try:
                manifest = self.parser.parse_manifest(file)
                manifests.append(manifest)
            except Exception:
                pass
        return manifests

    def find_manifest_files(self, path: Path) -> list[Path]:
        return list(path.rglob("plugin.json"))

    def filter_enabled(self, manifests: list[PluginManifest]) -> list[PluginManifest]:
        return [m for m in manifests if m.enabled]

    def discovery_summary(self, manifests: list[PluginManifest]) -> dict[str, Any]:
        return {
            "total_discovered": len(manifests),
            "enabled": len(self.filter_enabled(manifests)),
            "kinds": list(set(m.kind.value for m in manifests))
        }
