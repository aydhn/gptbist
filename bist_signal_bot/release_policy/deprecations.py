import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.release_policy.models import DeprecationNotice, ReleasePolicyStatus

class DeprecationPolicyManager:
    def __init__(self) -> None:
        self._active: List[DeprecationNotice] = []

    def default_deprecations(self) -> List[DeprecationNotice]:
        return self._active

    def create_deprecation(self, feature_name: str, deprecated_since: str, reason: str, replacement: Optional[str] = None, removal_target_version: Optional[str] = None) -> DeprecationNotice:
        notice = DeprecationNotice(
            deprecation_id=str(uuid.uuid4()),
            feature_name=feature_name,
            deprecated_since=deprecated_since,
            removal_target_version=removal_target_version,
            replacement=replacement,
            reason=reason,
            status=ReleasePolicyStatus.DRAFT
        )
        self._active.append(notice)
        return notice

    def validate_deprecation_notice(self, notice: DeprecationNotice) -> List[str]:
        errors = []
        if notice.removal_target_version and not self._is_valid_semver_target(notice.removal_target_version):
            errors.append(f"Invalid removal target version: {notice.removal_target_version}")
        if "live" in notice.feature_name.lower() or "broker" in notice.feature_name.lower():
            errors.append("Deprecated feature names cannot imply live/broker capabilities.")
        return errors

    def _is_valid_semver_target(self, target: str) -> bool:
        # Simple check for X.Y format
        import re
        return bool(re.match(r"^([0-9]+)\.([0-9]+)(?:\.[0-9]+)?$", target))

    def active_deprecations(self) -> List[DeprecationNotice]:
        return self._active

    def format_deprecations_markdown(self, notices: List[DeprecationNotice]) -> str:
        lines = ["# Deprecation Notices\n"]
        for notice in notices:
            lines.append(f"## {notice.feature_name} (since {notice.deprecated_since})")
            lines.append(f"Reason: {notice.reason}")
            if notice.replacement:
                lines.append(f"Replacement: {notice.replacement}")
            if notice.removal_target_version:
                lines.append(f"Target removal: {notice.removal_target_version}")
            lines.append(f"\n> *{notice.disclaimer}*\n")
        return "\n".join(lines)
