from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def _safe_score(function: Any, y_true: pd.Series, y_probability: np.ndarray) -> float:
    if y_true.nunique() < 2:
        return float("nan")
    return float(function(y_true, y_probability))


def choose_f1_threshold(y_true: pd.Series, y_probability: np.ndarray) -> float:
    thresholds = np.linspace(0.1, 0.9, 81)
    scores = [
        f1_score(y_true, y_probability >= threshold, zero_division=0)
        for threshold in thresholds
    ]
    return float(thresholds[int(np.argmax(scores))])


def weekly_top_k_precision(
    frame: pd.DataFrame,
    *,
    probability_column: str = "risk_probability",
    target_column: str = "target_surge",
    k: int = 10,
) -> float:
    weekly_scores = []
    for _, week in frame.groupby("prediction_date"):
        known = week.dropna(subset=[target_column]).nlargest(k, probability_column)
        if not known.empty:
            weekly_scores.append(float(known[target_column].mean()))
    return float(np.mean(weekly_scores)) if weekly_scores else float("nan")


def evaluate_probabilities(
    y_true: pd.Series,
    y_probability: np.ndarray,
    *,
    threshold: float,
    context: pd.DataFrame | None = None,
) -> dict[str, Any]:
    y_predicted = (y_probability >= threshold).astype(int)
    if y_true.nunique() >= 2:
        false_positive, true_positive, roc_thresholds = roc_curve(
            y_true, y_probability, drop_intermediate=True
        )
    else:
        false_positive = np.array([0.0, 1.0])
        true_positive = np.array([0.0, 1.0])
        roc_thresholds = np.array([float("inf"), 0.0])
    precision_curve, recall_curve, pr_thresholds = precision_recall_curve(
        y_true, y_probability
    )

    metrics: dict[str, Any] = {
        "roc_auc": _safe_score(roc_auc_score, y_true, y_probability),
        "pr_auc": _safe_score(average_precision_score, y_true, y_probability),
        "f1": float(f1_score(y_true, y_predicted, zero_division=0)),
        "precision": float(precision_score(y_true, y_predicted, zero_division=0)),
        "recall": float(recall_score(y_true, y_predicted, zero_division=0)),
        "positive_rate": float(y_true.mean()),
        "decision_threshold": float(threshold),
        "confusion_matrix": confusion_matrix(
            y_true, y_predicted, labels=[0, 1]
        ).tolist(),
        "roc_curve": {
            "false_positive_rate": false_positive.tolist(),
            "true_positive_rate": true_positive.tolist(),
            "thresholds": roc_thresholds.tolist(),
        },
        "precision_recall_curve": {
            "precision": precision_curve.tolist(),
            "recall": recall_curve.tolist(),
            "thresholds": pr_thresholds.tolist(),
        },
    }
    if context is not None:
        scored = context[["prediction_date", "target_surge"]].copy()
        scored["risk_probability"] = y_probability
        metrics["top_10_precision"] = weekly_top_k_precision(scored, k=10)
    return metrics
