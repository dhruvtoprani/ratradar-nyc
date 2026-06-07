from __future__ import annotations

import pandas as pd

from ratradar.cleaning import clean_rodent_complaints
from ratradar.targets import build_modeling_table


def _single_zip_complaints() -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2024-01-01")
    weekly_counts = [1, 3, 5, 7, 9, 11, 13, 15, 30, 1, 1, 1]
    for week, count in enumerate(weekly_counts):
        for complaint in range(count):
            rows.append(
                {
                    "unique_key": f"{week}-{complaint}",
                    "created_date": start + pd.Timedelta(weeks=week, days=1),
                    "complaint_type": "Rodent",
                    "descriptor": "Rat Sighting",
                    "incident_zip": "11221",
                    "borough": "BROOKLYN",
                }
            )
    rows.append(
        {
            "unique_key": "incomplete",
            "created_date": start + pd.Timedelta(weeks=14),
            "complaint_type": "Rodent",
            "descriptor": "Rat Sighting",
            "incident_zip": "11221",
            "borough": "BROOKLYN",
        }
    )
    return pd.DataFrame(rows)


def test_features_use_prior_week_not_target_week() -> None:
    table = build_modeling_table(
        clean_rodent_complaints(_single_zip_complaints()), min_history_weeks=4
    ).sort_values("prediction_date")
    labeled = table.loc[table["target_surge"].notna()].copy()
    row = labeled.iloc[3]
    previous = table.loc[
        table["prediction_date"] == row["prediction_date"] - pd.Timedelta(days=7)
    ].iloc[0]
    assert row["rodent_count_last_7d"] == previous["future_rodent_count_7d"]
    assert row["rodent_count_last_7d"] != row["future_rodent_count_7d"]


def test_threshold_uses_only_prior_history() -> None:
    table = build_modeling_table(
        clean_rodent_complaints(_single_zip_complaints()), min_history_weeks=4
    ).sort_values("prediction_date")
    row = table.loc[table["surge_threshold"].notna()].iloc[0]
    prior_counts = table.loc[
        table["prediction_date"] < row["prediction_date"], "future_rodent_count_7d"
    ].dropna()
    assert row["surge_threshold"] == max(1, prior_counts.quantile(0.75))
