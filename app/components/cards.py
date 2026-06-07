from __future__ import annotations

from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def configure_page(title: str, icon: str = "◉") -> None:
    st.set_page_config(
        page_title=f"{title} · RatRadar NYC",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css_path = PROJECT_ROOT / "app/assets/style.css"
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def brand_header(
    kicker: str,
    title: str,
    description: str,
    *,
    status: str = "MODEL ONLINE",
) -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="brand-row">
            <div class="radar-mark"><span></span></div>
            <div>
              <div class="eyebrow">{kicker}</div>
              <h1>{title}</h1>
            </div>
            <div class="status-pill"><i></i>{status}</div>
          </div>
          <p>{description}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, detail: str, tone: str = "cyan") -> str:
    return f"""
    <div class="metric-card tone-{tone}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-detail">{detail}</div>
    </div>
    """


def callout(title: str, body: str, eyebrow: str = "RATRADAR BRIEF") -> None:
    st.markdown(
        f"""
        <div class="brief-card">
          <div class="eyebrow">{eyebrow}</div>
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(tier: str) -> str:
    return f'<span class="risk-badge risk-{tier.lower()}">{tier}</span>'
