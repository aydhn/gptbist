from typing import List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.models import ScenarioResult, ScenarioStepResult, ScenarioStatus

class ScenarioValidator:
    def __init__(self, claim_guard=None, secret_redactor=None, settings: Optional[Settings] = None):
        self.claim_guard = claim_guard
        self.secret_redactor = secret_redactor
        self.settings = settings or Settings()

    def validate_result(self, result: ScenarioResult) -> List[str]:
        issues = []

        # 1. No real order sent disclaimer
        if not result.disclaimer or "No real order was sent" not in result.disclaimer:
            issues.append("Missing required 'No real order was sent' disclaimer.")

        # 2. Step level validations
        for step in result.step_results:
            step_issues = self.validate_step_result(step)
            if step_issues:
                 issues.extend([f"Step {step.step_id}: {i}" for i in step_issues])

        # 3. Overall status sanity
        if any(s.status == ScenarioStatus.FAILED for s in result.step_results) and result.status == ScenarioStatus.SUCCESS:
             issues.append("Result status is SUCCESS but some steps failed.")

        return issues

    def validate_step_result(self, step_result: ScenarioStepResult) -> List[str]:
        issues = []

        stdout = step_result.stdout_tail or ""
        stderr = step_result.stderr_tail or ""
        combined = stdout + stderr

        # Mock secret check
        if self.secret_redactor and hasattr(self.secret_redactor, 'has_secrets') and self.secret_redactor.has_secrets(combined):
            issues.append("Detected possible secrets in output.")
        elif "SECRET_TOKEN" in combined: # fallback
             issues.append("Detected possible secrets in output.")

        # Mock claim check
        if self.claim_guard and hasattr(self.claim_guard, 'has_unsafe_claims') and self.claim_guard.has_unsafe_claims(combined):
            issues.append("Detected unsafe financial claims in output.")
        else:
             claim_issues = self.validate_no_real_order_language(combined)
             issues.extend(claim_issues)

        if step_result.status == ScenarioStatus.TIMEOUT:
            issues.append("Step timed out.")

        return issues

    def validate_no_real_order_language(self, text: str) -> List[str]:
        issues = []
        text_lower = text.lower()
        if "live order executed" in text_lower or "real trade sent" in text_lower:
            issues.append("Found language implying real orders were sent.")
        return issues

    def validate_outputs_exist(self, result: ScenarioResult) -> List[str]:
        import os
        issues = []
        for name, path in result.output_files.items():
            if not os.path.exists(path):
                issues.append(f"Output file {name} at {path} does not exist.")
        return issues
