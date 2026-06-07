from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, callout, configure_page, metric_card
from app.components.data import app_state, render_setup_state
from app.components.map import risk_map
from app.components.metrics import build_weekly_brief, format_score, model_metric

configure_page("Overview")
state = app_state()
latest = state["latest"]
metrics = state["metrics"]

brand_header(
    "NYC CIVIC INTELLIGENCE · WEEKLY OPERATIONS",
    "RatRadar NYC",
    "An interpretable early-warning system for rodent complaint surges across New York City ZIP codes.",
    status="MODEL ONLINE" if not latest.empty else "SETUP REQUIRED",
)

if latest.empty:
    render_setup_state()
    st.stop()

prediction_date = latest["prediction_date"].max()
average_risk = latest["risk_probability"].mean()
roc_auc = model_metric(metrics, "roc_auc")
pr_auc = model_metric(metrics, "pr_auc")

columns = st.columns(4)
cards = [
    metric_card(
        "Prediction Date",
        prediction_date.strftime("%b %d"),
        prediction_date.strftime("%Y · next 7-day window"),
    ),
    metric_card(
        "ZIPs Scored",
        f"{latest['zip_code'].nunique():,}",
        "Valid NYC incident ZIP codes",
        "violet",
    ),
    metric_card(
        "Citywide Risk",
        f"{average_risk:.1%}",
        "Average modeled surge probability",
        "amber",
    ),
    metric_card(
        "Test ROC-AUC",
        format_score(roc_auc),
        f"PR-AUC {format_score(pr_auc)}",
        "red",
    ),
]
for column, card in zip(columns, cards, strict=True):
    column.markdown(card, unsafe_allow_html=True)

brief_title, brief_body = build_weekly_brief(latest)
callout(brief_title, brief_body)

map_column, ranking_column = st.columns([1.75, 1], gap="large")
with map_column:
    st.subheader("Citywide Risk Surface")
    figure = risk_map(latest, state["geojson"])
    if figure:
        st.plotly_chart(
            figure, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.info("Run `python scripts/fetch_zip_boundaries.py` to activate the map.")

with ranking_column:
    st.subheader("Priority Queue")
    ranking = latest.nlargest(10, "risk_probability")[
        ["zip_code", "borough", "risk_probability", "risk_tier", "top_driver"]
    ].copy()
    ranking["risk_probability"] = ranking["risk_probability"].map(
        lambda value: f"{value:.1%}"
    )
    ranking.columns = ["ZIP", "Borough", "Risk", "Tier", "Primary signal"]
    st.dataframe(ranking, hide_index=True, use_container_width=True, height=420)
    st.caption(
        "Priority ranks are model outputs for operational review, not enforcement decisions."
    )
