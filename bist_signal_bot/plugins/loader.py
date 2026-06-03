from datetime import datetime
from bist_signal_bot.plugins.models import PluginManifest, PluginLoadResult, PluginExecutionMode, PluginStatus, PluginValidationResult

class SafePluginLoader:
    def load_plugin(self, manifest: PluginManifest, mode: PluginExecutionMode = PluginExecutionMode.SAFE_METADATA_ONLY) -> PluginLoadResult:
        result = PluginLoadResult(
            load_id=f"load_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            execution_mode=mode,
            loaded=False,
            status=PluginStatus.UNKNOWN
        )

        if mode == PluginExecutionMode.DISABLED:
            result.status = PluginStatus.DISABLED
            result.warnings.append("Plugin loading is disabled.")
            return result

        if mode == PluginExecutionMode.SAFE_METADATA_ONLY:
            return self.metadata_only_load(manifest)

        if mode == PluginExecutionMode.DRY_RUN:
            return self.dry_run_load(manifest)

        # LOCAL_EXECUTE is highly restricted
        result.status = PluginStatus.BLOCKED
        result.errors.append("LOCAL_EXECUTE mode is blocked by default safety policy.")
        return result

    def load_plugins(self, manifests: list[PluginManifest], mode: PluginExecutionMode = PluginExecutionMode.SAFE_METADATA_ONLY) -> list[PluginLoadResult]:
        return [self.load_plugin(m, mode) for m in manifests]

    def metadata_only_load(self, manifest: PluginManifest) -> PluginLoadResult:
        # Mock load that only reads metadata
        return PluginLoadResult(
            load_id=f"load_meta_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            execution_mode=PluginExecutionMode.SAFE_METADATA_ONLY,
            loaded=True,
            status=PluginStatus.LOADED,
            warnings=["Loaded in safe metadata-only mode. No code executed."]
        )

    def dry_run_load(self, manifest: PluginManifest) -> PluginLoadResult:
        # Dry run doesn't actually execute side-effects
        return PluginLoadResult(
            load_id=f"load_dry_{manifest.plugin_id}_{datetime.now().timestamp()}",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            execution_mode=PluginExecutionMode.DRY_RUN,
            loaded=True,
            status=PluginStatus.LOADED,
            warnings=["Loaded in dry-run mode. Side effects blocked."]
        )

    def validate_before_load(self, manifest: PluginManifest) -> PluginValidationResult:
        # Placeholder for integration with PluginValidator
        return PluginValidationResult(
            validation_id="temp",
            plugin_id=manifest.plugin_id,
            created_at=datetime.now(),
            status=PluginStatus.VALIDATED,
            manifest_valid=True,
            contract_valid=True,
            capabilities_valid=True,
            hooks_valid=True,
            sandbox_valid=True
        )

    def should_block_load(self, manifest: PluginManifest, validation: PluginValidationResult) -> list[str]:
        reasons = []
        if validation.status in [PluginStatus.FAIL, PluginStatus.BLOCKED]:
            reasons.append(f"Validation failed with status {validation.status.value}")
        return reasons
