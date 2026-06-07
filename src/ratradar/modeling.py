from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from ratradar.config import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    RANDOM_SEED,
    risk_tier,
)
from ratradar.evaluation import choose_f1_threshold, evaluate_probabilities


@dataclass
class TimeSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def chronological_split(
    frame: pd.DataFrame,
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> TimeSplit:
    known = frame.dropna(subset=["target_surge"]).copy()
    unique_dates = np.array(sorted(pd.to_datetime(known["prediction_date"]).unique()))
    if len(unique_dates) < 12:
        raise ValueError("At least 12 labeled prediction dates are required")

    train_end = max(1, int(len(unique_dates) * train_fraction))
    validation_end = max(
        train_end + 1,
        int(len(unique_dates) * (train_fraction + validation_fraction)),
    )
    validation_end = min(validation_end, len(unique_dates) - 1)

    train_dates = set(unique_dates[:train_end])
    validation_dates = set(unique_dates[train_end:validation_end])
    test_dates = set(unique_dates[validation_end:])

    return TimeSplit(
        train=known.loc[known["prediction_date"].isin(train_dates)].copy(),
        validation=known.loc[known["prediction_date"].isin(validation_dates)].copy(),
        test=known.loc[known["prediction_date"].isin(test_dates)].copy(),
    )


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_logistic_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "model",
                LogisticRegression(
                    max_iter=1_000,
                    class_weight="balanced",
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def build_xgboost_pipeline(scale_pos_weight: float = 1.0) -> Pipeline:
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "model",
                XGBClassifier(
                    n_estimators=450,
                    max_depth=4,
                    learning_rate=0.04,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    min_child_weight=3,
                    reg_lambda=1.5,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    scale_pos_weight=scale_pos_weight,
                    random_state=RANDOM_SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def _positive_class_weight(target: pd.Series) -> float:
    positives = int(target.sum())
    negatives = int(len(target) - positives)
    return float(negatives / positives) if positives else 1.0


def train_models(frame: pd.DataFrame) -> tuple[dict[str, Any], TimeSplit]:
    split = chronological_split(frame)
    train_x = split.train[MODEL_FEATURES]
    train_y = split.train["target_surge"].astype(int)
    validation_x = split.validation[MODEL_FEATURES]
    validation_y = split.validation["target_surge"].astype(int)
    test_x = split.test[MODEL_FEATURES]
    test_y = split.test["target_surge"].astype(int)

    logistic = build_logistic_pipeline()
    logistic.fit(train_x, train_y)
    logistic_validation = logistic.predict_proba(validation_x)[:, 1]
    logistic_threshold = choose_f1_threshold(validation_y, logistic_validation)
    logistic_test = logistic.predict_proba(test_x)[:, 1]

    xgboost = build_xgboost_pipeline(_positive_class_weight(train_y))
    xgboost.fit(train_x, train_y)
    xgboost_validation = xgboost.predict_proba(validation_x)[:, 1]
    xgboost_threshold = choose_f1_threshold(validation_y, xgboost_validation)
    xgboost_test = xgboost.predict_proba(test_x)[:, 1]

    artifacts = {
        "logistic_pipeline": logistic,
        "xgboost_pipeline": xgboost,
        "logistic_threshold": logistic_threshold,
        "xgboost_threshold": xgboost_threshold,
        "metrics": {
            "logistic_regression": evaluate_probabilities(
                test_y,
                logistic_test,
                threshold=logistic_threshold,
                context=split.test,
            ),
            "xgboost": evaluate_probabilities(
                test_y,
                xgboost_test,
                threshold=xgboost_threshold,
                context=split.test,
            ),
        },
    }
    return artifacts, split


def fit_final_xgboost(frame: pd.DataFrame) -> Pipeline:
    known = frame.dropna(subset=["target_surge"])
    target = known["target_surge"].astype(int)
    pipeline = build_xgboost_pipeline(_positive_class_weight(target))
    pipeline.fit(known[MODEL_FEATURES], target)
    return pipeline


def add_prediction_columns(
    frame: pd.DataFrame, pipeline: Pipeline, *, threshold: float
) -> pd.DataFrame:
    scored = frame.copy()
    scored["risk_probability"] = pipeline.predict_proba(scored[MODEL_FEATURES])[:, 1]
    scored["predicted_surge"] = (scored["risk_probability"] >= threshold).astype(int)
    scored["risk_tier"] = scored["risk_probability"].map(risk_tier)
    scored["top_driver"] = scored.apply(infer_top_driver, axis=1)
    scored["why_this_zip"] = scored.apply(explain_prediction, axis=1)
    return scored


def infer_top_driver(row: pd.Series) -> str:
    if row.get("rodent_velocity_7d_vs_30d", 0) > 0.25:
        return "Complaint velocity"
    if row.get("rodent_count_last_7d", 0) > row.get(
        "rodent_rolling_mean_8w", float("inf")
    ):
        return "Recent complaint momentum"
    if row.get("rodent_rolling_std_8w", 0) > row.get(
        "rodent_rolling_mean_8w", float("inf")
    ):
        return "Complaint volatility"
    if row.get("zip_baseline_rodent_rate", 0) >= 5:
        return "Persistent baseline risk"
    return "Seasonal pattern"


def explain_prediction(row: pd.Series) -> str:
    probability = float(row.get("risk_probability", 0))
    velocity = float(row.get("rodent_velocity_7d_vs_30d", 0))
    last_week = float(row.get("rodent_count_last_7d", 0))
    baseline = float(row.get("rodent_rolling_mean_8w", 0))
    direction = "above" if last_week >= baseline else "below"
    return (
        f"Risk is {risk_tier(probability).lower()} because recent complaint volume "
        f"is {direction} the eight-week baseline and short-term complaint velocity "
        f"is {velocity:+.0%} versus the recent monthly pace."
    )


def extract_feature_importance(pipeline: Pipeline) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    return (
        pd.DataFrame(
            {
                "feature": [
                    name.replace("numeric__", "").replace("categorical__", "")
                    for name in feature_names
                ],
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
