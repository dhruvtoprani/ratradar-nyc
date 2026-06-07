from __future__ import annotations

import pandas as pd

from ratradar.cleaning import clean_rodent_complaints, normalize_zip
from ratradar.features import aggregate_weekly_counts


def _raw_complaints() -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2025-01-06")
    for week in range(14):
        for complaint in range((week % 4) + 1):
            rows.append(
                {
                    "unique_key": f"{week}-{complaint}",
                    "created_date": start + pd.Timedelta(weeks=week, days=1),
                    "complaint_type": "Rodent",
                    "descriptor": "Rat Sighting",
                    "incident_zip": "10001",
                    "borough": "MANHATTAN",
                }
            )
    rows.append(
        {
            "unique_key": "incomplete-week",
            "created_date": start + pd.Timedelta(weeks=15),
            "complaint_type": "Rodent",
            "descriptor": "Rat Sighting",
            "incident_zip": "10001",
            "borough": "MANHATTAN",
        }
    )
    return pd.DataFrame(rows)


def test_normalize_zip_keeps_valid_nyc_zip() -> None:
    assert normalize_zip("10001-0001") == "10001"
    assert normalize_zip("11004") == "11004"
    assert normalize_zip("11001") is None
    assert normalize_zip("99999") is None


def test_clean_rodent_complaints_standardizes_fields() -> None:
    cleaned = clean_rodent_complaints(_raw_complaints())
    assert cleaned["zip_code"].eq("10001").all()
    assert cleaned["borough"].eq("Manhattan").all()
    assert cleaned["created_date"].notna().all()


def test_aggregate_weekly_counts_appends_scoring_week() -> None:
    cleaned = clean_rodent_complaints(_raw_complaints())
    weekly, last_complete_week = aggregate_weekly_counts(cleaned)
    assert weekly["prediction_date"].max() == last_complete_week + pd.Timedelta(days=7)
    assert (
        weekly.loc[weekly["prediction_date"].idxmax(), "observed_rodent_count"]
        != weekly.loc[weekly["prediction_date"].idxmax(), "observed_rodent_count"]
    )
