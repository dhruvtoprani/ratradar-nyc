from __future__ import annotations

import pandas as pd

from ratradar.config import MIN_HISTORY_WEEKS
from ratradar.features import add_rodent_history_features, aggregate_weekly_counts


def add_surge_target(
    weekly_features: pd.DataFrame,
    *,
    quantile: float = 0.75,
    min_history_weeks: int = MIN_HISTORY_WEEKS,
) -> pd.DataFrame:
    frame = weekly_features.copy().sort_values(["zip_code", "prediction_date"])
    grouped = frame.groupby("zip_code", group_keys=False)

    frame["surge_threshold"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1)
        .expanding(min_periods=min_history_weeks)
        .quantile(quantile)
        .clip(lower=1)
    )
    frame["future_rodent_count_7d"] = frame["observed_rodent_count"]

    known_label = (
        frame["future_rodent_count_7d"].notna() & frame["surge_threshold"].notna()
    )
    target = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    target.loc[known_label] = (
        frame.loc[known_label, "future_rodent_count_7d"]
        >= frame.loc[known_label, "surge_threshold"]
    ).astype(int)
    frame["target_surge"] = target
    frame["is_scoring_row"] = frame["future_rodent_count_7d"].isna()
    return frame


def build_modeling_table(
    complaints: pd.DataFrame,
    *,
    quantile: float = 0.75,
    min_history_weeks: int = MIN_HISTORY_WEEKS,
) -> pd.DataFrame:
    weekly, last_complete_week = aggregate_weekly_counts(complaints)
    features = add_rodent_history_features(weekly)
    modeled = add_surge_target(
        features, quantile=quantile, min_history_weeks=min_history_weeks
    )
    modeled["data_through_date"] = last_complete_week + pd.Timedelta(days=6)
    return modeled.sort_values(["prediction_date", "zip_code"]).reset_index(drop=True)
