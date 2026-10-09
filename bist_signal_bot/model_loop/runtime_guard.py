"""Guards for the runtime ML-filter / drift-check flags.

The flags may only be effective when a baseline (or higher) model is registered.
Both functions return ``(enabled: bool, reason: str)``. Research/paper only.
No real order sent.

Flag semantics:
  * flag True (or truthy string)  -> enabled only if a usable model is registered
  * flag the string 'auto'        -> enabled iff a usable model is registered
  * flag False and MODEL_LOOP_AUTO_ENABLE_RUNTIME=True -> enabled iff a usable
    model is registered (so behavior is unchanged while no model exists)
  * flag False and auto disabled  -> False
"""
from __future__ import annotations

import logging
from typing import Any

from bist_signal_bot.model_registry.models import ModelKind, ModelRegistryStatus

logger = logging.getLogger(__name__)

_USABLE = {ModelRegistryStatus.ACTIVE_RESEARCH, ModelRegistryStatus.STAGING, ModelRegistryStatus.WATCH}
_BAD = {ModelRegistryStatus.FAILED_VALIDATION, ModelRegistryStatus.FAILED_CALIBRATION,
        ModelRegistryStatus.BLOCKED_LEAKAGE, ModelRegistryStatus.ARCHIVED, ModelRegistryStatus.MISSING,
        ModelRegistryStatus.UNKNOWN}


def default_registry(settings: Any):
    from bist_signal_bot.model_registry.registry import LocalModelRegistry
    from bist_signal_bot.model_registry.storage import ModelRegistryStore

    return LocalModelRegistry(settings, ModelRegistryStore(settings))


def has_baseline_model(registry: Any) -> bool:
    """True when a baseline-or-higher model is registered (unvetted challengers do not count)."""
    try:
        models = registry.list_models()
    except Exception as exc:
        logger.debug("registry unavailable: %s", exc)
        return False
    for m in models:
        if m.status in _BAD:
            continue
        if m.status in _USABLE or m.model_kind == ModelKind.BASELINE:
            return True
        if m.status == ModelRegistryStatus.CANDIDATE and "challenger" not in (m.tags or []):
            return True
    return False


def _flag(settings: Any, key: str) -> Any:
    try:
        return getattr(settings, key, False)
    except Exception:
        return False


def _effective(settings: Any, registry: Any, key: str) -> tuple[bool, str]:
    raw = _flag(settings, key)
    is_auto = isinstance(raw, str) and raw.strip().lower() == "auto"
    if isinstance(raw, str) and not is_auto:
        raw = raw.strip().lower() in ("1", "true", "yes", "on")
    auto_cfg = bool(getattr(settings, "MODEL_LOOP_AUTO_ENABLE_RUNTIME", False)) if not raw or is_auto else False
    if not raw and not is_auto and not auto_cfg:
        return False, f"{key} is off"
    if registry is None:
        try:
            registry = default_registry(settings)
        except Exception as exc:
            return False, f"{key}: model registry unavailable ({exc})"
    if has_baseline_model(registry):
        return True, "baseline model registered"
    if raw or is_auto:
        return False, f"{key} requested but no baseline model is registered"
    return False, "no baseline model registered"


def ml_filter_effective(settings: Any, registry: Any = None) -> tuple[bool, str]:
    return _effective(settings, registry, "RUNTIME_USE_ML_FILTER")


def drift_check_effective(settings: Any, registry: Any = None) -> tuple[bool, str]:
    return _effective(settings, registry, "RUNTIME_RUN_DRIFT_CHECK")
