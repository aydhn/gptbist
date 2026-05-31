import re

path = "bist_signal_bot/ml/inference/models.py"
with open(path, "r") as f:
    content = f.read()

# Add ModelGovernanceStatus import
if "from bist_signal_bot.model_registry.models import ModelGovernanceStatus" not in content:
    content = "from bist_signal_bot.model_registry.models import ModelGovernanceStatus\n" + content

# Add fields to MLInferenceResult
if "governance_status" not in content:
    pattern = r"(elapsed_seconds: float = 0\.0)"
    replacement = r"\1\n    governance_status: ModelGovernanceStatus | None = None\n    model_version: str | None = None\n    feature_set_version: str | None = None\n    model_card_id: str | None = None\n    validation_status: ModelGovernanceStatus | None = None\n    calibration_status: ModelGovernanceStatus | None = None"
    content = re.sub(pattern, replacement, content)

with open(path, "w") as f:
    f.write(content)
