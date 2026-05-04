from bist_signal_bot.config.settings import Settings
from bist_signal_bot.costs.commission import CommissionModel
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.costs.models import (
    CommissionModelType,
    CostScenario,
    SlippageModelType,
    SpreadModelType,
)
from bist_signal_bot.costs.slippage import SlippageModel
from bist_signal_bot.costs.spread import SpreadModel


def build_cost_engine_for_scenario(settings: Settings, scenario: CostScenario) -> TransactionCostEngine:
    # Base defaults
    commission_type = CommissionModelType(getattr(settings, "COMMISSION_MODEL_TYPE", "BPS"))
    commission_bps = getattr(settings, "COMMISSION_BPS", 5.0)
    flat_fee = getattr(settings, "COMMISSION_FLAT_FEE", 0.0)
    min_commission = getattr(settings, "COMMISSION_MINIMUM", 0.0)
    tax_bps = getattr(settings, "TRANSACTION_TAX_BPS", 0.0)
    other_fees = getattr(settings, "OTHER_FEE_BPS", 0.0)

    slippage_type = SlippageModelType(getattr(settings, "SLIPPAGE_MODEL_TYPE", "HYBRID"))
    fixed_slippage_bps = getattr(settings, "FIXED_SLIPPAGE_BPS", 5.0)
    volume_impact = getattr(settings, "VOLUME_IMPACT_FACTOR", 10.0)
    volatility_impact = getattr(settings, "VOLATILITY_IMPACT_FACTOR", 0.25)
    min_slippage = getattr(settings, "MIN_SLIPPAGE_BPS", 0.0)
    max_slippage = getattr(settings, "MAX_SLIPPAGE_BPS", 100.0)

    spread_type = SpreadModelType(getattr(settings, "SPREAD_MODEL_TYPE", "LIQUIDITY_BUCKET"))
    fixed_spread = getattr(settings, "FIXED_SPREAD_BPS", 5.0)
    high_liq = getattr(settings, "HIGH_LIQUIDITY_SPREAD_BPS", 3.0)
    med_liq = getattr(settings, "MEDIUM_LIQUIDITY_SPREAD_BPS", 8.0)
    low_liq = getattr(settings, "LOW_LIQUIDITY_SPREAD_BPS", 20.0)

    # Adjust based on scenario
    if scenario == CostScenario.OPTIMISTIC:
        commission_bps = max(0.0, commission_bps * 0.5)
        fixed_slippage_bps = max(0.0, fixed_slippage_bps * 0.5)
        volume_impact *= 0.5
        volatility_impact *= 0.5
        fixed_spread = max(0.0, fixed_spread * 0.5)
        high_liq = max(0.0, high_liq * 0.5)
        med_liq = max(0.0, med_liq * 0.5)
        low_liq = max(0.0, low_liq * 0.5)

    elif scenario == CostScenario.CONSERVATIVE:
        commission_bps = commission_bps * 1.2
        fixed_slippage_bps = fixed_slippage_bps * 2.0
        volume_impact *= 2.0
        volatility_impact *= 2.0
        fixed_spread = fixed_spread * 1.5
        high_liq = high_liq * 1.5
        med_liq = med_liq * 1.5
        low_liq = low_liq * 1.5

    elif scenario == CostScenario.STRESS:
        commission_bps = commission_bps * 1.5
        fixed_slippage_bps = fixed_slippage_bps * 4.0
        volume_impact *= 4.0
        volatility_impact *= 4.0
        max_slippage = max_slippage * 2.0
        fixed_spread = fixed_spread * 3.0
        high_liq = high_liq * 3.0
        med_liq = med_liq * 3.0
        low_liq = low_liq * 3.0

    commission_model = CommissionModel(
        model_type=commission_type,
        commission_bps=commission_bps,
        flat_fee=flat_fee,
        minimum_commission=min_commission,
        tax_bps=tax_bps,
        other_fee_bps=other_fees,
    )

    slippage_model = SlippageModel(
        model_type=slippage_type,
        fixed_slippage_bps=fixed_slippage_bps,
        volume_impact_factor=volume_impact,
        volatility_impact_factor=volatility_impact,
        min_slippage_bps=min_slippage,
        max_slippage_bps=max_slippage,
    )

    spread_model = SpreadModel(
        model_type=spread_type,
        fixed_spread_bps=fixed_spread,
        high_liquidity_spread_bps=high_liq,
        medium_liquidity_spread_bps=med_liq,
        low_liquidity_spread_bps=low_liq,
    )

    return TransactionCostEngine(
        commission_model=commission_model,
        slippage_model=slippage_model,
        spread_model=spread_model,
        settings=settings,
        scenario=scenario,
    )


def list_cost_scenarios() -> list[CostScenario]:
    return [
        CostScenario.OPTIMISTIC,
        CostScenario.BASE,
        CostScenario.CONSERVATIVE,
        CostScenario.STRESS,
    ]


def scenario_description(scenario: CostScenario) -> str:
    if scenario == CostScenario.OPTIMISTIC:
        return "Low commission, low slippage, low spread. Best case scenario."
    elif scenario == CostScenario.BASE:
        return "Default settings from configuration."
    elif scenario == CostScenario.CONSERVATIVE:
        return "Slightly higher commission, 2x slippage, 1.5x spread."
    elif scenario == CostScenario.STRESS:
        return "High commission, 4x slippage, 3x spread. Worst case scenario."
    return "Unknown scenario."
