#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.config import (
    MODEL_FEATURES,
    MODELS_DIR,
    PREDICTIONS_DATA_DIR,
    PROCESSED_DATA_DIR,
)
from ratradar.explainability import compute_shap_values
from ratradar.modeling import (
    add_prediction_columns,
    extract_feature_importance,
    fit_final_xgboost,
    train_models,
)
from ratradar.utils import (
    configure_logging,
    ensure_project_directories,
    read_table,
    write_json,
    write_table,
)

LOGGER = logging.getLogger("train_model")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RatRadar baseline models")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROCESSED_DATA_DIR / "rodent_zip_week.parquet",
    )
    parser.add_argument("--with-shap", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    ensure_project_directories()
    frame = read_table(args.dataset)
    frame["prediction_date"] = frame["prediction_date"].astype("datetime64[ns]")

    evaluated, split = train_models(frame)
    final_pipeline = fit_final_xgboost(frame)
    threshold = float(evaluated["xgboost_threshold"])
    model_version = datetime.now(UTC).strftime("%Y.%m.%d-%H%M")

    scored = add_prediction_columns(frame, final_pipeline, threshold=threshold)
    split_lookup = {}
    for split_name, split_frame in (
        ("train", split.train),
        ("validation", split.validation),
        ("test", split.test),
    ):
        split_lookup.update(
            {
                (str(row.zip_code), row.prediction_date): split_name
                for row in split_frame.itertuples()
            }
        )
    scored["split"] = [
        split_lookup.get((str(row.zip_code), row.prediction_date), "scoring")
        for row in scored.itertuples()
    ]
    scored["model_version"] = model_version

    bundle = {
        "pipeline": final_pipeline,
        "decision_threshold": threshold,
        "feature_columns": MODEL_FEATURES,
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
    }
    joblib.dump(bundle, MODELS_DIR / "ratradar_xgb.pkl")

    metrics = {
        "model_version": model_version,
        "trained_at": bundle["trained_at"],
        "target_definition": "ZIP past-only expanding 75th percentile",
        "data_through_date": str(frame["data_through_date"].max()),
        "latest_prediction_date": str(frame["prediction_date"].max()),
        "zip_count": int(frame["zip_code"].nunique()),
        "row_count": int(len(frame)),
        "split_dates": {
            "train": {
                "start": str(split.train["prediction_date"].min().date()),
                "end": str(split.train["prediction_date"].max().date()),
            },
            "validation": {
                "start": str(split.validation["prediction_date"].min().date()),
                "end": str(split.validation["prediction_date"].max().date()),
            },
            "test": {
                "start": str(split.test["prediction_date"].min().date()),
                "end": str(split.test["prediction_date"].max().date()),
            },
        },
        "models": evaluated["metrics"],
    }
    write_json(metrics, MODELS_DIR / "metrics.json")
    write_json({"features": MODEL_FEATURES}, MODELS_DIR / "feature_columns.json")

    importance = extract_feature_importance(final_pipeline)
    write_table(importance, MODELS_DIR / "feature_importance.parquet")
    write_table(scored, PREDICTIONS_DATA_DIR / "all_predictions.parquet")
    latest = scored.loc[
        scored["prediction_date"] == scored["prediction_date"].max()
    ].copy()
    write_table(latest, PREDICTIONS_DATA_DIR / "latest_predictions.parquet")

    if args.with_shap:
        known = frame.dropna(subset=["target_surge"])
        shap_values = compute_shap_values(final_pipeline, known[MODEL_FEATURES])
        write_table(shap_values, MODELS_DIR / "shap_values.parquet")

    xgb_metrics = metrics["models"]["xgboost"]
    LOGGER.info("Saved model version %s", model_version)
    LOGGER.info(
        "Test ROC-AUC %.3f | PR-AUC %.3f | top-10 precision %.3f",
        xgb_metrics["roc_auc"],
        xgb_metrics["pr_auc"],
        xgb_metrics["top_10_precision"],
    )
    LOGGER.info("Latest predictions: %s rows", len(latest))


if __name__ == "__main__":
    main()
