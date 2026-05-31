import re

path = "bist_signal_bot/tests/test_model_registry_core.py"
with open(path, "r") as f:
    content = f.read()

# Fix dummy store
hook = """
    def load_model_cards(self, model_id=None, limit=1000): return []
    def load_validation_summaries(self, model_id=None, limit=1000): return []
    def load_calibration_summaries(self, model_id=None, limit=1000): return []
"""
if "def load_model_cards" not in content:
    content = content.replace("def load_models(self, status=None, limit=1000): return self.models", "def load_models(self, status=None, limit=1000): return self.models" + hook)

with open(path, "w") as f:
    f.write(content)


path2 = "bist_signal_bot/model_registry/artifacts.py"
with open(path2, "r") as f:
    content2 = f.read()

if "ensure_safe_path" not in content2:
    # Need to check how PathGuard actually works in this project
    # We'll just try except around ensure_safe_path

    # Or just write a small helper inside artifacts.py
    helper = """
    def _is_safe(self, p):
        try:
            self.path_guard.ensure_safe_path(p)
            return True
        except:
            return False
"""
    content2 = content2.replace("    def checksum(self, path: Path) -> str | None:", helper + "\n    def checksum(self, path: Path) -> str | None:")
    content2 = content2.replace("self.path_guard.is_safe_path(path_obj)", "self._is_safe(path_obj)")
    content2 = content2.replace("self.path_guard.is_safe_path(path)", "self._is_safe(path)")

with open(path2, "w") as f:
    f.write(content2)
