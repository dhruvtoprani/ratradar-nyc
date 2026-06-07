# Development Notes

## 2026-06-07 — MVP Scope Locked

**Decision:** Build the rodent-history baseline and dashboard before integrating general 311, weather, restaurant, or permit data.

**Why:** A working vertical slice provides the fastest validation of the target, leakage controls, model artifacts, and product experience.

**Tradeoff:** Initial model lift may be limited because the strongest external signals are intentionally deferred.

**Files changed:**
- Repository bootstrap files
- Core pipeline modules
- Streamlit application

## 2026-06-07 — Weekly Prediction Semantics

**Decision:** Each row represents a Monday prediction date. Lag features use completed weeks strictly before that Monday; the label uses complaints created during the following seven-day window.

**Why:** This makes feature availability explicit and prevents the current prediction week from entering the feature set.

**Tradeoff:** Weekly aggregation removes daily detail but reduces noise and makes the dashboard easier to interpret.

**Files changed:**
- `src/ratradar/features.py`
- `src/ratradar/targets.py`
- `tests/test_no_leakage.py`

## 2026-06-07 — Surge Threshold

**Decision:** Use a past-only, ZIP-specific expanding 75th percentile with at least eight historical weeks and a one-complaint floor.

**Why:** ZIP-specific thresholds prevent high-volume areas from dominating the label. The expanding threshold avoids future leakage.

**Tradeoff:** The label is relative to each ZIP and is less intuitive than a global complaint threshold.

**Files changed:**
- `src/ratradar/targets.py`
- `scripts/build_dataset.py`

## 2026-06-07 — Official Source Query Tightened

**Decision:** Use `complaint_type = 'Rodent'` as the default Socrata filter and keep descriptor-based rat/mouse matching behind `--include-descriptor-matches`.

**Why:** The broad descriptor `OR` query is materially slower on the 2020-present dataset. The exact complaint type was validated against a live 2026 sample and is the appropriate indexed MVP source.

**Tradeoff:** Descriptor-only rodent-adjacent records are excluded by default, which is acceptable for the MVP because the official rodent complaint type is the target source.

**Files changed:**
- `scripts/fetch_311_rodent.py`
- `src/ratradar/data_sources.py`

## 2026-06-07 — Mapped ZIP Universe

**Decision:** Filter cleaned complaints to ZIP codes present in the official NYC MODZCTA GeoJSON when `data/external/nyc_modzcta.geojson` exists.

**Why:** The 311 data includes special-purpose ZIPs without MODZCTA polygons. Filtering to mapped ZIPs ensures every scored location appears on the dashboard.

**Tradeoff:** A small number of valid postal or facility ZIPs are excluded from the MVP risk surface.

**Files changed:**
- `scripts/build_dataset.py`
- `data/external/nyc_modzcta.geojson`

## 2026-06-07 — Real MVP Trained

**Decision:** Train the baseline on official NYC 311 Rodent complaints from January 1, 2020 through June 6, 2026, using data through the completed week ending May 31, 2026.

**Why:** This creates a real, current MVP artifact set instead of a placeholder or sample-only dashboard.

**Tradeoff:** The latest prediction date is June 1, 2026 because incomplete current-week observations are excluded from features and labels.

**Files changed:**
- `data/processed/rodent_zip_week.parquet`
- `data/predictions/latest_predictions.parquet`
- `models/ratradar_xgb.pkl`
- `models/metrics.json`
- `models/shap_values.parquet`

## 2026-06-07 — Public Release Architecture

**Decision:** Keep Streamlit as the complete analytical application and deploy a static interactive showcase generated from the same model artifacts.

**Why:** Streamlit depends on a persistent Python server and websocket connection, which is not a reliable Vercel runtime. A generated static showcase preserves interactive maps, charts, filters, and ZIP drilldown while producing a stable public URL.

**Tradeoff:** The public release does not execute model training or Python callbacks. Those remain in the full local Streamlit application.

**Files changed:**
- `scripts/build_showcase.py`
- `web/index.html`
- `web/styles.css`
- `web/app.js`
- `DEPLOYMENT.md`

## 2026-06-07 — Visual System Relaunch

**Decision:** Replace the original navy/cyan visual language with Midnight Plum, Acid Lime, Ultraviolet, Signal Orange, and Signal Coral.

**Why:** The original palette read as a familiar generic dashboard. The new system is more distinctive, editorial, and portfolio-ready while retaining strong risk contrast.

**Tradeoff:** Acid lime is intentionally prominent and must remain reserved for active state and primary signal emphasis.

**Files changed:**
- `app/assets/style.css`
- `app/components/charts.py`
- `app/components/map.py`
- `.streamlit/config.toml`
- `web/styles.css`

## 2026-06-07 — GitHub Artifact Policy

**Decision:** Track the trained model, evaluation outputs, SHAP values, MODZCTA geometry, processed modeling table, and prediction artifacts in the public release while excluding the raw NYC 311 extract.

**Why:** The complete MVP remains immediately inspectable and demo-ready from GitHub. The raw source is reproducible through the ingestion script and does not need to be duplicated in version control.

**Tradeoff:** Cloning the repository includes several megabytes of generated release artifacts, but avoids requiring a full data fetch and model training before the dashboard can be reviewed.

**Files changed:**
- `.gitignore`
- `README.md`
