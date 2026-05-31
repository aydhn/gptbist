import os
path = "bist_signal_bot/ops/store_checks.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    # The previous patch failed because it searched for 'class OpsStoreChecker:'
    # Let's fix it by searching for 'class StoreIntegrityChecker:'
    if "check_model_registry_dirs" not in content:
        hook = """
    def check_model_registry_dirs(self) -> dict[str, Any]:
        if not getattr(self.settings, "ENABLE_MODEL_REGISTRY", False):
            return {"status": "SKIPPED"}

        try:
            from bist_signal_bot.storage.paths import get_model_registry_dir
            base = get_model_registry_dir(self.settings)
            dirs = ["models", "experiments", "artifacts", "cards", "validation", "calibration", "promotion", "drift", "lineage", "governance", "reports"]
            missing = [d for d in dirs if not (base / d).exists()]
            return {
                "status": "PASS" if not missing else "WARN",
                "missing_dirs": missing
            }
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
"""
        content = content.replace("class StoreIntegrityChecker:", "class StoreIntegrityChecker:" + hook)

    with open(path, "w") as f:
        f.write(content)

path2 = "bist_signal_bot/tests/test_model_registry_integrations.py"
with open(path2, "r") as f:
    content2 = f.read()
content2 = content2.replace("from bist_signal_bot.ops.store_checks import OpsStoreChecker", "from bist_signal_bot.ops.store_checks import StoreIntegrityChecker")
content2 = content2.replace("checker = OpsStoreChecker(settings)", "checker = StoreIntegrityChecker(settings)")

with open(path2, "w") as f:
    f.write(content2)
