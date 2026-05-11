from enum import Enum
from typing import Any
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field
from bist_signal_bot.ml.models import MLTaskType, MLDatasetResult, MLDatasetSchema, LabelType, FeatureConfig, LabelConfig, PreprocessingConfig, MLDatasetRequest

class MLModelType(str, Enum):
    LOGISTIC_REGRESSION = "LOGISTIC_REGRESSION"
    RANDOM_FOREST_CLASSIFIER = "RANDOM_FOREST_CLASSIFIER"
    GRADIENT_BOOSTING_CLASSIFIER = "GRADIENT_BOOSTING_CLASSIFIER"
    EXTRA_TREES_CLASSIFIER = "EXTRA_TREES_CLASSIFIER"
    DUMMY_CLASSIFIER = "DUMMY_CLASSIFIER"
    RIDGE_REGRESSION = "RIDGE_REGRESSION"
    RANDOM_FOREST_REGRESSOR = "RANDOM_FOREST_REGRESSOR"
    GRADIENT_BOOSTING_REGRESSOR = "GRADIENT_BOOSTING_REGRESSOR"
    EXTRA_TREES_REGRESSOR = "EXTRA_TREES_REGRESSOR"
    DUMMY_REGRESSOR = "DUMMY_REGRESSOR"

class MLTrainStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class MLPredictionType(str, Enum):
    CLASS_PROBABILITY = "CLASS_PROBABILITY"
    CLASS_LABEL = "CLASS_LABEL"
    REGRESSION_VALUE = "REGRESSION_VALUE"
    SCORE = "SCORE"
    UNKNOWN = "UNKNOWN"

class MLScalerType(str, Enum):
    NONE = "NONE"
    STANDARD = "STANDARD"
    ROBUST = "ROBUST"
    MINMAX = "MINMAX"

class MLImputerType(str, Enum):
    NONE = "NONE"
    MEDIAN = "MEDIAN"
    MEAN = "MEAN"
    ZERO = "ZERO"

class MLFeatureImportanceType(str, Enum):
    MODEL_NATIVE = "MODEL_NATIVE"
    PERMUTATION = "PERMUTATION"
    COEFFICIENT = "COEFFICIENT"
    NONE = "NONE"

class MLTrainConfig(BaseModel):
    model_type: MLModelType
    task_type: MLTaskType
    target_col: str
    feature_cols: list[str] | None = None
    scaler: MLScalerType = MLScalerType.NONE
    imputer: MLImputerType = MLImputerType.MEDIAN
    train_ratio: float = Field(ge=0.0, le=1.0, default=0.7)
    random_seed: int = 42
    test_mode: str = "time_series"
    class_weight: str | None = None
    max_train_rows: int | None = Field(ge=0, default=None)
    model_params: dict[str, Any] = Field(default_factory=dict)
    save_model: bool = True
    save_report: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def validate_config(self):
        if not self.target_col:
            raise ValueError("target_col cannot be empty")
        # simple compat check
        if self.task_type == MLTaskType.CLASSIFICATION:
            if "REGRESSOR" in self.model_type.value or "REGRESSION" in self.model_type.value and "LOGISTIC" not in self.model_type.value:
                raise ValueError(f"Model type {self.model_type} not compatible with task {self.task_type}")
        elif self.task_type == MLTaskType.REGRESSION:
            if "CLASSIFIER" in self.model_type.value or "LOGISTIC" in self.model_type.value:
                raise ValueError(f"Model type {self.model_type} not compatible with task {self.task_type}")
        return self

class MLTrainInput(BaseModel):
    dataset_path: str | None = None
    dataset_result: MLDatasetResult | None = None
    data: Any | None = None # pd.DataFrame
    schema_: MLDatasetSchema | None = None
    config: MLTrainConfig
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def validate_input(self):
        if not self.dataset_path and self.dataset_result is None and self.data is None:
            raise ValueError("At least one of dataset_path, dataset_result, or data must be provided")
        return self

class MLPreparedData(BaseModel):
    X_train: Any # pd.DataFrame
    X_test: Any # pd.DataFrame
    y_train: Any # pd.Series
    y_test: Any # pd.Series
    feature_cols: list[str]
    target_col: str
    train_index: Any # pd.Index
    test_index: Any # pd.Index
    preprocessor: Any
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

class MLClassificationMetrics(BaseModel):
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    average_precision: float | None = None
    confusion_matrix: list[list[int]] = Field(default_factory=list)
    class_distribution_train: dict[str, int] = Field(default_factory=dict)
    class_distribution_test: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLRegressionMetrics(BaseModel):
    mae: float | None = None
    mse: float | None = None
    rmse: float | None = None
    r2: float | None = None
    directional_accuracy: float | None = None
    prediction_mean: float | None = None
    target_mean: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLFeatureImportance(BaseModel):
    feature: str
    importance: float
    importance_type: MLFeatureImportanceType
    rank: int
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLModelArtifact(BaseModel):
    model_id: str
    model_type: MLModelType
    task_type: MLTaskType
    target_col: str
    feature_cols: list[str]
    model_path: str
    metadata_path: str
    report_path: str | None = None
    created_at: datetime
    train_rows: int
    test_rows: int
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    feature_importance_top: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = "ML model research artifact only. Predictions are not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLTrainResult(BaseModel):
    status: MLTrainStatus
    config: MLTrainConfig
    artifact: MLModelArtifact | None = None
    classification_metrics: MLClassificationMetrics | None = None
    regression_metrics: MLRegressionMetrics | None = None
    feature_importance: list[MLFeatureImportance] = Field(default_factory=list)
    prepared_data_summary: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float = 0.0
    disclaimer: str = "ML model research artifact only. Predictions are not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "model_type": self.config.model_type.value,
            "task_type": self.config.task_type.value,
            "target_col": self.config.target_col,
            "train_rows": self.prepared_data_summary.get("train_rows", 0),
            "test_rows": self.prepared_data_summary.get("test_rows", 0),
            "metrics": self.artifact.metrics_summary if self.artifact else {},
            "issues": self.issues,
            "elapsed_seconds": self.elapsed_seconds
        }

class MLPredictionRequest(BaseModel):
    model_id: str | None = None
    model_path: str | None = None
    symbols: list[str] = Field(default_factory=list)
    source: str = "mock"
    timeframe: str = "1d"
    rows: int | None = None
    dataset_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLPredictionItem(BaseModel):
    symbol: str
    timestamp: datetime | None = None
    prediction_type: MLPredictionType
    predicted_value: float | int | str | None = None
    probability_positive: float | None = None
    probability_negative: float | None = None
    probability_neutral: float | None = None
    raw_prediction: Any | None = None
    feature_snapshot: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MLPredictionResult(BaseModel):
    model_id: str
    predictions: list[MLPredictionItem]
    row_count: int
    generated_at: datetime
    elapsed_seconds: float = 0.0
    issues: list[str] = Field(default_factory=list)
    disclaimer: str = "ML prediction research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "prediction_count": len(self.predictions),
            "row_count": self.row_count,
            "generated_at": self.generated_at.isoformat(),
            "elapsed_seconds": self.elapsed_seconds,
            "issues": self.issues,
            "disclaimer": self.disclaimer
        }
