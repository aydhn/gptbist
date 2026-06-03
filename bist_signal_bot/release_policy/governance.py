import uuid
from datetime import datetime
from typing import Any, Dict, List
from bist_signal_bot.release_policy.models import (
    ReleasePolicyGovernanceAssessment, ReleasePolicyStatus
)

class ReleasePolicyGovernanceEngine:
    def __init__(self) -> None:
        pass

    def assess_release_policy(self) -> ReleasePolicyGovernanceAssessment:
        bp_stat = self.assess_branch_policies()
        ver_stat = self.assess_versioning()
        compat_stat = self.assess_compatibility()
        cl_stat = self.assess_changelog()
        mig_stat = self.assess_migrations()
        dep_stat = self.assess_deprecations()
        frz_stat = self.assess_freeze()
        cls_stat = self.assess_closure()

        parts = [bp_stat, ver_stat, compat_stat, cl_stat, mig_stat, dep_stat, frz_stat, cls_stat]
        blocking = self.blocking_reasons()

        status = self.status_from_parts(parts, blocking)

        return ReleasePolicyGovernanceAssessment(
            assessment_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            status=status,
            branch_policy_status=bp_stat,
            version_status=ver_stat,
            compatibility_status=compat_stat,
            changelog_status=cl_stat,
            migration_status=mig_stat,
            deprecation_status=dep_stat,
            freeze_status=frz_stat,
            closure_status=cls_stat,
            unsafe_language_findings=[],
            blocking_reasons=blocking
        )

    def assess_branch_policies(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_versioning(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_compatibility(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_changelog(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_migrations(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_deprecations(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_freeze(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def assess_closure(self) -> ReleasePolicyStatus:
        return ReleasePolicyStatus.PASS

    def unsafe_language_findings(self, text: str) -> List[str]:
        findings = []
        lower_text = text.lower()
        unsafe_terms = ["trade ready", "işlem yapılabilir", "al/sat", "hedef fiyat", "live ready", "deployment approved", "broker ready"]
        for term in unsafe_terms:
            if term in lower_text:
                findings.append(f"Found unsafe language: '{term}'")
        return findings

    def blocking_reasons(self) -> List[str]:
        # Return empty list if no blocks
        return []

    def status_from_parts(self, parts: List[ReleasePolicyStatus], blocking: List[str]) -> ReleasePolicyStatus:
        if blocking:
            return ReleasePolicyStatus.BLOCKED
        if ReleasePolicyStatus.BLOCKED in parts:
            return ReleasePolicyStatus.BLOCKED
        if ReleasePolicyStatus.FAIL in parts:
            return ReleasePolicyStatus.FAIL
        if ReleasePolicyStatus.WATCH in parts:
            return ReleasePolicyStatus.WATCH
        return ReleasePolicyStatus.PASS
