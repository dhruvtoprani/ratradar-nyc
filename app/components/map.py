from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def risk_map(latest: pd.DataFrame, geojson: dict[str, Any] | None) -> go.Figure | None:
    if latest.empty or not geojson:
        return None
    figure = px.choropleth_mapbox(
        latest,
        geojson=geojson,
        locations="zip_code",
        featureidkey="properties.zip_code",
        color="risk_probability",
        color_continuous_scale=[
            [0.0, "#281c47"],
            [0.2, "#765ad6"],
            [0.4, "#d8ff4f"],
            [0.6, "#ffce69"],
            [0.8, "#ff8a64"],
            [1.0, "#ff4f6d"],
        ],
        range_color=(0, 1),
        mapbox_style="carto-darkmatter",
        zoom=9,
        center={"lat": 40.7128, "lon": -74.0060},
        opacity=0.78,
        hover_name="zip_code",
        hover_data={
            "borough": True,
            "risk_probability": ":.1%",
            "risk_tier": True,
            "top_driver": True,
            "zip_code": False,
        },
        labels={"risk_probability": "Surge risk"},
    )
    figure.update_layout(
        height=650,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar={
            "title": {"text": "RISK", "font": {"color": "#d7ccdf"}},
            "tickformat": ".0%",
            "bgcolor": "rgba(20,12,31,.9)",
            "tickfont": {"color": "#d7ccdf"},
        },
    )
    return figure
