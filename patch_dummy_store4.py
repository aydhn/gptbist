import re

path = "bist_signal_bot/tests/test_model_registry_core.py"
with open(path, "r") as f:
    content = f.read()

# Let's just rewrite that function cleanly
good_test = """
def test_artifact_manager(tmp_path, monkeypatch):
    store = DummyStore()
    mgr = ModelArtifactManager(store=store)
    monkeypatch.setattr(mgr, "_is_safe", lambda x: True)

    model_path = tmp_path / "model.json"
    model_path.write_text('{"params": 1}')

    art = mgr.register_artifact(model_path, model_id="m1", confirm=True)
    assert art.artifact_format == ModelArtifactFormat.JSON
    assert art.checksum is not None
"""

import re
content = re.sub(r"def test_artifact_manager.*?assert art.checksum is not None", good_test, content, flags=re.DOTALL)

with open(path, "w") as f:
    f.write(content)
