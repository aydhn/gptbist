import uuid
from typing import Any

from bist_signal_bot.monte_carlo.models import CostRandomizationConfig
from bist_signal_bot.monte_carlo.randomness import MonteCarloRandomState
from bist_signal_bot.config.settings import Settings

class CostRandomizer:
    def __init__(self, random_state: MonteCarloRandomState | None = None):
        self.random_state = random_state or MonteCarloRandomState()

    def default_config(self, settings: Settings | None = None) -> CostRandomizationConfig:
        s = settings or Settings()
        return CostRandomizationConfig(
            config_id=str(uuid.uuid4()),
            commission_multiplier_min=s.MONTE_CARLO_COMMISSION_MULTIPLIER_MIN,
            commission_multiplier_max=s.MONTE_CARLO_COMMISSION_MULTIPLIER_MAX,
            slippage_multiplier_min=s.MONTE_CARLO_SLIPPAGE_MULTIPLIER_MIN,
            slippage_multiplier_max=s.MONTE_CARLO_SLIPPAGE_MULTIPLIER_MAX,
            spread_multiplier_min=s.MONTE_CARLO_SPREAD_MULTIPLIER_MIN,
            spread_multiplier_max=s.MONTE_CARLO_SPREAD_MULTIPLIER_MAX,
            market_impact_multiplier_min=1.0,
            market_impact_multiplier_max=2.0,
            deterministic_seed=s.MONTE_CARLO_DEFAULT_SEED
        )

    def randomize_trade_costs(self, trades: list[dict[str, Any]], config: CostRandomizationConfig, seed: int) -> list[dict[str, Any]]:
        if not trades:
            return []

        result = []
        rng = self.random_state.create_rng(seed)

        for trade in trades:
            t = dict(trade)
            # Simulate random multiplier for slippage/cost
            if hasattr(rng, 'uniform'):
                mult = rng.uniform(config.slippage_multiplier_min, config.slippage_multiplier_max)
            else:
                mult = config.slippage_multiplier_min + (config.slippage_multiplier_max - config.slippage_multiplier_min) * rng.random()

            t = self.apply_slippage_multiplier(t, mult)
            result.append(t)

        return result

    def randomize_returns_for_costs(self, returns: list[float], config: CostRandomizationConfig, seed: int) -> list[float]:
        if not returns:
            return []

        result = []
        rng = self.random_state.create_rng(seed)

        for r in returns:
            if hasattr(rng, 'uniform'):
                mult = rng.uniform(config.slippage_multiplier_min, config.slippage_multiplier_max)
            else:
                mult = config.slippage_multiplier_min + (config.slippage_multiplier_max - config.slippage_multiplier_min) * rng.random()

            # Simple assumption: Cost drag reduces net return.
            # If r is 2.0%, maybe cost is 0.1%, so mult=1.5 means cost becomes 0.15%.
            # Without explicit cost data, we apply a small random haircut.
            haircut = 0.05 * mult  # 5 bps base * multiplier
            new_r = r - haircut
            result.append(new_r)

        return result

    def apply_slippage_multiplier(self, trade: dict[str, Any], multiplier: float) -> dict[str, Any]:
        gross = trade.get("gross_return_pct", 0.0)
        net = trade.get("net_return_pct", gross)

        # Calculate current cost drag
        cost_drag = gross - net
        if cost_drag < 0:
            cost_drag = 0.0

        # Apply multiplier
        new_cost_drag = cost_drag * multiplier
        new_net = gross - new_cost_drag

        trade["net_return_pct"] = new_net
        trade["cost"] = trade.get("cost", 0.0) * multiplier
        trade["metadata"] = trade.get("metadata", {})
        trade["metadata"]["cost_randomized"] = True
        trade["metadata"]["cost_multiplier"] = multiplier
        return trade
