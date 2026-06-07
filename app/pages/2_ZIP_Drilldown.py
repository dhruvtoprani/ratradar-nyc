from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, callout, configure_page, metric_card
from app.components.charts import complaint_history, risk_history
from app.components.data import app_state, render_setup_state

configure_page("ZIP Drilldown")
state = app_state()
latest = state["latest"]
history = state["all_predictions"]

brand_header(
    "LOCAL SIGNAL ANALYSIS",
    "ZIP Intelligence",
    "Inspect complaint momentum, baseline behavior, model trajectory, and the primary reason a ZIP entered the weekly priority queue.",
    status="ZIP ANALYSIS" if not latest.empty else "SETUP REQUIRED",
)

if latest.empty:
    render_setup_state()
    st.stop()

default_zip = latest.nlargest(1, "risk_probability")["zip_code"].iat[0]
zip_codes = sorted(latest["zip_code"].unique().tolist())
selected_zip = st.selectbox(
    "Select ZIP code",
    zip_codes,
    index=zip_codes.index(default_zip),
)
current = latest.loc[latest["zip_code"] == selected_zip].iloc[0]

cards = st.columns(4)
cards[0].markdown(
    metric_card(
        "Surge Risk", f"{current['risk_probability']:.1%}", current["risk_tier"], "red"
    ),
    unsafe_allow_html=True,
)
cards[1].markdown(
    metric_card(
        "Last 7 Days", f"{current['rodent_count_last_7d']:.0f}", "Rodent complaints"
    ),
    unsafe_allow_html=True,
)
cards[2].markdown(
    metric_card(
        "8-Week Baseline",
        f"{current['rodent_rolling_mean_8w']:.1f}",
        "Complaints per week",
        "amber",
    ),
    unsafe_allow_html=True,
)
cards[3].markdown(
    metric_card(
        "Complaint Velocity",
        f"{current['rodent_velocity_7d_vs_30d']:+.0%}",
        "Versus recent monthly pace",
        "violet",
    ),
    unsafe_allow_html=True,
)

callout(
    f"Why ZIP {selected_zip}?",
    current["why_this_zip"],
    eyebrow=f"{current['borough']} · {current['top_driver']}",
)

if history.empty:
    st.info("Historical scored predictions are not available.")
else:
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.plotly_chart(
            complaint_history(history, selected_zip),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with right:
        st.plotly_chart(
            risk_history(history, selected_zip),
            use_container_width=True,
            config={"displayModeBar": False},
        )

st.subheader("Signal Readout")
signal_table = {
    "Signal": [
        "30-day complaint volume",
        "90-day complaint volume",
        "Complaint volatility",
        "Persistent ZIP baseline",
        "Days since last complaint",
    ],
    "Current value": [
        f"{current['rodent_count_last_30d']:.0f}",
        f"{current['rodent_count_last_90d']:.0f}",
        f"{current['rodent_rolling_std_8w']:.1f}",
        f"{current['zip_baseline_rodent_rate']:.1f}",
        f"{current['days_since_last_rodent_complaint']:.0f}",
    ],
}
st.dataframe(signal_table, hide_index=True, use_container_width=True)
