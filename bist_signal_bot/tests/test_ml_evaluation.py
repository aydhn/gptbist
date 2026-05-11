import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.ml.training.evaluation import MLModelEvaluator

def test_evaluate_classification_binary():
    evaluator = MLModelEvaluator()
    y_true = pd.Series([0, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 1])
    y_proba = np.array([[0.8, 0.2], [0.1, 0.9], [0.4, 0.6], [0.2, 0.8]])

    metrics = evaluator.evaluate_classification(y_true, y_pred, y_proba)
    assert metrics.accuracy == 0.75
    assert metrics.roc_auc is not None

def test_evaluate_classification_single_class():
    evaluator = MLModelEvaluator()
    y_true = pd.Series([1, 1, 1, 1])
    y_pred = np.array([1, 1, 1, 1])

    metrics = evaluator.evaluate_classification(y_true, y_pred)
    assert metrics.accuracy == 1.0
    assert metrics.roc_auc is None

def test_evaluate_regression():
    evaluator = MLModelEvaluator()
    y_true = pd.Series([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 1.9, 3.2])

    metrics = evaluator.evaluate_regression(y_true, y_pred)
    assert metrics.mae is not None
    assert metrics.rmse is not None
    assert metrics.r2 is not None
