from __future__ import annotations

import pandas as pd

from ratradar.cleaning import clean_rodent_complaints
from ratradar.targets import build_modeling_table


def _complaints() -> pd.DataFrame:
    rows = []
    start = pd.Timestamp("2024-01-01")
    weekly_counts = [1, 1, 2, 1, 3, 2, 1, 4, 2, 5, 1, 6, 2, 7, 1, 8, 2]
    for week, count in enumerate(weekly_counts):
        for complaint in range(count):
            rows.append(
                {
                    "unique_key": f"10001-{week}-{complaint}",
                    "created_date": start + pd.Timedelta(weeks=week, days=1),
                    "complaint_type": "Rodent",
                    "descriptor": "Rat Sighting",
                    "incident_zip": "10001",
                    "borough": "MANHATTAN",
                }
            )
    rows.append(
        {
            "unique_key": "force-incomplete-week",
            "created_date": start + pd.Timedelta(weeks=19),
            "complaint_type": "Rodent",
            "descriptor": "Rat Sighting",
            "incident_zip": "10001",
            "borough": "MANHATTAN",
        }
    )
    return pd.DataFrame(rows)


def test_build_modeling_table_creates_targets_after_history_window() -> None:
    table = build_modeling_table(
        clean_rodent_complaints(_complaints()), min_history_weeks=8
    )
    known = table.loc[table["target_surge"].notna()]
    assert not known.empty
    assert known["surge_threshold"].ge(1).all()
    assert table.loc[table["is_scoring_row"], "target_surge"].isna().all()
