from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


def fetch_socrata_pages(
    endpoint: str,
    *,
    select: str,
    where: str,
    order: str,
    app_token: str | None = None,
    page_size: int = 25_000,
    max_rows: int | None = None,
    timeout: int = 90,
) -> Iterator[list[dict[str, Any]]]:
    session = requests.Session()
    session.headers.update({"User-Agent": "RatRadar-NYC/0.1"})
    if app_token:
        session.headers.update({"X-App-Token": app_token})

    offset = 0
    while True:
        remaining = None if max_rows is None else max_rows - offset
        if remaining is not None and remaining <= 0:
            return
        limit = page_size if remaining is None else min(page_size, remaining)
        params = {
            "$select": select,
            "$where": where,
            "$order": order,
            "$limit": limit,
            "$offset": offset,
        }

        for attempt in range(1, 5):
            try:
                response = session.get(endpoint, params=params, timeout=timeout)
                response.raise_for_status()
                page = response.json()
                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                sleep_seconds = 2**attempt
                LOGGER.warning(
                    "Socrata request failed; retrying in %s seconds", sleep_seconds
                )
                time.sleep(sleep_seconds)

        if not page:
            return

        yield page
        offset += len(page)
        LOGGER.info("Fetched %s rows", f"{offset:,}")
        if len(page) < limit:
            return
