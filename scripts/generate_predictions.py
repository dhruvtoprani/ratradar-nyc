#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.config import MODELS_DIR, PREDICTIONS_DATA_DIR, PROCESSED_DATA_DIR
from ratradar.modeling import add_prediction_columns
from ratradar.utils import configure_logging, read_table, write_table

LOGGER = logging.getLogger("generate_predictions")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate RatRadar predictions")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROCESSED_DATA_DIR / "rodent_zip_week.parquet",
    )
    parser.add_argument("--model", type=Path, default=MODELS_DIR / "ratradar_xgb.pkl")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    frame = read_table(args.dataset)
    bundle = joblib.load(args.model)
    scored = add_prediction_columns(
        frame,
        bundle["pipeline"],
        threshold=float(bundle["decision_threshold"]),
    )
    scored["model_version"] = bundle["model_version"]
    write_table(scored, PREDICTIONS_DATA_DIR / "all_predictions.parquet")
    latest = scored.loc[scored["prediction_date"] == scored["prediction_date"].max()]
    write_table(latest, PREDICTIONS_DATA_DIR / "latest_predictions.parquet")
    LOGGER.info("Generated %s latest ZIP predictions", len(latest))


if __name__ == "__main__":
    main()
