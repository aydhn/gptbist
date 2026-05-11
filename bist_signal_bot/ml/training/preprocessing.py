from typing import Any
import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from bist_signal_bot.ml.training.models import MLScalerType, MLImputerType
from bist_signal_bot.core.exceptions import MLTrainingValidationError

logger = logging.getLogger(__name__)

class MLTrainingPreprocessor:
    def __init__(self, scaler: MLScalerType = MLScalerType.NONE, imputer: MLImputerType = MLImputerType.MEDIAN):
        self.scaler_type = scaler
        self.imputer_type = imputer
        self._scaler = None
        self._imputer = None
        self._feature_cols = None
        self._is_fitted = False

        if self.imputer_type == MLImputerType.MEDIAN:
            self._imputer = SimpleImputer(strategy="median")
        elif self.imputer_type == MLImputerType.MEAN:
            self._imputer = SimpleImputer(strategy="mean")
        elif self.imputer_type == MLImputerType.ZERO:
            self._imputer = SimpleImputer(strategy="constant", fill_value=0.0)

        if self.scaler_type == MLScalerType.STANDARD:
            self._scaler = StandardScaler()
        elif self.scaler_type == MLScalerType.ROBUST:
            self._scaler = RobustScaler()
        elif self.scaler_type == MLScalerType.MINMAX:
            self._scaler = MinMaxScaler()

    def _prepare_numeric(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric = [c for c in df.columns if c not in numeric_cols]
        if non_numeric:
            logger.warning(f"Dropping non-numeric columns from features: {non_numeric}")
            df = df.drop(columns=non_numeric)
        return df

    def fit_transform_train(self, X_train: pd.DataFrame) -> pd.DataFrame:
        self.fit(X_train)
        return self.transform(X_train)

    def transform_test(self, X_test: pd.DataFrame) -> pd.DataFrame:
        return self.transform(X_test)

    def transform_live(self, X: pd.DataFrame) -> pd.DataFrame:
        return self.transform(X)

    def fit(self, X_train: pd.DataFrame) -> None:
        X_num = self._prepare_numeric(X_train)
        self._feature_cols = X_num.columns.tolist()

        if self._imputer is not None:
            X_num = pd.DataFrame(self._imputer.fit_transform(X_num), columns=self._feature_cols, index=X_num.index)

        if self._scaler is not None:
            self._scaler.fit(X_num)

        self._is_fitted = True

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self._is_fitted:
            raise MLTrainingValidationError("Preprocessor is not fitted")

        missing = [c for c in self._feature_cols if c not in X.columns]
        if missing:
            raise MLTrainingValidationError(f"Missing columns during transform: {missing}")

        df = X[self._feature_cols].copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        if self._imputer is not None:
            arr = self._imputer.transform(df)
            df = pd.DataFrame(arr, columns=self._feature_cols, index=df.index)

        if self._scaler is not None:
            arr = self._scaler.transform(df)
            df = pd.DataFrame(arr, columns=self._feature_cols, index=df.index)

        return df

    def get_pipeline(self) -> Any:
        return {
            "scaler_type": self.scaler_type.value,
            "imputer_type": self.imputer_type.value,
            "scaler": self._scaler,
            "imputer": self._imputer,
            "feature_cols": self._feature_cols,
            "is_fitted": self._is_fitted
        }
