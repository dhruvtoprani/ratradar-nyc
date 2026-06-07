#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.cleaning import clean_rodent_complaints
from ratradar.config import (
    EXTERNAL_DATA_DIR,
    INTERIM_DATA_DIR,
    MIN_HISTORY_WEEKS,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)
from ratradar.targets import build_modeling_table
from ratradar.utils import (
    configure_logging,
    ensure_project_directories,
    read_table,
    write_table,
)

LOGGER = logging.getLogger("build_dataset")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RatRadar ZIP-week dataset")
    parser.add_argument(
        "--input", type=Path, default=RAW_DATA_DIR / "311_rodent.parquet"
    )
    parser.add_argument(
        "--clean-output",
        type=Path,
        default=INTERIM_DATA_DIR / "311_rodent_clean.parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_DATA_DIR / "rodent_zip_week.parquet",
    )
    parser.add_argument(
        "--boundaries",
        type=Path,
        default=EXTERNAL_DATA_DIR / "nyc_modzcta.geojson",
        help="Optional MODZCTA GeoJSON used to keep only mappable ZIP codes.",
    )
    parser.add_argument("--quantile", type=float, default=0.75)
    parser.add_argument("--min-history-weeks", type=int, default=MIN_HISTORY_WEEKS)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    ensure_project_directories()
    raw = read_table(args.input)
    cleaned = clean_rodent_complaints(raw)
    if args.boundaries.exists():
        payload = json.loads(args.boundaries.read_text())
        valid_zip_codes = {
            str(feature.get("properties", {}).get("zip_code", "")).zfill(5)
            for feature in payload.get("features", [])
        }
        cleaned = cleaned.loc[cleaned["zip_code"].isin(valid_zip_codes)].copy()
    write_table(cleaned, args.clean_output)
    modeled = build_modeling_table(
        cleaned,
        quantile=args.quantile,
        min_history_weeks=args.min_history_weeks,
    )
    write_table(modeled, args.output)
    labeled = modeled["target_surge"].notna()
    LOGGER.info("Cleaned %s rodent complaints", f"{len(cleaned):,}")
    LOGGER.info(
        "Built %s ZIP-week rows across %s ZIP codes",
        f"{len(modeled):,}",
        modeled["zip_code"].nunique(),
    )
    LOGGER.info(
        "Labeled rows: %s | surge rate: %.1f%%",
        f"{labeled.sum():,}",
        100 * modeled.loc[labeled, "target_surge"].mean(),
    )
    LOGGER.info("Latest prediction date: %s", modeled["prediction_date"].max().date())
    LOGGER.info("Saved modeling table to %s", args.output)


if __name__ == "__main__":
    main()
