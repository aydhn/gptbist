import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.models import KillSwitchState, KillSwitchScope
from bist_signal_bot.core.exceptions import KillSwitchActiveError
from bist_signal_bot.storage.paths import ensure_dir

class KillSwitchManager:
    """Manages the operational kill switch state."""

    def __init__(self, settings: Settings, base_dir: Path):
        self.settings = settings
        self.security_dir = ensure_dir(base_dir / "security")
        self.file_path = self.security_dir / getattr(settings, "SECURITY_KILL_SWITCH_FILE_NAME", "kill_switch.json")

    def load_state(self) -> KillSwitchState:
        if not self.file_path.exists():
            return KillSwitchState(enabled=False)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            scopes = [KillSwitchScope(s) for s in data.get("scopes", [])]
            activated_at = None
            if data.get("activated_at"):
                try:
                    activated_at = datetime.fromisoformat(data["activated_at"])
                except ValueError:
                    pass

            return KillSwitchState(
                enabled=data.get("enabled", False),
                scopes=scopes,
                reason=data.get("reason"),
                activated_at=activated_at,
                activated_by=data.get("activated_by"),
                metadata=data.get("metadata", {})
            )
        except Exception:
            # Fail-safe: if file is corrupted, assume active for ALL
            return KillSwitchState(
                enabled=True,
                scopes=[KillSwitchScope.ALL],
                reason="Corrupted kill_switch.json. Defaulting to safe mode."
            )

    def save_state(self, state: KillSwitchState) -> Path:
        data = {
            "enabled": state.enabled,
            "scopes": [s.value for s in state.scopes],
            "reason": state.reason,
            "activated_at": state.activated_at.isoformat() if state.activated_at else None,
            "activated_by": state.activated_by,
            "metadata": state.metadata
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return self.file_path

    def activate(self, scopes: list[KillSwitchScope], reason: str, activated_by: str = "local_user") -> KillSwitchState:
        if not getattr(self.settings, "SECURITY_KILL_SWITCH_ENABLED", True):
            # Even if disabled in settings, allow manual hard-stop override.
            pass

        state = KillSwitchState(
            enabled=True,
            scopes=scopes,
            reason=reason,
            activated_at=datetime.now(timezone.utc),
            activated_by=activated_by
        )
        self.save_state(state)
        return state

    def deactivate(self, confirm: bool = False) -> KillSwitchState:
        if not confirm:
            raise ValueError("Must provide confirm=True to deactivate kill switch.")

        state = KillSwitchState(enabled=False)
        self.save_state(state)
        return state

    def is_active(self, scope: KillSwitchScope = KillSwitchScope.ALL) -> bool:
        state = self.load_state()
        return state.is_active_for(scope)

    def assert_not_active(self, scope: KillSwitchScope) -> None:
        state = self.load_state()
        if state.is_active_for(scope):
            raise KillSwitchActiveError(f"Kill switch is currently ACTIVE for scope {scope.value}. Reason: {state.reason}")

    def status(self) -> dict[str, Any]:
        state = self.load_state()
        return {
            "enabled": state.enabled,
            "scopes": [s.value for s in state.scopes],
            "reason": state.reason,
            "activated_at": state.activated_at.isoformat() if state.activated_at else None,
            "activated_by": state.activated_by
        }
