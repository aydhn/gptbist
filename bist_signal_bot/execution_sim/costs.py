from typing import Any
import uuid

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.execution_sim.models import (
    TransactionCostConfig,
    TransactionCostBreakdown,
    SimulatedOrder,
    SimulatedOrderSide,
)

class TransactionCostModel:
    def default_config(self, settings: Settings | None = None) -> TransactionCostConfig:
        s = settings or Settings()
        return TransactionCostConfig(
            config_id=str(uuid.uuid4()),
            commission_bps=getattr(s, "EXECUTION_COMMISSION_BPS", 5.0),
            min_commission=getattr(s, "EXECUTION_MIN_COMMISSION", 0.0),
            tax_bps_placeholder=getattr(s, "EXECUTION_TAX_BPS_PLACEHOLDER", 0.0),
            exchange_fee_bps_placeholder=getattr(s, "EXECUTION_EXCHANGE_FEE_BPS_PLACEHOLDER", 0.0),
            include_spread_cost=getattr(s, "EXECUTION_INCLUDE_SPREAD_COST", True),
            include_slippage_cost=getattr(s, "EXECUTION_INCLUDE_SLIPPAGE_COST", True),
            include_market_impact=getattr(s, "EXECUTION_INCLUDE_MARKET_IMPACT", True),
            warnings=["Using default settings. Vergi/masraf placeholder'dır, resmi beyan degildir."]
        )

    def estimate_cost(
        self,
        order: SimulatedOrder,
        fill_price: float,
        config: TransactionCostConfig | None = None,
        slippage_cost: float = 0.0,
        spread_cost: float = 0.0,
        market_impact_cost: float = 0.0
    ) -> TransactionCostBreakdown:
        cfg = config or self.default_config()
        notional = fill_price * order.quantity

        commission = max((notional * cfg.commission_bps) / 10000.0, cfg.min_commission)
        tax = (notional * cfg.tax_bps_placeholder) / 10000.0
        exchange_fee = (notional * cfg.exchange_fee_bps_placeholder) / 10000.0

        eff_spread = spread_cost if cfg.include_spread_cost else 0.0
        eff_slippage = slippage_cost if cfg.include_slippage_cost else 0.0
        eff_market = market_impact_cost if cfg.include_market_impact else 0.0

        total_cost = commission + tax + exchange_fee + eff_spread + eff_slippage + eff_market
        rounding_cost = 0.0

        if order.side == SimulatedOrderSide.BUY:
            net_notional = notional + total_cost
        elif order.side == SimulatedOrderSide.SELL:
            net_notional = notional - total_cost
        else:
            net_notional = notional

        bps = self.cost_bps(total_cost, notional)

        return TransactionCostBreakdown(
            breakdown_id=str(uuid.uuid4()),
            notional=notional,
            side=order.side,
            gross_price=fill_price,
            quantity=order.quantity,
            commission=commission,
            tax_placeholder=tax,
            exchange_fee_placeholder=exchange_fee,
            spread_cost=eff_spread,
            slippage_cost=eff_slippage,
            market_impact_cost=eff_market,
            rounding_cost=rounding_cost,
            total_cost=total_cost,
            total_cost_bps=bps,
            net_notional=net_notional,
            warnings=cfg.warnings
        )

    def estimate_round_trip_cost(
        self,
        entry_order: SimulatedOrder,
        exit_order: SimulatedOrder,
        entry_price: float,
        exit_price: float,
        config: TransactionCostConfig | None = None
    ) -> dict[str, Any]:
        entry_cost = self.estimate_cost(entry_order, entry_price, config)
        exit_cost = self.estimate_cost(exit_order, exit_price, config)
        return {
            "entry_cost": entry_cost,
            "exit_cost": exit_cost,
            "total_round_trip_cost": entry_cost.total_cost + exit_cost.total_cost,
            "net_profit": exit_cost.net_notional - entry_cost.net_notional if entry_order.side == SimulatedOrderSide.BUY else entry_cost.net_notional - exit_cost.net_notional
        }

    def cost_bps(self, total_cost: float, notional: float) -> float | None:
        if notional <= 0:
            return None
        return (total_cost / notional) * 10000.0

    def net_price_for_side(self, side: SimulatedOrderSide, fill_price: float, unit_cost: float) -> float:
        if side == SimulatedOrderSide.BUY:
            return fill_price + unit_cost
        elif side == SimulatedOrderSide.SELL:
            return fill_price - unit_cost
        return fill_price
