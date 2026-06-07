from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, configure_page, metric_card
from app.components.data import app_state, render_setup_state
from app.components.map import risk_map

configure_page("Risk Map")
state = app_state()
latest = state["latest"]

brand_header(
    "GEOSPATIAL WATCHBOARD",
    "NYC Risk Map",
    "Scan modeled complaint-surge probability across the city, then move from citywide context to ZIP-level inspection priority.",
    status="LIVE RISK LAYER" if not latest.empty else "SETUP REQUIRED",
)

if latest.empty:
    render_setup_state()
    st.stop()

boroughs = ["All boroughs"] + sorted(latest["borough"].dropna().unique().tolist())
selected_borough = st.selectbox("Borough focus", boroughs)
filtered = (
    latest
    if selected_borough == "All boroughs"
    else latest.loc[latest["borough"] == selected_borough]
)

summary = st.columns(3)
summary[0].markdown(
    metric_card(
        "Average Risk", f"{filtered['risk_probability'].mean():.1%}", selected_borough
    ),
    unsafe_allow_html=True,
)
summary[1].markdown(
    metric_card(
        "High / Critical",
        str(filtered["risk_tier"].isin(["High", "Critical"]).sum()),
        "ZIPs above 60% probability",
        "red",
    ),
    unsafe_allow_html=True,
)
summary[2].markdown(
    metric_card(
        "Highest Signal",
        filtered.nlargest(1, "risk_probability")["zip_code"].iat[0],
        filtered.nlargest(1, "risk_probability")["top_driver"].iat[0],
        "amber",
    ),
    unsafe_allow_html=True,
)

figure = risk_map(filtered, state["geojson"])
if figure:
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Run `python scripts/fetch_zip_boundaries.py` to activate the map.")

st.caption(
    "Risk tiers: Low 0–20% · Watch 20–40% · Elevated 40–60% · High 60–80% · Critical 80–100%"
)
