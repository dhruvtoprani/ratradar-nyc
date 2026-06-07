#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.config import DEFAULT_START_DATE, NYC_311_ENDPOINT, RAW_DATA_DIR
from ratradar.data_sources import fetch_socrata_pages
from ratradar.utils import configure_logging, ensure_project_directories, write_table

LOGGER = logging.getLogger("fetch_311_rodent")
SELECT_COLUMNS = ",".join(
    [
        "unique_key",
        "created_date",
        "complaint_type",
        "descriptor",
        "incident_zip",
        "borough",
        "latitude",
        "longitude",
        "status",
        "resolution_description",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch rat-related NYC 311 requests")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument(
        "--output", type=Path, default=RAW_DATA_DIR / "311_rodent.parquet"
    )
    parser.add_argument("--page-size", type=int, default=25_000)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument(
        "--include-descriptor-matches",
        action="store_true",
        help="Also scan rat/mouse descriptor text; slower on large date ranges.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    load_dotenv()
    ensure_project_directories()

    rodent_filter = "complaint_type = 'Rodent'"
    if args.include_descriptor_matches:
        rodent_filter = (
            "(upper(complaint_type) = 'RODENT' "
            "OR upper(descriptor) like '%RAT%' "
            "OR upper(descriptor) like '%MOUSE%' "
            "OR upper(descriptor) like '%MICE%')"
        )
    where = f"created_date >= '{args.start_date}T00:00:00' AND {rodent_filter}"
    pages = fetch_socrata_pages(
        NYC_311_ENDPOINT,
        select=SELECT_COLUMNS,
        where=where,
        order="created_date ASC, unique_key ASC",
        app_token=os.getenv("NYC_OPEN_DATA_APP_TOKEN"),
        page_size=args.page_size,
        max_rows=args.max_rows,
    )
    records = [record for page in pages for record in page]
    if not records:
        raise SystemExit("The NYC Open Data query returned no rodent complaints")

    frame = pd.DataFrame.from_records(records)
    write_table(frame, args.output)
    dates = pd.to_datetime(frame["created_date"], errors="coerce")
    LOGGER.info("Saved %s rows to %s", f"{len(frame):,}", args.output)
    LOGGER.info(
        "Source date range: %s through %s",
        dates.min().date(),
        dates.max().date(),
    )


if __name__ == "__main__":
    main()
