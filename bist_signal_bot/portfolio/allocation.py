import logging
import math
from typing import Optional
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio.models import (
    AllocationRequest, AllocationResult, AllocationResultItem, AllocationMethod
)
from bist_signal_bot.risk.models import RiskDecision

class PortfolioAllocator:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        from bist_signal_bot.config.settings import settings as default_settings
        self.settings = settings or default_settings
        self.logger = logger or logging.getLogger(__name__)

    def allocate(self, request: AllocationRequest) -> AllocationResult:
        decisions_by_sym = {d.signal.symbol: d for d in request.risk_decisions}

        # Filter for approved ones
        valid_symbols = []
        for d in request.risk_decisions:
            # Assuming risk engine approves if final status is not rejected.
            if d.status.value not in ["REJECTED", "WATCH_ONLY"]:
                valid_symbols.append(d.signal.symbol)

        items = []
        issues = []
        rejected = []
        reduced = []

        if not valid_symbols:
            issues.append("No valid symbols to allocate")
            for d in request.risk_decisions:
                items.append(AllocationResultItem(
                    symbol=d.signal.symbol,
                    approved=False,
                    original_notional=d.position_size.final_notional if d.position_size else None,
                    allocated_notional=0.0,
                    allocated_weight_pct=0.0,
                    quantity=0.0,
                    reduction_pct=1.0,
                    reasons=["Rejected by trade risk"],
                    metadata={}
                ))
                rejected.append(d.signal.symbol)

            return AllocationResult(
                method=request.method,
                items=items,
                total_allocated_notional=0.0,
                total_allocated_pct=0.0,
                rejected_symbols=rejected,
                reduced_symbols=reduced,
                issues=issues,
                generated_at=datetime.utcnow()
            )

        raw_weights = {}

        if request.method == AllocationMethod.EQUAL_WEIGHT:
            w = 1.0 / len(valid_symbols)
            for s in valid_symbols:
                raw_weights[s] = w

        elif request.method == AllocationMethod.SCORE_WEIGHTED:
            total_score = sum(decisions_by_sym[s].signal.score for s in valid_symbols)
            for s in valid_symbols:
                score = decisions_by_sym[s].signal.score
                raw_weights[s] = score / total_score if total_score > 0 else 1.0 / len(valid_symbols)

        elif request.method == AllocationMethod.RISK_PARITY_SIMPLE:
            # Inverse risk weighting
            inv_risks = {}
            for s in valid_symbols:
                r_pct = decisions_by_sym[s].risk_pct or 0.01
                if r_pct <= 0: r_pct = 0.01
                inv_risks[s] = 1.0 / r_pct

            tot_inv = sum(inv_risks.values())
            for s in valid_symbols:
                raw_weights[s] = inv_risks[s] / tot_inv if tot_inv > 0 else 1.0 / len(valid_symbols)

        elif request.method == AllocationMethod.VOLATILITY_SCALED:
            # simple mock
            raw_weights = {s: 1.0/len(valid_symbols) for s in valid_symbols}
            issues.append("VOLATILITY_SCALED fallback to EQUAL_WEIGHT")

        elif request.method == AllocationMethod.LIQUIDITY_WEIGHTED:
            raw_weights = {s: 1.0/len(valid_symbols) for s in valid_symbols}
            issues.append("LIQUIDITY_WEIGHTED fallback to EQUAL_WEIGHT")

        elif request.method == AllocationMethod.RISK_BUDGET:
            for s in valid_symbols:
                r_pct = decisions_by_sym[s].risk_pct or 0.01
                raw_weights[s] = r_pct

        elif request.method == AllocationMethod.HYBRID:
            # 40% score, 30% risk, 20% liq, 10% eq
            for s in valid_symbols:
                raw_weights[s] = 1.0 / len(valid_symbols)
        else:
            raw_weights = {s: 1.0/len(valid_symbols) for s in valid_symbols}
            issues.append("Unknown method, fallback to EQUAL_WEIGHT")

        norm_weights = self.normalize_weights(raw_weights)
        capped_weights = self.cap_weights(norm_weights, request.max_symbol_weight_pct)
        final_weights = self.normalize_weights(capped_weights)

        # Scale by total allocation pct
        for s in valid_symbols:
            final_weights[s] = final_weights[s] * request.total_allocation_pct

        total_equity = request.portfolio_state.equity
        available_cash = request.portfolio_state.cash
        min_notional = getattr(self.settings, "PORTFOLIO_MIN_ALLOCATION_NOTIONAL", 100.0)
        use_fractional = getattr(self.settings, "PORTFOLIO_USE_FRACTIONAL_SHARES", False)

        total_notional = 0.0

        for d in request.risk_decisions:
            s = d.signal.symbol
            if s not in valid_symbols:
                items.append(AllocationResultItem(
                    symbol=s, approved=False, original_notional=d.position_size.final_notional if d.position_size else None,
                    allocated_notional=0.0, allocated_weight_pct=0.0, quantity=0.0,
                    reduction_pct=1.0, reasons=["Rejected by trade risk"], metadata={}
                ))
                rejected.append(s)
                continue

            target_wt = final_weights.get(s, 0.0)
            target_notional = target_wt * total_equity

            # Use original if smaller
            if d.position_size and d.position_size.final_notional < target_notional:
                target_notional = d.position_size.final_notional if d.position_size else None

            price = d.signal.entry_reference_price or 1.0
            qty = self.quantity_from_notional(target_notional, price, use_fractional)
            actual_notional = qty * price

            if actual_notional < min_notional:
                items.append(AllocationResultItem(
                    symbol=s, approved=False, original_notional=d.position_size.final_notional if d.position_size else None,
                    allocated_notional=0.0, allocated_weight_pct=0.0, quantity=0.0,
                    reduction_pct=1.0, reasons=[f"Below min notional {min_notional}"], metadata={}
                ))
                rejected.append(s)
                continue

            if available_cash < actual_notional:
                qty = self.quantity_from_notional(available_cash, price, use_fractional)
                actual_notional = qty * price

            if actual_notional < min_notional:
                 items.append(AllocationResultItem(
                    symbol=s, approved=False, original_notional=d.position_size.final_notional if d.position_size else None,
                    allocated_notional=0.0, allocated_weight_pct=0.0, quantity=0.0,
                    reduction_pct=1.0, reasons=["Insufficient cash"], metadata={}
                ))
                 rejected.append(s)
                 continue

            available_cash -= actual_notional
            total_notional += actual_notional
            act_wt = actual_notional / total_equity if total_equity > 0 else 0.0

            red_pct = 0.0
            if d.position_size.final_notional if d.position_size else None and actual_notional < d.position_size.final_notional if d.position_size else None:
                red_pct = 1.0 - (actual_notional / d.position_size.final_notional if d.position_size else None)
                reduced.append(s)

            items.append(AllocationResultItem(
                symbol=s, approved=True, original_notional=d.position_size.final_notional if d.position_size else None,
                allocated_notional=actual_notional, allocated_weight_pct=act_wt,
                quantity=qty, reduction_pct=red_pct, reasons=[], metadata={}
            ))

        return AllocationResult(
            method=request.method,
            items=items,
            total_allocated_notional=total_notional,
            total_allocated_pct=total_notional / total_equity if total_equity > 0 else 0.0,
            rejected_symbols=rejected,
            reduced_symbols=reduced,
            issues=issues,
            generated_at=datetime.utcnow()
        )

    def normalize_weights(self, raw_weights: dict[str, float]) -> dict[str, float]:
        if not raw_weights:
            return {}
        total = sum(raw_weights.values())
        if total <= 0:
            return {k: 0.0 for k in raw_weights}
        return {k: v / total for k, v in raw_weights.items()}

    def cap_weights(self, weights: dict[str, float], max_symbol_weight: float) -> dict[str, float]:
        capped = {}
        excess = 0.0
        uncapped = []

        for k, v in weights.items():
            if v > max_symbol_weight:
                capped[k] = max_symbol_weight
                excess += v - max_symbol_weight
            else:
                capped[k] = v
                uncapped.append(k)

        # Redistribute excess if possible
        if excess > 0 and uncapped:
            share = excess / len(uncapped)
            for k in uncapped:
                capped[k] += share

            # One more pass to ensure redist didn't breach
            for k in uncapped:
                if capped[k] > max_symbol_weight:
                    capped[k] = max_symbol_weight

        return capped

    def quantity_from_notional(self, notional: float, price: float, fractional: bool) -> float:
        if price <= 0: return 0.0
        qty = notional / price
        if not fractional:
            qty = math.floor(qty)
        return float(qty)
