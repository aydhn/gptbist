import pandas as pd
import numpy as np
import logging
from bist_signal_bot.ml.models import LabelConfig, LabelType
from bist_signal_bot.config.settings import Settings

logger = logging.getLogger(__name__)

class LabelBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def add_labels(self, data: pd.DataFrame, config: LabelConfig, price_col: str = "close") -> pd.DataFrame:
        df = data.copy()
        horizon = config.horizon_bars

        # Calculate forward return
        fwd_ret = self.forward_return(df, horizon, price_col)
        df[fwd_ret.name] = fwd_ret

        if config.label_type == LabelType.FORWARD_RETURN:
            pass # already added

        elif config.label_type == LabelType.BINARY_DIRECTION:
            lbl = self.binary_direction_label(fwd_ret, config.positive_threshold)
            df[lbl.name] = lbl

        elif config.label_type == LabelType.MULTICLASS_DIRECTION:
            lbl = self.multiclass_direction_label(fwd_ret, config.positive_threshold, config.negative_threshold)
            df[lbl.name] = lbl

        elif config.label_type == LabelType.THRESHOLD_EVENT:
            lbl = self.threshold_event_label(fwd_ret, config.positive_threshold, config.negative_threshold)
            df[lbl.name] = lbl

        elif config.label_type == LabelType.VOLATILITY_ADJUSTED_RETURN:
            lbl = self.volatility_adjusted_return(df, fwd_ret)
            df[lbl.name] = lbl

        elif config.label_type == LabelType.RISK_ADJUSTED_RETURN:
            lbl = self.risk_adjusted_return(df, fwd_ret)
            df[lbl.name] = lbl

        return df

    def forward_return(self, data: pd.DataFrame, horizon_bars: int, price_col: str = "close") -> pd.Series:
        shifted = data[price_col].shift(-horizon_bars)
        fwd_ret = (shifted / data[price_col]) - 1
        fwd_ret.name = f"label_fwd_return_{horizon_bars}"
        return fwd_ret

    def binary_direction_label(self, forward_return: pd.Series, positive_threshold: float) -> pd.Series:
        name = forward_return.name.replace("label_fwd_return", "label_direction_binary")
        lbl = pd.Series(0, index=forward_return.index, name=name)
        lbl[forward_return > positive_threshold] = 1
        lbl[forward_return.isna()] = np.nan
        return lbl

    def multiclass_direction_label(self, forward_return: pd.Series, positive_threshold: float, negative_threshold: float) -> pd.Series:
        name = forward_return.name.replace("label_fwd_return", "label_direction_3class")
        lbl = pd.Series(0, index=forward_return.index, name=name)
        lbl[forward_return > positive_threshold] = 1
        lbl[forward_return < negative_threshold] = -1
        lbl[forward_return.isna()] = np.nan
        return lbl

    def threshold_event_label(self, forward_return: pd.Series, positive_threshold: float, negative_threshold: float) -> pd.Series:
        name = forward_return.name.replace("label_fwd_return", "label_threshold_event")
        lbl = pd.Series(0, index=forward_return.index, name=name)
        lbl[(forward_return > positive_threshold) | (forward_return < negative_threshold)] = 1
        lbl[forward_return.isna()] = np.nan
        return lbl

    def volatility_adjusted_return(self, data: pd.DataFrame, forward_return: pd.Series) -> pd.Series:
        name = forward_return.name.replace("label_fwd_return", "label_vol_adj_return")

        # Try to find a volatility feature
        vol_cols = [c for c in data.columns if "volatility" in c.lower() or "atr_pct" in c.lower()]

        if vol_cols:
            vol_col = vol_cols[0]
            # avoid division by zero
            safe_vol = data[vol_col].replace(0, np.nan)
            lbl = forward_return / safe_vol
        else:
            logger.warning("No volatility feature found for volatility_adjusted_return. Using unadjusted forward return.")
            lbl = forward_return.copy()

        lbl.name = name
        return lbl

    def risk_adjusted_return(self, data: pd.DataFrame, forward_return: pd.Series) -> pd.Series:
        name = forward_return.name.replace("label_fwd_return", "label_risk_adj_return")
        logger.warning("risk_adjusted_return uses unadjusted forward return as placeholder.")
        lbl = forward_return.copy()
        lbl.name = name
        return lbl

    def label_columns_for_config(self, config: LabelConfig) -> list[str]:
        horizon = config.horizon_bars
        cols = [f"label_fwd_return_{horizon}"]

        if config.label_type == LabelType.BINARY_DIRECTION:
            cols.append(f"label_direction_binary_{horizon}")
        elif config.label_type == LabelType.MULTICLASS_DIRECTION:
            cols.append(f"label_direction_3class_{horizon}")
        elif config.label_type == LabelType.THRESHOLD_EVENT:
            cols.append(f"label_threshold_event_{horizon}")
        elif config.label_type == LabelType.VOLATILITY_ADJUSTED_RETURN:
            cols.append(f"label_vol_adj_return_{horizon}")
        elif config.label_type == LabelType.RISK_ADJUSTED_RETURN:
            cols.append(f"label_risk_adj_return_{horizon}")

        return cols
