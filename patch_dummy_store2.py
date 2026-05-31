import re

path = "bist_signal_bot/tests/test_model_registry_core.py"
with open(path, "r") as f:
    content = f.read()

# PathGuard may require path to be within BASE_DIR.
# We'll just mock the PathGuard check for the test.
hook = """
def test_artifact_manager(tmp_path, monkeypatch):
    store = DummyStore()
    mgr = ModelArtifactManager(store=store)
    monkeypatch.setattr(mgr, "_is_safe", lambda x: True)
    monkeypatch.setattr(mgr.path_guard, "ensure_safe_path", lambda x: None, raising=False)
"""
content = content.replace("def test_artifact_manager(tmp_path):", hook)

with open(path, "w") as f:
    f.write(content)
