# Build Log

## Entry 001 — Project Initialized

**Completed:**
- Created the repository structure and dependency manifest
- Added the complete MVP product and methodology documentation
- Defined leakage-safe weekly prediction semantics
- Added the Streamlit application structure

**Next:**
- Validate the official Socrata query against a small live sample
- Run the weekly feature and target tests
- Train the first production-data model

## Entry 002 — Rodent MVP Implemented

**Completed:**
- Added paginated NYC 311 rodent ingestion
- Added ZIP and date cleaning
- Added weekly lag features and expanding ZIP thresholds
- Added chronological logistic regression and XGBoost training
- Added metrics and latest-prediction artifact generation
- Added the dark civic-operations dashboard

**Next:**
- Install the pinned environment
- Fetch a bounded development dataset
- Run the full pipeline and capture dashboard screenshots

## Entry 003 — Live Data and Model Artifacts Built

**Completed:**
- Installed the Python 3.12 virtual environment dependencies
- Installed `libomp` with Homebrew so XGBoost can load on macOS
- Fetched 230,339 official NYC 311 Rodent records from 2020-01-01 through 2026-06-06
- Fetched 178 official MODZCTA map features
- Filtered modeling rows to 177 mapped ZIP areas
- Built 59,472 ZIP-week rows with 57,879 labeled examples
- Trained logistic regression and XGBoost baselines
- Generated latest predictions for June 1, 2026
- Generated SHAP values and feature importance artifacts

**Next:**
- Capture final README screenshots
- Add sanitation and weather feature branches after baseline review
- Decide whether raw/model artifacts should be tracked or regenerated only

## Entry 004 — Dashboard Browser Verification

**Completed:**
- Launched Streamlit at `http://localhost:8501`
- Verified all six pages in the Codex in-app browser
- Confirmed no browser console errors, Streamlit tracebacks, or setup-required states
- Fixed a Plotly 6 colorbar API incompatibility in the map component
- Added verified screenshots at `app/assets/dashboard-overview.png` and `app/assets/risk-map.png`

**Next:**
- Begin Phase 4 with general 311 sanitation features

## Entry 005 — Visual Relaunch and Public Deployment

**Completed:**
- Replaced the cyan/navy theme with Midnight Plum × Acid Lime × Signal Coral
- Applied the new visual system to Streamlit maps, charts, cards, controls, and risk tiers
- Built a static interactive showcase from the latest prediction and model artifacts
- Added interactive overview, risk map, ZIP drilldown, model, explorer, and methodology views
- Rewrote `PRD.md` as a launch-ready product document
- Added `DEPLOYMENT.md` and `RELEASE_NOTES.md`
- Generated a 3.5 MB product-tour GIF and a 2.2 MB ZIP drilldown GIF
- Browser-tested navigation, map rendering, ZIP selection, charts, and console output
- Deployed the named Vercel project at `https://ratradar-nyc.vercel.app`

**Next:**
- Add sanitation and weather features
- Promote SHAP values into local explanation cards
- Add scheduled weekly artifact refresh

## Entry 006 — GitHub Release Prepared

**Completed:**
- Added the GitHub repository link and launch badges to `README.md`
- Refined the project description for the public repository and portfolio profile
- Included the trained model, metrics, SHAP values, map geometry, and prediction artifacts in the GitHub release
- Kept the reproducible raw NYC 311 source extract out of version control

**Next:**
- Publish `dhruvtoprani/ratradar-nyc`
- Add RatRadar NYC to the GitHub profile README
- Verify the repository and profile links
