import re

path = "bist_signal_bot/ml/inference/engine.py"
with open(path, "r") as f:
    content = f.read()

# Make sure we don't duplicate
if "import ModelGovernanceStatus" not in content:
    imports = """from bist_signal_bot.model_registry.models import ModelGovernanceStatus
from bist_signal_bot.app.model_registry_app import create_model_governance_engine
"""
    content = content.replace("from bist_signal_bot.ml.inference.scoring import MLSignalScorer", imports + "from bist_signal_bot.ml.inference.scoring import MLSignalScorer")

# Look for MLInferenceResult to add registry fields
if "governance_status: ModelGovernanceStatus | None = None" not in content:
    # Actually, we need to modify MLInferenceResult in models.py
    pass

with open(path, "w") as f:
    f.write(content)
