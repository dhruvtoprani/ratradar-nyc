from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.components.cards import brand_header, configure_page, metric_card
from app.components.charts import (
    confusion_matrix_chart,
    feature_importance,
    precision_recall_chart,
    roc_chart,
)
from app.components.data import app_state, render_setup_state
from app.components.metrics import format_score, model_metric

configure_page("Model Intelligence")
state = app_state()
metrics = state["metrics"]
importance = state["importance"]

brand_header(
    "MODEL CONTROL ROOM",
    "Model Intelligence",
    "Evaluate ranking quality, classification tradeoffs, chronological validation, and the global signals used by the XGBoost baseline.",
    status="EVALUATION READY" if metrics else "SETUP REQUIRED",
)

if not metrics:
    render_setup_state()
    st.stop()

cards = st.columns(4)
metric_specs = [
    ("ROC-AUC", model_metric(metrics, "roc_auc"), "Ranking discrimination", "cyan"),
    ("PR-AUC", model_metric(metrics, "pr_auc"), "Positive-class quality", "amber"),
    ("F1", model_metric(metrics, "f1"), "Thresholded balance", "violet"),
    (
        "Top-10 Precision",
        model_metric(metrics, "top_10_precision"),
        "Weekly priority queue",
        "red",
    ),
]
for column, (label, value, detail, tone) in zip(cards, metric_specs, strict=True):
    column.markdown(
        metric_card(label, format_score(value), detail, tone),
        unsafe_allow_html=True,
    )

left, right = st.columns(2, gap="large")
with left:
    st.plotly_chart(
        roc_chart(metrics), use_container_width=True, config={"displayModeBar": False}
    )
with right:
    st.plotly_chart(
        precision_recall_chart(metrics),
        use_container_width=True,
        config={"displayModeBar": False},
    )

left, right = st.columns([1, 1.35], gap="large")
with left:
    st.plotly_chart(
        confusion_matrix_chart(metrics),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with right:
    if not importance.empty:
        st.plotly_chart(
            feature_importance(importance),
            use_container_width=True,
            config={"displayModeBar": False},
        )

st.subheader("Baseline Comparison")
rows = []
for name, values in metrics.get("models", {}).items():
    rows.append(
        {
            "Model": name.replace("_", " ").title(),
            "ROC-AUC": values.get("roc_auc"),
            "PR-AUC": values.get("pr_auc"),
            "F1": values.get("f1"),
            "Precision": values.get("precision"),
            "Recall": values.get("recall"),
            "Top-10 Precision": values.get("top_10_precision"),
        }
    )
comparison = pd.DataFrame(rows)
st.dataframe(
    comparison.style.format(precision=3),
    hide_index=True,
    use_container_width=True,
)

splits = metrics.get("split_dates", {})
st.info(
    f"Chronological split — train {splits.get('train', {}).get('start')} to "
    f"{splits.get('train', {}).get('end')}; validation "
    f"{splits.get('validation', {}).get('start')} to "
    f"{splits.get('validation', {}).get('end')}; test "
    f"{splits.get('test', {}).get('start')} to {splits.get('test', {}).get('end')}."
)
