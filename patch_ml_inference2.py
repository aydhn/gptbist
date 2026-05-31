import re

path = "bist_signal_bot/ml/inference/engine.py"
with open(path, "r") as f:
    content = f.read()

# We need to add governance checking to the predict method
# Find: def predict(self, input_data: MLInferenceInput) -> MLInferenceResult:
# Add logic right after model_id extraction

predict_hook = """
            # Governance Check
            if getattr(self.settings, "RUNTIME_MODEL_REGISTRY_ENABLED", False):
                try:
                    gov_engine = create_model_governance_engine(self.settings)
                    assessment = gov_engine.assess_model(model_id)
                    if assessment.status == ModelGovernanceStatus.BLOCKED or \\
                       (assessment.status == ModelGovernanceStatus.FAIL and getattr(self.settings, "RUNTIME_INFERENCE_BLOCK_GOVERNANCE_FAIL", False)):
                        reasons.append(f"Model {model_id} governance blocked/failed")
                        from bist_signal_bot.ml.inference.models import MLFeatureAlignmentResult, MLFeatureAlignmentStatus
                        dummy_align = MLFeatureAlignmentResult(status=MLFeatureAlignmentStatus.FAILED)
                        res = self._create_error_result(input_data, dummy_align, reasons, warnings, start_time, generated_at)
                        res.governance_status = assessment.status
                        return res

                    # Warning logic
                    if assessment.status == ModelGovernanceStatus.WATCH and getattr(self.settings, "RUNTIME_INFERENCE_WARN_ON_MODEL_DRIFT", True):
                        warnings.append(f"Model {model_id} is on WATCH status")
                except Exception as e:
                    self.logger.warning(f"Failed to check model governance: {e}")
"""

if "Governance Check" not in content:
    content = content.replace(
        "model_id = input_data.config.model_id or input_data.config.model_path or \"unknown\"",
        "model_id = input_data.config.model_id or input_data.config.model_path or \"unknown\"\n" + predict_hook
    )

    # We also need to add these fields to the final success result creation
    res_creation = """res = MLInferenceResult(
                symbol=input_data.symbol,"""
    res_creation_new = """res = MLInferenceResult(
                symbol=input_data.symbol,
                governance_status=assessment.status if 'assessment' in locals() else None,
                validation_status=assessment.validation_status if 'assessment' in locals() else None,
                calibration_status=assessment.calibration_status if 'assessment' in locals() else None,"""

    content = content.replace(res_creation, res_creation_new)

with open(path, "w") as f:
    f.write(content)
