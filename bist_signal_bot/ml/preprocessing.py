import pandas as pd
import numpy as np
import logging
from bist_signal_bot.ml.models import PreprocessingConfig

logger = logging.getLogger(__name__)

class MLPreprocessor:
    def preprocess(self, data: pd.DataFrame, config: PreprocessingConfig, feature_cols: list[str], label_cols: list[str]) -> pd.DataFrame:
        df = data.copy()

        if config.remove_inf:
            df = self.remove_inf_values(df)

        if config.fill_method != "none":
            df = self.fill_missing(df, feature_cols, config.fill_method)

        if config.max_missing_feature_pct < 1.0:
            df, dropped_cols = self.drop_high_missing_features(df, feature_cols, config.max_missing_feature_pct)
            # update feature_cols internally to avoid issues downstream
            feature_cols = [c for c in feature_cols if c not in dropped_cols]

        if config.winsorize:
            df = self.winsorize_features(df, feature_cols, config.winsorize_lower_pct, config.winsorize_upper_pct)

        if config.standardize:
            logger.warning("Scaling applied globally on the entire dataset. This can cause leakage if not handled carefully during train/test splits. It is recommended to standardize during pipeline training.")
            df = self.standardize_features(df, feature_cols)

        if config.robust_scale:
            logger.warning("Robust Scaling applied globally on the entire dataset. This can cause leakage if not handled carefully during train/test splits.")
            df = self.robust_scale_features(df, feature_cols)

        if config.drop_na_labels and label_cols:
            df = df.dropna(subset=label_cols)

        if config.drop_na_features and feature_cols:
            df = df.dropna(subset=feature_cols)

        return df

    def remove_inf_values(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        return df

    def fill_missing(self, data: pd.DataFrame, feature_cols: list[str], method: str) -> pd.DataFrame:
        df = data.copy()
        if method == "ffill":
            df[feature_cols] = df[feature_cols].ffill()
        elif method == "bfill":
            df[feature_cols] = df[feature_cols].bfill()
        elif method == "zero":
            df[feature_cols] = df[feature_cols].fillna(0)
        elif method == "median":
            # Using transform to fill with median per column to avoid leakage from other symbols if this was a global median
            # But the requirement doesn't strictly dictate per symbol median, although it's better.
            # We'll just do global column median for simplicity as a basic baseline.
            df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median(numeric_only=True))
        return df

    def drop_high_missing_features(self, data: pd.DataFrame, feature_cols: list[str], max_missing_pct: float) -> tuple[pd.DataFrame, list[str]]:
        df = data.copy()
        missing_pcts = df[feature_cols].isna().mean()
        drop_cols = missing_pcts[missing_pcts > max_missing_pct].index.tolist()
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        return df, drop_cols

    def winsorize_features(self, data: pd.DataFrame, feature_cols: list[str], lower_pct: float, upper_pct: float) -> pd.DataFrame:
        df = data.copy()
        # pandas doesn't have an in-built winsorize, so we do it via clip
        for col in feature_cols:
            if df[col].dtype.kind in 'bifc':
                lower_val = df[col].quantile(lower_pct)
                upper_val = df[col].quantile(upper_pct)
                df[col] = df[col].clip(lower=lower_val, upper=upper_val)
        return df

    def standardize_features(self, data: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
        df = data.copy()
        for col in feature_cols:
            if df[col].dtype.kind in 'bifc':
                mean = df[col].mean()
                std = df[col].std()
                if std != 0 and not pd.isna(std):
                    df[col] = (df[col] - mean) / std
        return df

    def robust_scale_features(self, data: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
        df = data.copy()
        for col in feature_cols:
            if df[col].dtype.kind in 'bifc':
                median = df[col].median()
                q75, q25 = df[col].quantile(0.75), df[col].quantile(0.25)
                iqr = q75 - q25
                if iqr != 0 and not pd.isna(iqr):
                    df[col] = (df[col] - median) / iqr
        return df
