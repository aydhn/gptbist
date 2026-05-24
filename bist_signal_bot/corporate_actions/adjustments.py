import pandas as pd
from typing import List, Optional
import uuid
from bist_signal_bot.corporate_actions.models import CorporateActionRecord, PriceAdjustmentFactor, AdjustedPriceResult, AdjustmentDirection, CorporateActionType

class PriceAdjustmentEngine:
    def build_factors(self, symbol: str, actions: List[CorporateActionRecord], direction: AdjustmentDirection = AdjustmentDirection.BACKWARD) -> List[PriceAdjustmentFactor]:
        factors = []
        cum_factor = 1.0

        # Sort by effective date descending for backward
        sorted_actions = sorted(actions, key=lambda x: x.effective_date, reverse=(direction==AdjustmentDirection.BACKWARD))

        for action in sorted_actions:
            factor = self.calculate_factor(action)
            if factor is not None:
                cum_factor *= factor
                factors.append(PriceAdjustmentFactor(
                    factor_id=str(uuid.uuid4()),
                    symbol=symbol,
                    effective_date=action.effective_date,
                    action_ids=[action.action_id],
                    factor=factor,
                    cumulative_factor=cum_factor,
                    direction=direction,
                    source="engine"
                ))
        return factors

    def apply_adjustments(self, symbol: str, raw_df: pd.DataFrame, actions: List[CorporateActionRecord], direction: AdjustmentDirection = AdjustmentDirection.BACKWARD) -> pd.DataFrame:
        factors = self.build_factors(symbol, actions, direction)
        return self.adjust_ohlcv(raw_df, factors)

    def adjust_ohlcv(self, df: pd.DataFrame, factors: List[PriceAdjustmentFactor]) -> pd.DataFrame:
        if df.empty or not factors:
            return df.copy()

        res_df = df.copy()

        # Initialize adjusted columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in res_df.columns:
                res_df[f'adj_{col.lower()}'] = res_df[col]

        res_df['adjustment_factor'] = 1.0
        res_df['cumulative_adjustment_factor'] = 1.0

        # Simple backward adjustment logic
        for factor in factors:
            # Mask for rows strictly before the effective date
            mask = res_df.index < factor.effective_date

            for col in ['adj_open', 'adj_high', 'adj_low', 'adj_close']:
                if col in res_df.columns:
                    res_df.loc[mask, col] = res_df.loc[mask, col] * factor.factor

            if 'adj_volume' in res_df.columns:
                res_df.loc[mask, 'adj_volume'] = res_df.loc[mask, 'adj_volume'] / factor.factor

            res_df.loc[mask, 'cumulative_adjustment_factor'] = res_df.loc[mask, 'cumulative_adjustment_factor'] * factor.factor

        return res_df

    def calculate_factor(self, action: CorporateActionRecord, previous_close: Optional[float] = None) -> Optional[float]:
        if action.action_type == CorporateActionType.STOCK_SPLIT and action.ratio is not None:
            return 1.0 / (1.0 + action.ratio)
        elif action.action_type == CorporateActionType.STOCK_DIVIDEND and action.ratio is not None:
            return 1.0 / (1.0 + action.ratio)
        return 1.0

    def generate_adjusted_price_result(self, symbol: str, raw_df: pd.DataFrame, adjusted_df: pd.DataFrame, actions: List[CorporateActionRecord]) -> AdjustedPriceResult:
        return AdjustedPriceResult(
            result_id=str(uuid.uuid4()),
            symbol=symbol,
            direction=AdjustmentDirection.BACKWARD,
            raw_rows=len(raw_df),
            adjusted_rows=len(adjusted_df),
            actions_applied=len(actions)
        )
