from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, callout, configure_page

configure_page("Methodology")

brand_header(
    "MODEL CARD · VERSION 0.1",
    "Methodology",
    "How RatRadar converts public complaint history into a leakage-safe weekly prioritization signal.",
    status="PUBLIC METHODOLOGY",
)

callout(
    "A complaint-surge predictor, not a rat census.",
    "RatRadar predicts rodent complaint surge risk, not actual rat population density. "
    "311 volume reflects reporting behavior, access, awareness, trust, and local norms "
    "in addition to underlying rodent conditions.",
    eyebrow="CRITICAL INTERPRETATION",
)

st.subheader("Problem Framing")
st.write(
    "Every Monday, the MVP estimates whether each valid NYC incident ZIP code will "
    "experience a relative surge in rodent-related 311 complaints during the next seven days."
)

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Target")
    st.markdown("""
        - Aggregate complaints into Monday-starting weeks.
        - Compute each ZIP's expanding historical 75th percentile using only prior weeks.
        - Apply a minimum threshold of one complaint.
        - Label the next seven-day count as a surge when it meets or exceeds that threshold.
        - Require at least eight historical weeks before assigning a label.
        """)

    st.subheader("Features")
    st.markdown("""
        - Complaint counts over 7, 14, 30, 60, and 90-day windows
        - Four and eight-week baseline levels
        - Eight-week complaint volatility
        - Short-versus-long complaint velocity
        - Days since the last nonzero complaint week
        - Past-only ZIP baseline complaint rate
        - Calendar and borough terms
        """)

with right:
    st.subheader("Validation")
    st.markdown("""
        - Chronological train, validation, and test partitions
        - No random split
        - Decision threshold selected on validation F1
        - Final reporting on the untouched recent test period
        - Logistic regression baseline compared with XGBoost
        - Weekly top-10 precision reported for operational ranking quality
        """)

    st.subheader("Leakage Controls")
    st.markdown("""
        - Prediction rows are anchored to Monday.
        - Every lag feature is shifted by at least one completed week.
        - ZIP baselines and target thresholds are expanding past-only statistics.
        - The active incomplete week is excluded from observed training counts.
        - The latest scoring row has no known future target.
        """)

st.subheader("Data Sources")
st.markdown("""
    **Active MVP sources**
    - NYC 311 Service Requests from 2020 to present (`erm2-nwe9`)
    - NYC Modified ZIP Code Tabulation Areas (`pri4-ifjk`)

    **Planned controlled additions**
    - General 311 sanitation signals
    - Citywide weather
    - Restaurant inspection results
    - DOB permit activity
    """)

st.subheader("Limitations and Responsible Use")
st.markdown("""
    - Complaint counts are not direct measurements of rat population.
    - Relative ZIP thresholds improve fairness across different baseline volumes but make scores less intuitive.
    - Postal ZIP codes and MODZCTA map areas are not identical administrative geographies.
    - Historical correlations do not establish causal drivers.
    - Predictions should support inspection prioritization and investigation, not stigmatize residents or neighborhoods.
    - Human review remains necessary before operational action.
    """)
