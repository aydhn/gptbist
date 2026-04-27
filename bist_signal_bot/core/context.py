import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bist_signal_bot.config.settings import Settings


@dataclass
class RuntimeContext:
    run_id: str
    app_name: str
    app_env: str
    started_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

_global_runtime_context: RuntimeContext | None = None

def create_runtime_context(settings: Settings) -> RuntimeContext:
    """Creates a new runtime context with a unique run_id."""
    return RuntimeContext(
        run_id=str(uuid.uuid4())[:8],  # Short UUID
        app_name=settings.APP_NAME,
        app_env=settings.APP_ENV,
        started_at=datetime.now(UTC),
        metadata={}
    )

def get_runtime_context() -> RuntimeContext | None:
    """Gets the global runtime context."""
    return _global_runtime_context

def set_runtime_context(context: RuntimeContext) -> None:
    """Sets the global runtime context."""
    global _global_runtime_context
    _global_runtime_context = context
