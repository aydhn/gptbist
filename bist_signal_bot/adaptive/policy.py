import json
import logging
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import AdaptivePolicy, AdaptiveMode
from bist_signal_bot.core.exceptions import AdaptivePolicyError

class AdaptivePolicyManager:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)

    def build_default_policy(self, settings: Settings | None = None) -> AdaptivePolicy:
        s = settings or self.settings
        if not s:
            return AdaptivePolicy()

        try:
            return AdaptivePolicy(
                mode=AdaptiveMode(s.ADAPTIVE_MODE),
                min_evidence_count=s.ADAPTIVE_MIN_EVIDENCE_COUNT,
                min_backtest_trades=s.ADAPTIVE_MIN_BACKTEST_TRADES,
                min_walk_forward_splits=s.ADAPTIVE_MIN_WALK_FORWARD_SPLITS,
                min_oos_positive_split_pct=s.ADAPTIVE_MIN_OOS_POSITIVE_SPLIT_PCT,
                max_allowed_drawdown_pct=s.ADAPTIVE_MAX_ALLOWED_DRAWDOWN_PCT,
                min_profit_factor=s.ADAPTIVE_MIN_PROFIT_FACTOR,
                min_sharpe=s.ADAPTIVE_MIN_SHARPE,
                min_paper_trades=s.ADAPTIVE_MIN_PAPER_TRADES,
                max_recent_paper_drawdown_pct=s.ADAPTIVE_MAX_RECENT_PAPER_DRAWDOWN_PCT,
                max_model_age_days=s.ADAPTIVE_MAX_MODEL_AGE_DAYS,
                min_ml_score=s.ADAPTIVE_MIN_ML_SCORE,
                require_regime_match=s.ADAPTIVE_REQUIRE_REGIME_MATCH,
                reject_high_overfit_warning=s.ADAPTIVE_REJECT_HIGH_OVERFIT_WARNING,
                auto_apply_requires_confirm=s.ADAPTIVE_AUTO_APPLY_REQUIRES_CONFIRM
            )
        except Exception as e:
            self.logger.warning(f"Error building policy from settings, using default: {e}")
            return AdaptivePolicy()

    def load_policy(self, path: Path | None = None) -> AdaptivePolicy:
        if path is None:
            return self.build_default_policy()
        if not path.exists():
            return self.build_default_policy()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AdaptivePolicy.model_validate(data)
        except Exception as e:
            self.logger.error(f"Error loading adaptive policy from {path}: {e}")
            raise AdaptivePolicyError(f"Failed to load policy: {e}")

    def save_policy(self, policy: AdaptivePolicy, path: Path) -> Path:
        try:
            self.validate_policy(policy)
            path.parent.mkdir(parents=True, exist_ok=True)

            from bist_signal_bot.security.path_guard import PathGuard
            PathGuard([path]).resolve_safe_path(path)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(policy.model_dump(mode='json'), f, indent=2)
            self.logger.info(f"Saved adaptive policy to {path}")
            return path
        except Exception as e:
            raise AdaptivePolicyError(f"Failed to save policy: {e}")

    def validate_policy(self, policy: AdaptivePolicy) -> None:
        pass

    def policy_summary(self, policy: AdaptivePolicy) -> dict[str, Any]:
        return {
            "mode": policy.mode.value,
            "min_evidence": policy.min_evidence_count,
            "min_trades": policy.min_backtest_trades,
            "max_drawdown": policy.max_allowed_drawdown_pct,
            "auto_apply_safe": policy.auto_apply_requires_confirm
        }
