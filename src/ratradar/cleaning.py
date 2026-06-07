from __future__ import annotations

import re

import pandas as pd

NYC_BOROUGHS = {
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "MANHATTAN": "Manhattan",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
    "STATEN_ISLAND": "Staten Island",
}
NYC_ZIP_PREFIXES = {
    "100",
    "101",
    "102",
    "103",
    "104",
    "110",
    "111",
    "112",
    "113",
    "114",
    "116",
}
RODENT_PATTERN = re.compile(r"rodent|rat|mouse|mice", flags=re.IGNORECASE)


def normalize_zip(value: object) -> str | None:
    if pd.isna(value):
        return None
    match = re.search(r"\b(\d{5})\b", str(value).strip())
    if not match:
        return None
    zip_code = match.group(1)
    if zip_code[:3] not in NYC_ZIP_PREFIXES:
        return None
    if zip_code.startswith("110") and zip_code not in {"11004", "11005"}:
        return None
    return zip_code


def normalize_borough(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip().upper()
    return NYC_BOROUGHS.get(normalized)


def clean_rodent_complaints(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [column.strip().lower() for column in frame.columns]

    required = {"created_date", "incident_zip"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    for optional in (
        "complaint_type",
        "descriptor",
        "borough",
        "latitude",
        "longitude",
        "status",
        "resolution_description",
        "unique_key",
    ):
        if optional not in frame:
            frame[optional] = pd.NA

    frame["created_date"] = pd.to_datetime(frame["created_date"], errors="coerce")
    if getattr(frame["created_date"].dt, "tz", None) is not None:
        frame["created_date"] = frame["created_date"].dt.tz_localize(None)

    frame["zip_code"] = frame["incident_zip"].map(normalize_zip)
    frame["borough"] = frame["borough"].map(normalize_borough)

    complaint_text = (
        frame["complaint_type"].fillna("").astype(str)
        + " "
        + frame["descriptor"].fillna("").astype(str)
    )
    rodent_mask = complaint_text.str.contains(RODENT_PATTERN, na=False)

    frame = frame.loc[
        frame["created_date"].notna()
        & frame["zip_code"].notna()
        & frame["borough"].notna()
        & rodent_mask
    ].copy()

    frame["event_date"] = frame["created_date"].dt.normalize()
    frame = frame.sort_values(["created_date", "zip_code", "unique_key"])

    columns = [
        "unique_key",
        "created_date",
        "event_date",
        "complaint_type",
        "descriptor",
        "zip_code",
        "borough",
        "latitude",
        "longitude",
        "status",
        "resolution_description",
    ]
    return frame[columns].reset_index(drop=True)
