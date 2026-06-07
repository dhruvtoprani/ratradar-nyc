# RatRadar NYC Context

## Purpose

RatRadar NYC predicts whether each NYC ZIP code will experience a rodent-related 311 complaint surge during the next seven days. It is an operational prioritization tool, not a rat population estimator.

## Current Status

The Phase 0–3 MVP is implemented, trained on official data, and browser-verified:

- Official NYC 311 rodent ingestion
- Complaint cleaning and NYC ZIP validation
- Weekly, leakage-safe modeling table
- Logistic regression baseline and XGBoost training
- Time-based metrics and top-10 precision
- Latest prediction artifacts
- Multi-page Streamlit dashboard
- MODZCTA boundary ingestion
- Feature, target, and leakage tests
- Streamlit dashboard running successfully at `http://localhost:8501` in the current session
- Static public showcase deployed at `https://ratradar-nyc.vercel.app`
- GitHub release prepared for `https://github.com/dhruvtoprani/ratradar-nyc`

The local environment uses Python 3.12 in `.venv`. XGBoost required `brew install libomp` on this macOS machine.

## Major Decisions

- Prediction cadence: every Monday
- Geographic unit: incident ZIP code, mapped with MODZCTA geometry
- MVP source: rodent-related NYC 311 complaints only
- Target: future weekly complaints at or above the ZIP's past-only expanding 75th percentile
- Threshold floor: one complaint
- Minimum label history: eight weeks
- Validation: chronological train/validation/test partitions
- Product ranking metric: weekly top-10 precision
- Modeling universe: ZIPs present in the official MODZCTA GeoJSON
- Latest prediction date: June 1, 2026
- Data used for completed features: through May 31, 2026
- Raw source fetch: 230,339 official 311 Rodent records through June 6, 2026
- Visual system: Midnight Plum × Acid Lime × Signal Coral
- GitHub artifact policy: publish processed/model/demo artifacts; regenerate raw NYC 311 data locally

## Current Features

- Complaint counts over 7, 14, approximately 30, 60, and 90 days
- Four- and eight-week rolling mean
- Eight-week rolling standard deviation
- Short-versus-long complaint velocity
- Days since the last nonzero complaint week
- Past-only ZIP baseline complaint rate
- Month, quarter, week of year, year, summer, and winter flags
- Borough encoded by the model preprocessing pipeline

## Data Files

Expected artifacts:

- `data/raw/311_rodent.parquet`
- `data/external/nyc_modzcta.geojson`
- `data/processed/rodent_zip_week.parquet`
- `data/predictions/all_predictions.parquet`
- `data/predictions/latest_predictions.parquet`
- `models/ratradar_xgb.pkl`
- `models/feature_columns.json`
- `models/metrics.json`
- `models/feature_importance.parquet`

Current artifact status:

- `data/processed/rodent_zip_week.parquet`: 59,472 ZIP-week rows
- `data/predictions/latest_predictions.parquet`: 177 latest ZIP scores
- `models/metrics.json`: XGBoost ROC-AUC 0.780, PR-AUC 0.455, top-10 precision 0.488
- `models/shap_values.parquet`: generated for the trained XGBoost model
- `web/`: public interactive showcase generated from the model artifacts
- `app/assets/ratradar-product-tour.gif`: full product demo
- `app/assets/ratradar-zip-demo.gif`: ZIP interaction demo

## Known Issues

- The current machine's default Python is 3.13; use `.venv` with Python 3.12.
- XGBoost on macOS requires Homebrew `libomp`.
- PyArrow emits sandbox-related `sysctlbyname` CPU cache warnings during Parquet operations; the commands still complete successfully.
- The dashboard displays a clear setup state if artifacts are deleted or regenerated elsewhere.
- MODZCTA geometry can combine postal ZIP codes and is an approximation for mapping.

## Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_311_rodent.py
python scripts/fetch_zip_boundaries.py
python scripts/build_dataset.py
python scripts/train_model.py
streamlit run app/Home.py
```

## Next Steps

1. Review the baseline model metrics and top-risk ZIP outputs.
2. Promote SHAP outputs into the ZIP Drilldown explanation card.
3. Add general 311 sanitation features.
4. Add citywide weather features.
5. Compare feature lift with controlled ablation reports.
6. Add a scheduled weekly refresh for generated artifacts and the public showcase.
