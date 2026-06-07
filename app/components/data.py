from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LATEST_PREDICTIONS = PROJECT_ROOT / "data/predictions/latest_predictions.parquet"
ALL_PREDICTIONS = PROJECT_ROOT / "data/predictions/all_predictions.parquet"
MODELING_DATA = PROJECT_ROOT / "data/processed/rodent_zip_week.parquet"
METRICS = PROJECT_ROOT / "models/metrics.json"
FEATURE_IMPORTANCE = PROJECT_ROOT / "models/feature_importance.parquet"
GEOJSON = PROJECT_ROOT / "data/external/nyc_modzcta.geojson"


@st.cache_data(show_spinner=False)
def load_parquet(path: str) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    for column in ("prediction_date", "data_through_date"):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column])
    if "zip_code" in frame:
        frame["zip_code"] = frame["zip_code"].astype(str).str.zfill(5)
    return frame


@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def app_state() -> dict[str, Any]:
    return {
        "latest": (
            load_parquet(str(LATEST_PREDICTIONS))
            if LATEST_PREDICTIONS.exists()
            else pd.DataFrame()
        ),
        "all_predictions": (
            load_parquet(str(ALL_PREDICTIONS))
            if ALL_PREDICTIONS.exists()
            else pd.DataFrame()
        ),
        "modeling": (
            load_parquet(str(MODELING_DATA))
            if MODELING_DATA.exists()
            else pd.DataFrame()
        ),
        "metrics": load_json(str(METRICS)) if METRICS.exists() else {},
        "importance": (
            load_parquet(str(FEATURE_IMPORTANCE))
            if FEATURE_IMPORTANCE.exists()
            else pd.DataFrame()
        ),
        "geojson": load_json(str(GEOJSON)) if GEOJSON.exists() else None,
    }


def render_setup_state() -> None:
    st.markdown(
        """
        <div class="setup-card">
          <div class="eyebrow">SYSTEM STATUS · AWAITING ARTIFACTS</div>
          <h2>Run the baseline pipeline to activate RatRadar.</h2>
          <p>The interface is ready. It needs processed 311 data, a trained model,
          and the latest ZIP risk predictions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        "\n".join(
            [
                "python scripts/fetch_311_rodent.py",
                "python scripts/fetch_zip_boundaries.py",
                "python scripts/build_dataset.py",
                "python scripts/train_model.py",
            ]
        ),
        language="bash",
    )
