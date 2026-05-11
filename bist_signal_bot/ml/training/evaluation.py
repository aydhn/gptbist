import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from bist_signal_bot.ml.training.models import MLClassificationMetrics, MLRegressionMetrics
from bist_signal_bot.core.exceptions import MLEvaluationError

class MLModelEvaluator:
    def evaluate_classification(self, y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None = None) -> MLClassificationMetrics:
        try:
            acc = accuracy_score(y_true, y_pred)

            # handle multi-class vs binary for precision/recall/f1
            n_classes = len(np.unique(y_true))
            avg_method = 'binary' if n_classes <= 2 else 'weighted'

            # prevent ValueError if binary but targets aren't exactly [0, 1] - let sklearn handle or fallback
            if n_classes <= 2 and not set(np.unique(y_true)).issubset({0, 1}):
                avg_method = 'weighted'

            prec = precision_score(y_true, y_pred, average=avg_method, zero_division=0)
            rec = recall_score(y_true, y_pred, average=avg_method, zero_division=0)
            f1 = f1_score(y_true, y_pred, average=avg_method, zero_division=0)

            cm = confusion_matrix(y_true, y_pred).tolist()

            roc_auc = None
            avg_prec = None
            if y_proba is not None and n_classes == 2:
                try:
                    # assume positive class is column 1
                    roc_auc = roc_auc_score(y_true, y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba)
                    avg_prec = average_precision_score(y_true, y_proba[:, 1] if len(y_proba.shape) > 1 else y_proba)
                except Exception:
                    pass

            train_dist = {} # can't do here, done in trainer
            test_dist = y_true.value_counts().to_dict()

            return MLClassificationMetrics(
                accuracy=acc,
                precision=prec,
                recall=rec,
                f1=f1,
                roc_auc=roc_auc,
                average_precision=avg_prec,
                confusion_matrix=cm,
                class_distribution_test={str(k): int(v) for k, v in test_dist.items()}
            )
        except Exception as e:
            raise MLEvaluationError(f"Failed to evaluate classification: {e}")

    def evaluate_regression(self, y_true: pd.Series, y_pred: np.ndarray) -> MLRegressionMetrics:
        try:
            mae = mean_absolute_error(y_true, y_pred)
            mse = mean_squared_error(y_true, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true, y_pred)

            # directional accuracy (did it predict the correct sign of the return?)
            dir_acc = None
            if len(y_true) > 0:
                correct_dir = (np.sign(y_true) == np.sign(y_pred)).sum()
                dir_acc = correct_dir / len(y_true)

            return MLRegressionMetrics(
                mae=mae,
                mse=mse,
                rmse=rmse,
                r2=r2,
                directional_accuracy=dir_acc,
                prediction_mean=float(np.mean(y_pred)),
                target_mean=float(np.mean(y_true))
            )
        except Exception as e:
            raise MLEvaluationError(f"Failed to evaluate regression: {e}")
