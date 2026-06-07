from __future__ import annotations

from typing import Any

import pandas as pd


def model_metric(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get("models", {}).get("xgboost", {}).get(key)
    return None if value is None else float(value)


def format_score(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:.3f}"


def build_weekly_brief(latest: pd.DataFrame) -> tuple[str, str]:
    if latest.empty:
        return "Signals unavailable", "Run the model pipeline to generate this brief."
    ranked = latest.nlargest(3, "risk_probability")
    zip_list = ", ".join(ranked["zip_code"].astype(str).tolist())
    borough_risk = (
        latest.groupby("borough", as_index=False)["risk_probability"]
        .mean()
        .sort_values("risk_probability", ascending=False)
    )
    leading_boroughs = " and ".join(borough_risk.head(2)["borough"].tolist())
    drivers = ", ".join(
        latest["top_driver"].value_counts().head(2).index.str.lower().tolist()
    )
    title = f"Priority signals cluster in {leading_boroughs}."
    body = (
        f"ZIPs {zip_list} carry the highest modeled surge risk this week. "
        f"The dominant baseline drivers are {drivers}. This is a complaint-surge "
        "prioritization signal, not an estimate of rat population density."
    )
    return title, body
