from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#d7ccdf", "family": "Inter, ui-sans-serif, sans-serif"},
    "margin": {"l": 12, "r": 12, "t": 45, "b": 12},
    "hoverlabel": {"bgcolor": "#21162f", "font_color": "#fbf7ff"},
}


def complaint_history(frame: pd.DataFrame, zip_code: str) -> go.Figure:
    zip_frame = frame.loc[frame["zip_code"] == zip_code].sort_values("prediction_date")
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=zip_frame["prediction_date"],
            y=zip_frame["future_rodent_count_7d"],
            name="Weekly complaints",
            marker_color="#d8ff4f",
            opacity=0.75,
        )
    )
    figure.add_trace(
        go.Scatter(
            x=zip_frame["prediction_date"],
            y=zip_frame["rodent_rolling_mean_8w"],
            name="8-week baseline",
            line={"color": "#ff6b7a", "width": 2},
        )
    )
    figure.update_layout(
        **CHART_LAYOUT,
        title="Complaint volume vs. eight-week baseline",
        height=360,
        legend={"orientation": "h", "y": 1.08},
        xaxis={"gridcolor": "rgba(148,163,184,.08)"},
        yaxis={"gridcolor": "rgba(148,163,184,.08)", "title": None},
    )
    return figure


def risk_history(frame: pd.DataFrame, zip_code: str) -> go.Figure:
    zip_frame = frame.loc[
        (frame["zip_code"] == zip_code) & frame["risk_probability"].notna()
    ].sort_values("prediction_date")
    figure = px.area(
        zip_frame,
        x="prediction_date",
        y="risk_probability",
        title="Modeled surge probability",
        color_discrete_sequence=["#a78bfa"],
    )
    figure.update_traces(line={"width": 2}, fillcolor="rgba(167,139,250,.16)")
    figure.update_layout(
        **CHART_LAYOUT,
        height=300,
        yaxis={
            "tickformat": ".0%",
            "range": [0, 1],
            "gridcolor": "rgba(148,163,184,.08)",
        },
        xaxis={"gridcolor": "rgba(148,163,184,.08)"},
    )
    return figure


def feature_importance(frame: pd.DataFrame, limit: int = 12) -> go.Figure:
    plotted = frame.head(limit).sort_values("importance")
    figure = px.bar(
        plotted,
        x="importance",
        y="feature",
        orientation="h",
        title="Global XGBoost feature importance",
        color="importance",
        color_continuous_scale=["#261934", "#a78bfa", "#d8ff4f"],
    )
    figure.update_layout(
        **CHART_LAYOUT,
        height=430,
        coloraxis_showscale=False,
        xaxis={"gridcolor": "rgba(148,163,184,.08)", "title": None},
        yaxis={"title": None},
    )
    return figure


def roc_chart(metrics: dict[str, Any]) -> go.Figure:
    models = metrics.get("models", {})
    figure = go.Figure()
    colors = {"xgboost": "#d8ff4f", "logistic_regression": "#a78bfa"}
    for model_name, model_metrics in models.items():
        curve = model_metrics.get("roc_curve", {})
        figure.add_trace(
            go.Scatter(
                x=curve.get("false_positive_rate", []),
                y=curve.get("true_positive_rate", []),
                mode="lines",
                name=model_name.replace("_", " ").title(),
                line={"color": colors.get(model_name, "#94a3b8"), "width": 3},
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Random",
            line={"color": "#6f617d", "dash": "dash"},
        )
    )
    figure.update_layout(
        **CHART_LAYOUT,
        title="ROC curve",
        height=390,
        xaxis={"title": "False positive rate", "gridcolor": "rgba(148,163,184,.08)"},
        yaxis={"title": "True positive rate", "gridcolor": "rgba(148,163,184,.08)"},
    )
    return figure


def precision_recall_chart(metrics: dict[str, Any]) -> go.Figure:
    models = metrics.get("models", {})
    figure = go.Figure()
    colors = {"xgboost": "#ff6b7a", "logistic_regression": "#a78bfa"}
    for model_name, model_metrics in models.items():
        curve = model_metrics.get("precision_recall_curve", {})
        figure.add_trace(
            go.Scatter(
                x=curve.get("recall", []),
                y=curve.get("precision", []),
                mode="lines",
                name=model_name.replace("_", " ").title(),
                line={"color": colors.get(model_name, "#94a3b8"), "width": 3},
            )
        )
    figure.update_layout(
        **CHART_LAYOUT,
        title="Precision–recall curve",
        height=390,
        xaxis={"title": "Recall", "gridcolor": "rgba(148,163,184,.08)"},
        yaxis={"title": "Precision", "gridcolor": "rgba(148,163,184,.08)"},
    )
    return figure


def confusion_matrix_chart(metrics: dict[str, Any]) -> go.Figure:
    matrix = (
        metrics.get("models", {})
        .get("xgboost", {})
        .get("confusion_matrix", [[0, 0], [0, 0]])
    )
    figure = px.imshow(
        matrix,
        text_auto=True,
        x=["Predicted no surge", "Predicted surge"],
        y=["Actual no surge", "Actual surge"],
        color_continuous_scale=["#21162f", "#d8ff4f"],
        title="XGBoost confusion matrix",
    )
    figure.update_layout(**CHART_LAYOUT, height=390, coloraxis_showscale=False)
    return figure
