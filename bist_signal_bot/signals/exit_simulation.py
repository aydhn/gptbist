import uuid
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Optional
from bist_signal_bot.signals.models import (
    TrackedSignal, ResearchExitSimulation, ResearchExitRule,
    ResearchExitRuleType, SignalOutcomeState
)
from bist_signal_bot.config.settings import get_settings

class ResearchExitSimulator:
    def __init__(self):
        self.settings = get_settings()

    def simulate(self, signal: TrackedSignal, price_data: pd.DataFrame, rules: List[ResearchExitRule], as_of_date: Optional[datetime] = None) -> ResearchExitSimulation:
        if price_data is None or price_data.empty:
            raise ValueError(f"Price data required for exit simulation for {signal.symbol}")

        now = datetime.now(timezone.utc)
        as_of = as_of_date or now

        # Prevent look-ahead bias
        # Keep only rows <= as_of
        try:
             # Ensure index is datetime and localized/naive match
             df = price_data.copy()
             if df.index.tz is None and as_of.tz is not None:
                  df.index = df.index.tz_localize('UTC')
             df = df[df.index <= as_of]
        except Exception:
             # Fallback
             df = price_data

        ref_price = self.calculate_reference_price(signal, df)

        rule_triggered, outcome = self.evaluate_rules(signal, df, rules)

        curr_price = df['Close'].iloc[-1] if not df.empty and 'Close' in df.columns else None

        ret_pct = None
        if ref_price and curr_price:
             if signal.direction == "LONG":
                  ret_pct = ((curr_price - ref_price) / ref_price) * 100
             elif signal.direction == "SHORT":
                  ret_pct = ((ref_price - curr_price) / ref_price) * 100

        sim = ResearchExitSimulation(
            simulation_id=str(uuid.uuid4()),
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            started_at=signal.created_at,
            evaluated_at=now,
            entry_reference_price=ref_price,
            current_price=curr_price,
            triggered_rule=rule_triggered,
            outcome_state=outcome,
            simulated_return_pct=ret_pct
        )

        # Optional: set targets from rules
        for r in rules:
            if r.rule_type == ResearchExitRuleType.FIXED_PERCENT_TARGET and ref_price:
                sim.target_price = ref_price * (1 + r.value/100) if signal.direction == "LONG" else ref_price * (1 - r.value/100)
            elif r.rule_type == ResearchExitRuleType.FIXED_PERCENT_STOP and ref_price:
                sim.stop_price = ref_price * (1 - r.value/100) if signal.direction == "LONG" else ref_price * (1 + r.value/100)

        return sim

    def build_default_rules(self, signal: TrackedSignal) -> List[ResearchExitRule]:
        rules = []
        rules.append(ResearchExitRule(
            rule_id=str(uuid.uuid4()),
            rule_type=ResearchExitRuleType.FIXED_PERCENT_TARGET,
            value=getattr(self.settings, "SIGNAL_EXIT_DEFAULT_TARGET_PCT", 8.0)
        ))
        rules.append(ResearchExitRule(
            rule_id=str(uuid.uuid4()),
            rule_type=ResearchExitRuleType.FIXED_PERCENT_STOP,
            value=getattr(self.settings, "SIGNAL_EXIT_DEFAULT_STOP_PCT", 4.0)
        ))
        rules.append(ResearchExitRule(
            rule_id=str(uuid.uuid4()),
            rule_type=ResearchExitRuleType.TIME_STOP,
            value=getattr(self.settings, "SIGNAL_EXIT_DEFAULT_TIME_STOP_DAYS", 10)
        ))
        return rules

    def calculate_reference_price(self, signal: TrackedSignal, price_data: pd.DataFrame) -> Optional[float]:
        if price_data.empty or 'Close' not in price_data.columns:
            return None
        # Try to find the closest price at or after signal creation
        mask = price_data.index >= signal.created_at
        if mask.any():
            return float(price_data[mask]['Close'].iloc[0])
        return float(price_data['Close'].iloc[-1])

    def evaluate_rules(self, signal: TrackedSignal, price_data: pd.DataFrame, rules: List[ResearchExitRule]) -> Tuple[ResearchExitRuleType, SignalOutcomeState]:
        # Simplistic evaluation for Phase 55 MVP
        # Check time stop first
        for r in rules:
            if r.rule_type == ResearchExitRuleType.TIME_STOP and r.enabled:
                if datetime.now(timezone.utc) > signal.created_at + timedelta(days=r.value):
                     return ResearchExitRuleType.TIME_STOP, SignalOutcomeState.TIME_EXPIRED

        if price_data.empty:
            return ResearchExitRuleType.NONE, SignalOutcomeState.PENDING

        ref_price = self.calculate_reference_price(signal, price_data)
        if not ref_price:
            return ResearchExitRuleType.NONE, SignalOutcomeState.PENDING

        curr_price = float(price_data['Close'].iloc[-1])
        ret_pct = ((curr_price - ref_price) / ref_price) * 100 if signal.direction == "LONG" else ((ref_price - curr_price) / ref_price) * 100

        for r in rules:
            if r.rule_type == ResearchExitRuleType.FIXED_PERCENT_TARGET and r.enabled:
                 if ret_pct >= r.value:
                     return ResearchExitRuleType.FIXED_PERCENT_TARGET, SignalOutcomeState.HIT_RESEARCH_TARGET
            elif r.rule_type == ResearchExitRuleType.FIXED_PERCENT_STOP and r.enabled:
                 if ret_pct <= -r.value:
                     return ResearchExitRuleType.FIXED_PERCENT_STOP, SignalOutcomeState.HIT_RESEARCH_STOP

        return ResearchExitRuleType.NONE, SignalOutcomeState.PENDING

    def simulate_batch(self, signals: List[TrackedSignal], data_by_symbol: Dict[str, pd.DataFrame]) -> List[ResearchExitSimulation]:
        results = []
        for s in signals:
            df = data_by_symbol.get(s.symbol)
            if df is not None:
                rules = self.build_default_rules(s)
                sim = self.simulate(s, df, rules)
                results.append(sim)
        return results
