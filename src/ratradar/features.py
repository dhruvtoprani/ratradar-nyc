from __future__ import annotations

import numpy as np
import pandas as pd


def _completed_week_start(max_event_date: pd.Timestamp) -> pd.Timestamp:
    current_week_start = max_event_date.normalize() - pd.Timedelta(
        days=max_event_date.weekday()
    )
    return current_week_start - pd.Timedelta(days=7)


def aggregate_weekly_counts(
    complaints: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Timestamp]:
    if complaints.empty:
        raise ValueError("No cleaned complaints were provided")

    frame = complaints.copy()
    frame["created_date"] = pd.to_datetime(frame["created_date"])
    frame["week_start"] = frame["created_date"].dt.normalize() - pd.to_timedelta(
        frame["created_date"].dt.weekday, unit="D"
    )
    last_complete_week = _completed_week_start(frame["created_date"].max())
    frame = frame.loc[frame["week_start"] <= last_complete_week]
    if frame.empty:
        raise ValueError("No completed complaint weeks are available")

    counts = (
        frame.groupby(["zip_code", "week_start"], as_index=False)
        .size()
        .rename(columns={"size": "observed_rodent_count"})
    )

    zip_metadata = (
        frame.groupby("zip_code")["borough"]
        .agg(lambda values: values.mode().iat[0])
        .to_dict()
    )
    first_week = counts["week_start"].min()
    all_weeks = pd.date_range(first_week, last_complete_week, freq="W-MON")
    index = pd.MultiIndex.from_product(
        [sorted(zip_metadata), all_weeks], names=["zip_code", "prediction_date"]
    )

    weekly = (
        counts.rename(columns={"week_start": "prediction_date"})
        .set_index(["zip_code", "prediction_date"])["observed_rodent_count"]
        .reindex(index, fill_value=0)
        .rename("observed_rodent_count")
        .reset_index()
    )
    weekly["borough"] = weekly["zip_code"].map(zip_metadata)

    scoring_date = last_complete_week + pd.Timedelta(days=7)
    scoring_rows = pd.DataFrame(
        {
            "zip_code": sorted(zip_metadata),
            "prediction_date": scoring_date,
            "observed_rodent_count": np.nan,
            "borough": [zip_metadata[zip_code] for zip_code in sorted(zip_metadata)],
        }
    )
    weekly = pd.concat([weekly, scoring_rows], ignore_index=True)
    weekly = weekly.sort_values(["zip_code", "prediction_date"]).reset_index(drop=True)
    return weekly, last_complete_week


def _days_since_last_complaint(group: pd.DataFrame) -> pd.Series:
    prior_count = group["observed_rodent_count"].shift(1)
    prior_week = group["prediction_date"] - pd.Timedelta(days=7)
    last_nonzero_week = prior_week.where(prior_count.gt(0)).ffill()
    return (group["prediction_date"] - last_nonzero_week).dt.days


def _days_since_last_complaint_by_zip(frame: pd.DataFrame) -> pd.Series:
    result = pd.Series(index=frame.index, dtype="float64")
    for _, group in frame.groupby("zip_code"):
        ordered = group.sort_values("prediction_date")
        result.loc[ordered.index] = _days_since_last_complaint(ordered)
    return result


def add_rodent_history_features(weekly: pd.DataFrame) -> pd.DataFrame:
    frame = weekly.copy().sort_values(["zip_code", "prediction_date"])
    grouped = frame.groupby("zip_code", group_keys=False)
    prior = grouped["observed_rodent_count"].shift(1)

    frame["rodent_count_last_7d"] = prior
    frame["rodent_count_last_14d"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(2, min_periods=1).sum()
    )
    frame["rodent_count_last_30d"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(4, min_periods=1).sum()
    )
    frame["rodent_count_last_60d"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(9, min_periods=1).sum()
    )
    frame["rodent_count_last_90d"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(13, min_periods=1).sum()
    )
    frame["rodent_rolling_mean_4w"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(4, min_periods=2).mean()
    )
    frame["rodent_rolling_mean_8w"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(8, min_periods=4).mean()
    )
    frame["rodent_rolling_std_8w"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).rolling(8, min_periods=4).std()
    )
    frame["zip_baseline_rodent_rate"] = grouped["observed_rodent_count"].transform(
        lambda values: values.shift(1).expanding(min_periods=1).mean()
    )

    average_week_30d = frame["rodent_count_last_30d"] / 4
    average_week_60d = frame["rodent_count_last_60d"] / 9
    frame["rodent_velocity_7d_vs_30d"] = (
        frame["rodent_count_last_7d"] - average_week_30d
    ) / (average_week_30d + 1)
    frame["rodent_velocity_14d_vs_60d"] = (
        frame["rodent_count_last_14d"] / 2 - average_week_60d
    ) / (average_week_60d + 1)
    frame["days_since_last_rodent_complaint"] = _days_since_last_complaint_by_zip(frame)

    dates = pd.to_datetime(frame["prediction_date"])
    frame["week_of_year"] = dates.dt.isocalendar().week.astype(int)
    frame["month"] = dates.dt.month
    frame["quarter"] = dates.dt.quarter
    frame["year"] = dates.dt.year
    frame["is_summer"] = dates.dt.month.isin([6, 7, 8]).astype(int)
    frame["is_winter"] = dates.dt.month.isin([12, 1, 2]).astype(int)
    return frame
