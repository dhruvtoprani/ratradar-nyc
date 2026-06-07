#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ratradar.config import EXTERNAL_DATA_DIR, NYC_MODZCTA_ENDPOINT
from ratradar.geo import normalize_modzcta_geojson
from ratradar.utils import configure_logging, ensure_project_directories

LOGGER = logging.getLogger("fetch_zip_boundaries")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NYC MODZCTA GeoJSON")
    parser.add_argument(
        "--output", type=Path, default=EXTERNAL_DATA_DIR / "nyc_modzcta.geojson"
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    ensure_project_directories()
    response = requests.get(
        NYC_MODZCTA_ENDPOINT,
        params={"$limit": 500},
        timeout=90,
        headers={"User-Agent": "RatRadar-NYC/0.1"},
    )
    response.raise_for_status()
    payload = normalize_modzcta_geojson(response.json())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload))
    LOGGER.info(
        "Saved %s MODZCTA features to %s",
        len(payload.get("features", [])),
        args.output,
    )


if __name__ == "__main__":
    main()
