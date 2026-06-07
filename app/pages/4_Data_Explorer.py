from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, configure_page
from app.components.data import app_state, render_setup_state

configure_page("Data Explorer")
state = app_state()
predictions = state["all_predictions"]

brand_header(
    "AUDITABLE PREDICTION TABLE",
    "Data Explorer",
    "Filter historical model rows, inspect feature values, and export prediction records for independent analysis.",
    status="DATA ACCESS" if not predictions.empty else "SETUP REQUIRED",
)

if predictions.empty:
    render_setup_state()
    st.stop()

filters = st.columns(4)
borough_options = ["All"] + sorted(predictions["borough"].dropna().unique().tolist())
borough = filters[0].selectbox("Borough", borough_options)
risk_options = ["All"] + ["Low", "Watch", "Elevated", "High", "Critical"]
risk_tier = filters[1].selectbox("Risk tier", risk_options)
zip_options = ["All"] + sorted(predictions["zip_code"].unique().tolist())
zip_code = filters[2].selectbox("ZIP code", zip_options)
date_range = filters[3].date_input(
    "Prediction dates",
    value=(
        predictions["prediction_date"].min().date(),
        predictions["prediction_date"].max().date(),
    ),
)

filtered = predictions.copy()
if borough != "All":
    filtered = filtered.loc[filtered["borough"] == borough]
if risk_tier != "All":
    filtered = filtered.loc[filtered["risk_tier"] == risk_tier]
if zip_code != "All":
    filtered = filtered.loc[filtered["zip_code"] == zip_code]
if len(date_range) == 2:
    filtered = filtered.loc[
        filtered["prediction_date"].dt.date.between(date_range[0], date_range[1])
    ]

st.caption(f"{len(filtered):,} rows match the active filters.")
display_columns = [
    "prediction_date",
    "zip_code",
    "borough",
    "risk_probability",
    "risk_tier",
    "predicted_surge",
    "target_surge",
    "rodent_count_last_7d",
    "rodent_count_last_30d",
    "rodent_rolling_mean_8w",
    "rodent_velocity_7d_vs_30d",
    "top_driver",
]
available_columns = [column for column in display_columns if column in filtered]
st.dataframe(
    filtered[available_columns].sort_values(
        ["prediction_date", "risk_probability"], ascending=[False, False]
    ),
    hide_index=True,
    use_container_width=True,
    height=560,
    column_config={
        "risk_probability": st.column_config.ProgressColumn(
            "Risk probability", min_value=0, max_value=1, format="%.1f%%"
        ),
        "prediction_date": st.column_config.DateColumn("Prediction date"),
    },
)
st.download_button(
    "Download filtered predictions",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="ratradar_predictions.csv",
    mime="text/csv",
)
