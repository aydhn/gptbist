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
        valid_decisions, rejected, items, issues, reduced = self._filter_valid_decisions(request)

        if not valid_decisions:
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

        raw_weights = self._compute_raw_weights(request, valid_decisions, issues)

        norm_weights = self.normalize_weights(raw_weights)
        capped_weights = self.cap_weights(norm_weights, request.max_symbol_weight_pct)
        final_weights = self.normalize_weights(capped_weights)

        total_allocation_pct = request.total_allocation_pct
        for k in final_weights.keys():
            final_weights[k] *= total_allocation_pct

        total_notional, act_items = self._calculate_target_allocations(
            request, final_weights, valid_decisions, rejected, reduced
        )

        items.extend(act_items)

        total_equity = request.portfolio_state.equity

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

    def _filter_valid_decisions(self, request: AllocationRequest) -> tuple[list[RiskDecision], list[str], list[AllocationResultItem], list[str], list[str]]:
        valid_decisions = []
        rejected = []
        for d in request.risk_decisions:
            if d.status.value not in ["REJECTED", "WATCH_ONLY"]:
                valid_decisions.append(d)
            else:
                rejected.append(d.signal.symbol)

        items = []
        issues = []
        reduced = []

        if not valid_decisions:
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
        return valid_decisions, rejected, items, issues, reduced

    def _compute_raw_weights(self, request: AllocationRequest, valid_decisions: list[RiskDecision], issues: list[str]) -> dict[str, float]:
        raw_weights = {}

        if request.method == AllocationMethod.EQUAL_WEIGHT:
            w = 1.0 / len(valid_decisions)
            raw_weights = {d.signal.symbol: w for d in valid_decisions}
        elif request.method == AllocationMethod.SCORE_WEIGHTED:
            total_score = sum(d.signal.score for d in valid_decisions)
            if total_score > 0:
                raw_weights = {d.signal.symbol: d.signal.score / total_score for d in valid_decisions}
            else:
                w = 1.0 / len(valid_decisions)
                raw_weights = {d.signal.symbol: w for d in valid_decisions}
        elif request.method == AllocationMethod.RISK_PARITY_SIMPLE:
            inv_risks = {}
            for d in valid_decisions:
                r_pct = d.risk_pct or 0.01
                if r_pct <= 0: r_pct = 0.01
                inv_risks[d.signal.symbol] = 1.0 / r_pct
            tot_inv = sum(inv_risks.values())
            if tot_inv > 0:
                raw_weights = {s: ir / tot_inv for s, ir in inv_risks.items()}
            else:
                w = 1.0 / len(valid_decisions)
                raw_weights = {d.signal.symbol: w for d in valid_decisions}
        elif request.method == AllocationMethod.VOLATILITY_SCALED:
            w = 1.0 / len(valid_decisions)
            raw_weights = {d.signal.symbol: w for d in valid_decisions}
            issues.append("VOLATILITY_SCALED fallback to EQUAL_WEIGHT")
        elif request.method == AllocationMethod.LIQUIDITY_WEIGHTED:
            w = 1.0 / len(valid_decisions)
            raw_weights = {d.signal.symbol: w for d in valid_decisions}
            issues.append("LIQUIDITY_WEIGHTED fallback to EQUAL_WEIGHT")
        elif request.method == AllocationMethod.RISK_BUDGET:
            raw_weights = {d.signal.symbol: d.risk_pct or 0.01 for d in valid_decisions}
        elif request.method == AllocationMethod.HYBRID:
            w = 1.0 / len(valid_decisions)
            raw_weights = {d.signal.symbol: w for d in valid_decisions}
        else:
            w = 1.0 / len(valid_decisions)
            raw_weights = {d.signal.symbol: w for d in valid_decisions}
            issues.append("Unknown method, fallback to EQUAL_WEIGHT")

        return raw_weights

    def _calculate_target_allocations(
        self, request: AllocationRequest, final_weights: dict[str, float],
        valid_decisions: list[RiskDecision], rejected: list[str], reduced: list[str]
    ) -> tuple[float, list[AllocationResultItem]]:
        total_equity = request.portfolio_state.equity
        available_cash = request.portfolio_state.cash
        min_notional_val = getattr(self.settings, "PORTFOLIO_MIN_ALLOCATION_NOTIONAL", 100.0)
        try:
            min_notional = float(min_notional_val)
        except (ValueError, TypeError):
            min_notional = 100.0
        use_fractional = getattr(self.settings, "PORTFOLIO_USE_FRACTIONAL_SHARES", False)

        items = []
        total_notional = 0.0

        for d in valid_decisions:
            s = d.signal.symbol
            d_pos_size_final_notional = d.position_size.final_notional if d.position_size else None

            target_wt = final_weights.get(s, 0.0)
            target_notional = target_wt * total_equity

            if d.position_size and d_pos_size_final_notional < target_notional:
                target_notional = d_pos_size_final_notional

            price = d.signal.entry_reference_price or 1.0
            qty = self.quantity_from_notional(target_notional, price, use_fractional)
            actual_notional = qty * price

            if actual_notional < min_notional:
                items.append(AllocationResultItem(
                    symbol=s, approved=False, original_notional=d_pos_size_final_notional,
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
                    symbol=s, approved=False, original_notional=d_pos_size_final_notional,
                    allocated_notional=0.0, allocated_weight_pct=0.0, quantity=0.0,
                    reduction_pct=1.0, reasons=["Insufficient cash"], metadata={}
                ))
                 rejected.append(s)
                 continue

            available_cash -= actual_notional
            total_notional += actual_notional
            act_wt = actual_notional / total_equity if total_equity > 0 else 0.0

            red_pct = 0.0
            if d_pos_size_final_notional and actual_notional < d_pos_size_final_notional:
                red_pct = 1.0 - (actual_notional / d_pos_size_final_notional)
                reduced.append(s)

            items.append(AllocationResultItem(
                symbol=s, approved=True, original_notional=d_pos_size_final_notional,
                allocated_notional=actual_notional, allocated_weight_pct=act_wt,
                quantity=qty, reduction_pct=red_pct, reasons=[], metadata={}
            ))

        return total_notional, items

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
