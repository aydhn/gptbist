import json
from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import EnsembleWeightError
from bist_signal_bot.ensemble.models import EnsembleWeights
from bist_signal_bot.storage.paths import get_ensemble_dir
from bist_signal_bot.security.path_guard import PathGuard


class EnsembleWeightManager:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def default_weights(self) -> EnsembleWeights:
        return EnsembleWeights(
            strategy_weight=self.settings.ENSEMBLE_WEIGHT_STRATEGY,
            indicator_weight=self.settings.ENSEMBLE_WEIGHT_INDICATOR,
            pattern_weight=self.settings.ENSEMBLE_WEIGHT_PATTERN,
            divergence_weight=self.settings.ENSEMBLE_WEIGHT_DIVERGENCE,
            ml_weight=self.settings.ENSEMBLE_WEIGHT_ML,
            regime_weight=self.settings.ENSEMBLE_WEIGHT_REGIME,
            risk_weight=self.settings.ENSEMBLE_WEIGHT_RISK,
            fundamental_weight=self.settings.ENSEMBLE_WEIGHT_FUNDAMENTAL,
            breadth_weight=self.settings.ENSEMBLE_WEIGHT_BREADTH,
            relative_strength_weight=self.settings.ENSEMBLE_WEIGHT_RELATIVE_STRENGTH,
            sector_rotation_weight=self.settings.ENSEMBLE_WEIGHT_SECTOR_ROTATION,
            adaptive_weight=self.settings.ENSEMBLE_WEIGHT_ADAPTIVE,
        )

    def weights_for_regime(self, regime_name: Optional[str], base_weights: EnsembleWeights) -> EnsembleWeights:
        if not regime_name:
            return base_weights.normalized()

        w = base_weights.model_copy()
        rn = regime_name.upper()

        if rn == "TRENDING":
            w.strategy_weight *= 1.2
            w.breadth_weight *= 1.2
            w.relative_strength_weight *= 1.2
            w.risk_weight *= 0.8
        elif rn == "RANGE":
            w.pattern_weight *= 1.5
            w.divergence_weight *= 1.5
            w.strategy_weight *= 0.8
        elif rn == "STRESSED":
            w.risk_weight *= 1.5
            w.regime_weight *= 1.5
            w.breadth_weight *= 1.5
            w.strategy_weight *= 0.5
            w.ml_weight *= 0.5

        return w.normalized()

    def validate_weights(self, weights: EnsembleWeights) -> None:
        try:
            weights.validate_weights()
            weights.normalized()
        except ValueError as e:
            raise EnsembleWeightError(str(e))

    def normalize_weights(self, weights: EnsembleWeights) -> EnsembleWeights:
        try:
            return weights.normalized()
        except ValueError as e:
            raise EnsembleWeightError(str(e))

    def _get_weights_path(self, path: Optional[Path] = None) -> Path:
        if path:
            return path
        ens_dir = get_ensemble_dir(self.settings)
        return ens_dir / "weights" / "ensemble_weights.json"

    def load_weights(self, path: Optional[Path] = None) -> EnsembleWeights:
        p = self._get_weights_path(path)
        if not p.exists():
            return self.default_weights()

        try:
            PathGuard(self.settings).resolve_safe_path(p)
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                return EnsembleWeights(**data)
        except Exception as e:
            raise EnsembleWeightError(f"Failed to load weights from {p}: {e}")

    def save_weights(self, weights: EnsembleWeights, path: Optional[Path] = None, confirm: bool = False) -> Path:
        if not confirm:
            raise EnsembleWeightError("Cannot save weights without explicit confirmation (confirm=True)")

        self.validate_weights(weights)
        p = self._get_weights_path(path)

        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            PathGuard(self.settings).resolve_safe_path(p.parent)

            with open(p, "w", encoding="utf-8") as f:
                json.dump(weights.model_dump(), f, indent=2)
            return p
        except Exception as e:
            raise EnsembleWeightError(f"Failed to save weights to {p}: {e}")
