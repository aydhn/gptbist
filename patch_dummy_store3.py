import re

path = "bist_signal_bot/tests/test_model_registry_core.py"
with open(path, "r") as f:
    content = f.read()

# I accidentally recreated mgr in the test function which overrode the monkeypatch
bad_mgr = """
    store = DummyStore()
    mgr = ModelArtifactManager(store=store)"""

if content.count(bad_mgr) > 1:
    content = content.replace(bad_mgr, "", 1) # remove the second one

with open(path, "w") as f:
    f.write(content)
