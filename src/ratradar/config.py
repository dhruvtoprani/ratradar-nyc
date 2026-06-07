from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
PREDICTIONS_DATA_DIR = DATA_DIR / "predictions"
MODELS_DIR = PROJECT_ROOT / "models"

NYC_311_DATASET_ID = "erm2-nwe9"
NYC_311_ENDPOINT = f"https://data.cityofnewyork.us/resource/{NYC_311_DATASET_ID}.json"
NYC_MODZCTA_ENDPOINT = "https://data.cityofnewyork.us/resource/pri4-ifjk.geojson"

DEFAULT_START_DATE = os.getenv("RATRADAR_START_DATE", "2020-01-01")
MIN_HISTORY_WEEKS = int(os.getenv("RATRADAR_MIN_HISTORY_WEEKS", "8"))
RANDOM_SEED = int(os.getenv("RATRADAR_RANDOM_SEED", "42"))

NUMERIC_FEATURES = [
    "rodent_count_last_7d",
    "rodent_count_last_14d",
    "rodent_count_last_30d",
    "rodent_count_last_60d",
    "rodent_count_last_90d",
    "rodent_rolling_mean_4w",
    "rodent_rolling_mean_8w",
    "rodent_rolling_std_8w",
    "rodent_velocity_7d_vs_30d",
    "rodent_velocity_14d_vs_60d",
    "days_since_last_rodent_complaint",
    "zip_baseline_rodent_rate",
    "week_of_year",
    "month",
    "quarter",
    "year",
    "is_summer",
    "is_winter",
]
CATEGORICAL_FEATURES = ["borough"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

RISK_COLORS = {
    "Low": "#765ad6",
    "Watch": "#d8ff4f",
    "Elevated": "#ffce69",
    "High": "#ff8a64",
    "Critical": "#ff4f6d",
}


def risk_tier(probability: float) -> str:
    if probability < 0.2:
        return "Low"
    if probability < 0.4:
        return "Watch"
    if probability < 0.6:
        return "Elevated"
    if probability < 0.8:
        return "High"
    return "Critical"
