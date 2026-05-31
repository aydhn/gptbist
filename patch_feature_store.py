import re

path = "bist_signal_bot/feature_store/leakage.py"
with open(path, "r") as f:
    content = f.read()

# Make sure FeatureQualityStatus is mapped to ModelGovernanceStatus if needed.
# It already happens in drift.py. So leakage.py is probably fine as is, but we can
# add a small helper just in case.

if "to_model_governance_status" not in content:
    hook = """
    def to_model_governance_status(self, fq_status: FeatureQualityStatus) -> str:
        from bist_signal_bot.model_registry.models import ModelGovernanceStatus
        if fq_status == FeatureQualityStatus.BLOCKED:
            return ModelGovernanceStatus.BLOCKED
        if fq_status == FeatureQualityStatus.FAIL:
            return ModelGovernanceStatus.FAIL
        if fq_status == FeatureQualityStatus.WATCH:
            return ModelGovernanceStatus.WATCH
        return ModelGovernanceStatus.PASS
"""
    content += hook

with open(path, "w") as f:
    f.write(content)
