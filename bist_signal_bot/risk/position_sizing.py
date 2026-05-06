import math
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.costs.models import OrderSide
from .models import (
    PositionSizingMethod, RiskContext, StopTargetReference, PositionSizeResult, RiskSide
)
from bist_signal_bot.core.exceptions import PositionSizingError

class PositionSizer:
    def __init__(self, settings: Settings | None = None, cost_engine: TransactionCostEngine | None = None):
        self.settings = settings or Settings()
        self.cost_engine = cost_engine

    def quantity_from_notional(self, notional: float, price: float, fractional: bool) -> float:
        if price <= 0:
            return 0.0
        raw_qty = notional / price
        if fractional:
            return round(raw_qty, 6)
        else:
            return float(math.floor(raw_qty))

    def estimate_cost(self, symbol: str, side: RiskSide, quantity: float, price: float) -> tuple[float, float | None]:
        if not self.cost_engine or quantity <= 0:
            return 0.0, None

        order_side = OrderSide.BUY if side == RiskSide.LONG else OrderSide.SELL
        try:
            res = self.cost_engine.calculate_costs(symbol, order_side, quantity, price)
            return res.total_cost, res.total_cost_bps
        except Exception:
            return 0.0, None

    def cap_notional(self, raw_notional: float, context: RiskContext, max_position_pct: float) -> tuple[float, bool]:
        capped = raw_notional
        reduced = False

        max_notional_from_pct = context.equity * max_position_pct
        if capped > max_notional_from_pct:
            capped = max_notional_from_pct
            reduced = True

        if capped > context.available_cash:
            capped = context.available_cash
            reduced = True

        return capped, reduced

    def calculate_position_size(self, signal: SignalCandidate, context: RiskContext, stop_target: StopTargetReference | None, method: PositionSizingMethod | None = None) -> PositionSizeResult:
        method = method or PositionSizingMethod(self.settings.RISK_POSITION_SIZING_METHOD)
        side = RiskSide.LONG if signal.direction.value == "LONG" else (RiskSide.SHORT if signal.direction.value == "SHORT" else RiskSide.FLAT)

        entry_price = stop_target.entry_price if stop_target else signal.entry_reference_price
        if not entry_price or entry_price <= 0:
            raise PositionSizingError("Entry price must be provided and > 0")

        stop_price = stop_target.stop_price if stop_target else signal.stop_reference_price
        risk_per_share = stop_target.risk_per_share if stop_target else None

        raw_notional = 0.0
        risk_amount = None
        risk_pct = None
        issues = []

        target_risk_pct = self.settings.RISK_PER_TRADE_PCT
        max_pos_pct = self.settings.RISK_MAX_POSITION_SIZE_PCT

        if side == RiskSide.FLAT:
            return PositionSizeResult(
                method=method, symbol=signal.symbol, side=side, equity=context.equity,
                entry_price=entry_price, stop_price=stop_price, issues=["Signal is FLAT"]
            )

        if method == PositionSizingMethod.FIXED_NOTIONAL:
            raw_notional = self.settings.RISK_FIXED_NOTIONAL

        elif method == PositionSizingMethod.EQUITY_PERCENT:
            raw_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT

        elif method == PositionSizingMethod.RISK_PERCENT:
            risk_amount = context.equity * target_risk_pct
            if risk_per_share and risk_per_share > 0:
                qty = risk_amount / risk_per_share
                raw_notional = qty * entry_price
            else:
                issues.append("Risk percent sizing requested but no valid stop/risk_per_share available. Falling back to equity percent.")
                raw_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT

        elif method == PositionSizingMethod.ATR_RISK:
            if "atr_14" in signal.feature_snapshot and signal.feature_snapshot["atr_14"]:
                atr = signal.feature_snapshot["atr_14"]
                risk_amount = context.equity * target_risk_pct
                qty = risk_amount / (atr * self.settings.RISK_ATR_MULTIPLIER)
                raw_notional = qty * entry_price
            else:
                issues.append("ATR risk sizing requested but no ATR in feature snapshot. Falling back to equity percent.")
                raw_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT

        elif method == PositionSizingMethod.VOLATILITY_TARGET:
            if "hist_vol_20" in signal.feature_snapshot and signal.feature_snapshot["hist_vol_20"]:
                vol = signal.feature_snapshot["hist_vol_20"]
                target_vol = 0.20 # 20% annualized
                scalar = target_vol / max(vol, 0.01)
                base_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT
                raw_notional = base_notional * scalar
            else:
                issues.append("Volatility target sizing requested but no historical vol available. Falling back.")
                raw_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT

        elif method == PositionSizingMethod.KELLY_FRACTIONAL:
            issues.append("Kelly fractional not fully supported yet (needs win prob/payoff). Falling back.")
            raw_notional = context.equity * self.settings.RISK_EQUITY_POSITION_PCT

        elif method == PositionSizingMethod.SCORE_WEIGHTED:
            base_notional = context.equity * max_pos_pct
            score_factor = max(0, min(1, signal.score / 100.0))
            conf_factor = max(0, min(1, signal.confidence / 100.0))
            raw_notional = base_notional * (score_factor * 0.7 + conf_factor * 0.3)

        capped_notional, reduced = self.cap_notional(raw_notional, context, max_pos_pct)

        if capped_notional < self.settings.RISK_MIN_TRADE_NOTIONAL:
            capped_notional = 0.0
            issues.append(f"Notional {capped_notional} is below min trade notional {self.settings.RISK_MIN_TRADE_NOTIONAL}")

        qty = self.quantity_from_notional(capped_notional, entry_price, self.settings.RISK_USE_FRACTIONAL_SHARES)
        final_notional = qty * entry_price

        if final_notional < raw_notional - (entry_price if not self.settings.RISK_USE_FRACTIONAL_SHARES else 0):
             reduced = True

        est_cost, est_cost_bps = self.estimate_cost(signal.symbol, side, qty, entry_price)
        final_position_pct = final_notional / context.equity if context.equity > 0 else 0.0

        actual_risk_amount = None
        actual_risk_pct = None
        if qty > 0 and risk_per_share and risk_per_share > 0:
            actual_risk_amount = qty * risk_per_share
            actual_risk_pct = actual_risk_amount / context.equity

        return PositionSizeResult(
            method=method,
            symbol=signal.symbol,
            side=side,
            equity=context.equity,
            entry_price=entry_price,
            stop_price=stop_price,
            target_risk_pct=target_risk_pct,
            max_position_pct=max_pos_pct,
            raw_notional=raw_notional,
            capped_notional=capped_notional,
            quantity=qty,
            estimated_cost=est_cost,
            final_notional=final_notional,
            final_position_pct=final_position_pct,
            risk_amount=actual_risk_amount,
            risk_pct=actual_risk_pct,
            reduced=reduced,
            issues=issues
        )
