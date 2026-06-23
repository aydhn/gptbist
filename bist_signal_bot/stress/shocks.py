from typing import Protocol

class SnapshotItem(Protocol):
    symbol: str

class SnapshotProtocol(Protocol):
    items: list[SnapshotItem]


from bist_signal_bot.stress.models import (
    StressScenario,
    StressScenarioType,
    StressSeverity,
    ShockScenarioResult,
    StressStatus
)

class ShockScenarioEngine:

    @staticmethod
    def default_scenarios() -> list[StressScenario]:
        return [
            StressScenario(
                scenario_id="market_drop_mild",
                name="Mild Market Drop",
                scenario_type=StressScenarioType.MARKET_SHOCK,
                severity=StressSeverity.LOW,
                market_shock_pct=-5.0
            ),
            StressScenario(
                scenario_id="market_drop_medium",
                name="Medium Market Drop",
                scenario_type=StressScenarioType.MARKET_SHOCK,
                severity=StressSeverity.MEDIUM,
                market_shock_pct=-10.0
            ),
            StressScenario(
                scenario_id="market_drop_severe",
                name="Severe Market Drop",
                scenario_type=StressScenarioType.MARKET_SHOCK,
                severity=StressSeverity.HIGH,
                market_shock_pct=-20.0
            ),
            StressScenario(
                scenario_id="volatility_spike_2x",
                name="Volatility Spike 2x",
                scenario_type=StressScenarioType.VOLATILITY_SPIKE,
                severity=StressSeverity.HIGH,
                volatility_multiplier=2.0
            ),
            StressScenario(
                scenario_id="correlation_spike",
                name="Correlation Spike",
                scenario_type=StressScenarioType.CORRELATION_SPIKE,
                severity=StressSeverity.MEDIUM,
                correlation_multiplier=1.5
            ),
            StressScenario(
                scenario_id="liquidity_haircut",
                name="Liquidity Haircut",
                scenario_type=StressScenarioType.LIQUIDITY_STRESS,
                severity=StressSeverity.HIGH,
                liquidity_haircut_pct=10.0
            ),
            StressScenario(
                scenario_id="losing_streak_5_days",
                name="5 Day Losing Streak",
                scenario_type=StressScenarioType.LOSING_STREAK,
                severity=StressSeverity.MEDIUM,
                losing_streak_days=5
            )
        ]

    def apply_scenario(self, snapshot: SnapshotProtocol, scenario: StressScenario) -> ShockScenarioResult:
        warnings = []
        status = StressStatus.PASS
        item_impacts = {}
        exposure_impacts = {}

        items = getattr(snapshot, "items", [])
        if not items:
            warnings.append("No items in snapshot to apply shock.")
            return ShockScenarioResult(
                result_id=str(uuid.uuid4()),
                scenario=scenario,
                status=StressStatus.WARN,
                warnings=warnings
            )

        if scenario.scenario_type == StressScenarioType.MARKET_SHOCK and scenario.market_shock_pct is not None:
            item_impacts = self.apply_market_shock(items, scenario.market_shock_pct)
        elif scenario.scenario_type == StressScenarioType.SECTOR_SHOCK and scenario.sector_shocks:
            item_impacts = self.apply_sector_shocks(items, scenario.sector_shocks)
            missing = [item.symbol for item in items if not hasattr(item, "sector") or not item.sector]
            if missing:
                warnings.append(f"Missing sector information for {len(missing)} items.")
                status = StressStatus.WARN
        elif scenario.scenario_type == StressScenarioType.CUSTOM and scenario.symbol_shocks:
             item_impacts = self.apply_symbol_shocks(items, scenario.symbol_shocks)
        else:
            warnings.append(f"Scenario type {scenario.scenario_type.name} not fully modeled. Returning zero impacts.")
            item_impacts = {item.symbol: 0.0 for item in items}
            status = StressStatus.PARTIAL

        # Calculate portfolio level impact
        weights = {item.symbol: getattr(item, "weight_pct", 100.0 / len(items)) / 100.0 for item in items}

        portfolio_impact = self.estimate_portfolio_impact(item_impacts, weights)

        total_value = getattr(snapshot, "total_value", 100000.0)
        value_after = total_value * (1 + (portfolio_impact / 100.0))

        return ShockScenarioResult(
            result_id=str(uuid.uuid4()),
            scenario=scenario,
            status=status,
            estimated_portfolio_impact_pct=portfolio_impact,
            estimated_value_after_shock=value_after,
            item_impacts=item_impacts,
            exposure_impacts=exposure_impacts,
            warnings=warnings
        )

    def apply_market_shock(self, items: list[SnapshotItem], shock_pct: float) -> dict[str, float]:
        impacts = {}
        for item in items:
            # Simplified beta approach: assume beta=1 if not present
            beta = getattr(item, "beta", 1.0)
            impacts[item.symbol] = shock_pct * beta
        return impacts

    def apply_sector_shocks(self, items: list[SnapshotItem], sector_shocks: dict[str, float]) -> dict[str, float]:
        impacts = {}
        for item in items:
            sector = getattr(item, "sector", None)
            if sector and sector in sector_shocks:
                impacts[item.symbol] = sector_shocks[sector]
            else:
                impacts[item.symbol] = 0.0
        return impacts

    def apply_symbol_shocks(self, items: list[SnapshotItem], symbol_shocks: dict[str, float]) -> dict[str, float]:
        impacts = {}
        for item in items:
            if item.symbol in symbol_shocks:
                 impacts[item.symbol] = symbol_shocks[item.symbol]
            else:
                 impacts[item.symbol] = 0.0
        return impacts

    def estimate_portfolio_impact(self, item_impacts: dict[str, float], weights: dict[str, float]) -> float:
        total_impact = 0.0
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        for sym, impact in item_impacts.items():
            w = weights.get(sym, 0.0) / total_weight
            total_impact += impact * w

        return total_impact
