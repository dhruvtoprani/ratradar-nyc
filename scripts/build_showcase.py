#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ratradar.config import EXTERNAL_DATA_DIR, MODELS_DIR, PREDICTIONS_DATA_DIR
from ratradar.utils import load_json, read_table, write_json

WEB_DIR = PROJECT_ROOT / "web"
WEB_DATA_DIR = WEB_DIR / "data"


def downsample(values: list[float], target_points: int = 180) -> list[float]:
    if len(values) <= target_points:
        return values
    indexes = pd.Series(range(len(values))).iloc[
        :: max(1, len(values) // target_points)
    ]
    return [values[index] for index in indexes]


def compact_metrics(metrics: dict) -> dict:
    compact = {
        "model_version": metrics["model_version"],
        "trained_at": metrics["trained_at"],
        "target_definition": metrics["target_definition"],
        "data_through_date": metrics["data_through_date"],
        "latest_prediction_date": metrics["latest_prediction_date"],
        "zip_count": metrics["zip_count"],
        "row_count": metrics["row_count"],
        "split_dates": metrics["split_dates"],
        "models": {},
    }
    for model_name, model_metrics in metrics["models"].items():
        roc = model_metrics["roc_curve"]
        precision_recall = model_metrics["precision_recall_curve"]
        compact["models"][model_name] = {
            key: model_metrics[key]
            for key in (
                "roc_auc",
                "pr_auc",
                "f1",
                "precision",
                "recall",
                "positive_rate",
                "decision_threshold",
                "top_10_precision",
                "confusion_matrix",
            )
        }
        compact["models"][model_name]["roc_curve"] = {
            "false_positive_rate": downsample(roc["false_positive_rate"]),
            "true_positive_rate": downsample(roc["true_positive_rate"]),
        }
        compact["models"][model_name]["precision_recall_curve"] = {
            "precision": downsample(precision_recall["precision"]),
            "recall": downsample(precision_recall["recall"]),
        }
    return compact


def records(frame: pd.DataFrame) -> list[dict]:
    normalized = frame.copy()
    for column in normalized.columns:
        if pd.api.types.is_datetime64_any_dtype(normalized[column]):
            normalized[column] = normalized[column].dt.strftime("%Y-%m-%d")
    return json.loads(normalized.to_json(orient="records"))


def main() -> None:
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    latest = read_table(PREDICTIONS_DATA_DIR / "latest_predictions.parquet")
    history = read_table(PREDICTIONS_DATA_DIR / "all_predictions.parquet")
    importance = read_table(MODELS_DIR / "feature_importance.parquet")
    metrics = load_json(MODELS_DIR / "metrics.json")

    latest_columns = [
        "prediction_date",
        "zip_code",
        "borough",
        "risk_probability",
        "risk_tier",
        "top_driver",
        "why_this_zip",
        "rodent_count_last_7d",
        "rodent_count_last_30d",
        "rodent_count_last_90d",
        "rodent_rolling_mean_8w",
        "rodent_rolling_std_8w",
        "rodent_velocity_7d_vs_30d",
        "zip_baseline_rodent_rate",
        "days_since_last_rodent_complaint",
    ]
    history_columns = [
        "prediction_date",
        "zip_code",
        "risk_probability",
        "future_rodent_count_7d",
        "rodent_rolling_mean_8w",
    ]

    write_json({"rows": records(latest[latest_columns])}, WEB_DATA_DIR / "latest.json")
    write_json(
        {"rows": records(history[history_columns])},
        WEB_DATA_DIR / "history.json",
    )
    write_json(
        compact_metrics(metrics),
        WEB_DATA_DIR / "metrics.json",
    )
    write_json(
        {"rows": records(importance.head(20))},
        WEB_DATA_DIR / "importance.json",
    )
    shutil.copy2(
        EXTERNAL_DATA_DIR / "nyc_modzcta.geojson",
        WEB_DATA_DIR / "nyc_modzcta.geojson",
    )
    print(f"Built static showcase data in {WEB_DATA_DIR}")


if __name__ == "__main__":
    main()
